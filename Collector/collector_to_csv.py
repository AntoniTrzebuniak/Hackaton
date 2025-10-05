"""
ProcessBot local demo data collector (consent-first, local-only)
Logs:
 - Active window focus (title, process, pid, timestamp)
 - Clipboard contents (when changed) + active window at copy time
 - Copy / Paste events metadata (Ctrl/Cmd+C and Ctrl/Cmd+V): timestamp + active window + clipboard snapshot
 - Browser history sampling (Chrome and Firefox local history DB)
Data stored in separate CSV files

IMPORTANT: This script does NOT record typed text (no keylogging).
Run only on your own machine or with explicit consent.
"""

import threading
import time
import os
import sys
from datetime import datetime
import csv
import keyboard
import win32gui
import win32process
import psutil

import pyperclip
import pygetwindow as gw


# ---------- Configuration ----------
from pathlib import Path
DATA_DIR = Path("./data")
WINDOWS_CSV = DATA_DIR / "windows.csv"
CLIPBOARD_CSV = DATA_DIR / "clipboard.csv"
EVENTS_CSV = DATA_DIR / "events.csv"
BROWSER_HISTORY_CSV = DATA_DIR / "browser_history.csv"

ACTIVE_WINDOW_POLL_INTERVAL = 1.0   # seconds
CLIPBOARD_POLL_INTERVAL = 0.5       # seconds
BROWSER_HISTORY_POLL_INTERVAL = 60  # seconds (sample every minute)
# -----------------------------------

# ---------- Helper utilities ----------

def now_iso():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def ensure_csv_files():
    """Initialize CSV files with headers if they don't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Windows CSV
    if not os.path.exists(WINDOWS_CSV):
        with open(WINDOWS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'title', 'process', 'pid'])
    
    # Clipboard CSV
    if not os.path.exists(CLIPBOARD_CSV):
        with open(CLIPBOARD_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'content', 'window_title', 'process', 'pid'])
    
    # Events CSV
    if not os.path.exists(EVENTS_CSV):
        with open(EVENTS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'event_type', 'window_title', 'process', 'pid', 'associated_clipboard_timestamp'])
    
    # Browser History CSV
    if not os.path.exists(BROWSER_HISTORY_CSV):
        with open(BROWSER_HISTORY_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'browser', 'url', 'title', 'visit_count', 'last_visit_time'])

def append_to_csv(filepath, row):
    """Thread-safe append to CSV file"""
    with csv_lock:
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

def get_active_window_info():
    """Pobiera nazwę procesu aktywnego okna"""
    try:
        # Pobierz uchwyt do aktywnego okna
        hwnd = win32gui.GetForegroundWindow()
        
        # Pobierz PID procesu
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Pobierz informacje o procesie
        process = psutil.Process(pid)
        process_name = process.name()
        
        # Pobierz tytuł okna
        window_title = win32gui.GetWindowText(hwnd)
        
        return window_title, pid, process_name
        
    except Exception as e:
        print(f"Błąd: {e}")
        return None, None, None

# ---------- CSV helper with lock ----------
csv_lock = threading.Lock()

def log_window_snapshot(title, pid, process):
    timestamp = now_iso()
    append_to_csv(WINDOWS_CSV, [timestamp, title, process, pid])

def log_clipboard(content, title, pid, process):
    timestamp = now_iso()
    # Escape newlines and quotes in content for CSV
    content_escaped = content.replace('\n', '\\n').replace('\r', '\\r')
    append_to_csv(CLIPBOARD_CSV, [timestamp, content_escaped, title, process, pid])
    return timestamp  # Return timestamp as ID

def log_event(event_type, title, pid, process, clipboard_timestamp=None):
    timestamp = now_iso()
    append_to_csv(EVENTS_CSV, [timestamp, event_type, title, process, pid, clipboard_timestamp or ''])
    return timestamp


# ---------- Active window monitor ----------
def active_window_monitor(stop_event):
    last_title = None
    while not stop_event.is_set():
        title, pid, process = get_active_window_info()
        if title != last_title:
            print(f"[WINDOW] {now_iso()} - {title} ({process} pid={pid})")
            log_window_snapshot(title, pid, process)
            last_title = title
        time.sleep(ACTIVE_WINDOW_POLL_INTERVAL)

# ---------- Clipboard monitor ----------
# Global to track clipboard and prevent double-logging from keyboard events
last_clipboard_content = None
clipboard_lock = threading.Lock()

def clipboard_monitor(stop_event):
    global last_clipboard_content
    while not stop_event.is_set():
        try:
            clip = pyperclip.paste()
        except Exception:
            clip = None
        if clip and clip != last_clipboard_content:
            with clipboard_lock:
                if clip != last_clipboard_content:
                    title, pid, process = get_active_window_info()
                    clip_timestamp = log_clipboard(clip, title, pid, process)
                    print(f"[CLIP] {now_iso()} - clipboard changed (len={len(clip)}) in window '{title}'")
                    last_clipboard_content = clip
        time.sleep(CLIPBOARD_POLL_INTERVAL)

# ---------- Keyboard listener for copy/paste events ----------
def keyboard_listener_thread(stop_event):
    
    def on_copy():
        global last_clipboard_content
        title, pid, process = get_active_window_info()
        print("[EVENT] Copy detected!")
        
        # Get clipboard content 
        try:
            clip = pyperclip.paste()
            clip_timestamp = None
            if clip:
                with clipboard_lock:
                    if clip != last_clipboard_content:
                        clip_timestamp = log_clipboard(clip, title, pid, process)
                        last_clipboard_content = clip
                    else:
                        clip_timestamp = now_iso()
            
            event_timestamp = log_event('copy', title, pid, process, clipboard_timestamp=clip_timestamp)
            print(f"[EVENT] Copy event logged at {event_timestamp}")
        except Exception as e:
            print(f"[ERROR] Copy event error: {e}")

    def on_paste():
        title, pid, process = get_active_window_info()
        print("[EVENT] Paste detected!")
        
        try:
            clip = pyperclip.paste()
            clip_timestamp = now_iso() if clip else None
            event_timestamp = log_event('paste', title, pid, process, clipboard_timestamp=clip_timestamp)
            print(f"[EVENT] Paste event logged at {event_timestamp}")
        except Exception as e:
            print(f"[ERROR] Paste event error: {e}")

    # Register hotkeys
    keyboard.add_hotkey("ctrl+c", on_copy, suppress=False)
    keyboard.add_hotkey("ctrl+v", on_paste, suppress=False)
    
    # Keep thread running until stop event
    while not stop_event.is_set():
        time.sleep(0.1)
    
    # Clean up
    keyboard.unhook_all()

# ---------- Browser history reader (Chrome, Firefox local) ----------




# ---------- Main controller ----------
def main():
    print("ProcessBot Local Demo Collector (CSV version)")
    print("This script collects active windows, clipboard contents, copy/paste events, and local browser history.")
    print(f"Data will be stored in separate CSV files:")
    print(f"  - {WINDOWS_CSV}")
    print(f"  - {CLIPBOARD_CSV}")
    print(f"  - {EVENTS_CSV}")
    print(f"  - {BROWSER_HISTORY_CSV}")
    
    ensure_csv_files()
    stop_event = threading.Event()
    threads = []

    t_window = threading.Thread(target=active_window_monitor, args=(stop_event,), daemon=True)
    threads.append(t_window)
    t_clip = threading.Thread(target=clipboard_monitor, args=(stop_event,), daemon=True)
    threads.append(t_clip)
    t_kb = threading.Thread(target=keyboard_listener_thread, args=(stop_event,), daemon=True)
    threads.append(t_kb)

    print("\nStarting monitors... Press Ctrl+C here to stop.")
    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitors...")
        stop_event.set()
        for t in threads:
            t.join(timeout=2)
        print("Stopped. Data saved in CSV files.")
        sys.exit(0)

if __name__ == "__main__":
    main()