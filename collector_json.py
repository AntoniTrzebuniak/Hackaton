"""
ProcessBot local demo data collector (consent-first, local-only)
Logs:
 - Active window focus (title, process, pid, timestamp)
 - Clipboard contents (when changed) + active window at copy time
 - Copy / Paste events metadata (Ctrl/Cmd+C and Ctrl/Cmd+V): timestamp + active window + clipboard snapshot
 - Browser history sampling (Chrome and Firefox local history DB)
Data stored in separate JSON files

IMPORTANT: This script does NOT record typed text (no keylogging).
Run only on your own machine or with explicit consent.
"""

import threading
import time
import os
import sys
import platform
from datetime import datetime, timedelta
import shutil
import tempfile
import sqlite3
import json

import psutil
import pyperclip
from pynput import keyboard
import pygetwindow as gw

# ---------- Configuration ----------
WINDOWS_JSON = "data/windows.json"
CLIPBOARD_JSON = "data/clipboard.json"
EVENTS_JSON = "data/events.json"
BROWSER_HISTORY_JSON = "data/browser_history.json"

ACTIVE_WINDOW_POLL_INTERVAL = 1.0   # seconds
CLIPBOARD_POLL_INTERVAL = 0.5       # seconds
BROWSER_HISTORY_POLL_INTERVAL = 60  # seconds (sample every minute)
# -----------------------------------

# ---------- Helper utilities ----------
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def ensure_json_files():
    """Initialize JSON files if they don't exist"""
    for filepath in [WINDOWS_JSON, CLIPBOARD_JSON, EVENTS_JSON, BROWSER_HISTORY_JSON]:
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump([], f)

def append_to_json(filepath, data):
    """Thread-safe append to JSON file"""
    with json_lock:
        try:
            # Read existing data
            with open(filepath, 'r') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []
        
        # Append new data
        existing_data.append(data)
        
        # Write back
        with open(filepath, 'w') as f:
            json.dump(existing_data, f, indent=2)

def get_active_window_info():
    """
    Try to return (title, pid, process_name). Some platforms may not provide PID.
    """
    title = None
    pid = None
    process_name = None
    try:
        win = gw.getActiveWindow()
        if win:
            title = win.title
    except Exception:
        win = None

    # Fallback strategies:
    if title is None:
        plat = platform.system()
        if plat == "Darwin":
            try:
                sc = 'tell application "System Events" to get name of first process whose frontmost is true'
                app_name = os.popen('osascript -e \'{}\''.format(sc)).read().strip()
                title = app_name
            except Exception:
                title = "Unknown"
        else:
            title = "Unknown"

    # Try to find a process by matching window title among running processes (best-effort)
    try:
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = p.info.get('name') or ''
                cmdline = ' '.join(p.info.get('cmdline') or [])
                if title and (title.lower() in name.lower() or title.lower() in cmdline.lower()):
                    pid = p.info['pid']
                    process_name = name
                    break
            except Exception:
                continue
    except Exception:
        pass

    if process_name is None:
        process_name = ""
    return title, pid or 0, process_name

# ---------- JSON helper with lock ----------
json_lock = threading.Lock()

def log_window_snapshot(title, pid, process):
    data = {
        "timestamp": now_iso(),
        "title": title,
        "process": process,
        "pid": pid
    }
    append_to_json(WINDOWS_JSON, data)

def log_clipboard(content, title, pid, process):
    data = {
        "timestamp": now_iso(),
        "content": content,
        "window_title": title,
        "process": process,
        "pid": pid
    }
    append_to_json(CLIPBOARD_JSON, data)
    return data["timestamp"]  # Return timestamp as ID

def log_event(event_type, title, pid, process, clipboard_timestamp=None):
    data = {
        "timestamp": now_iso(),
        "event_type": event_type,
        "window_title": title,
        "process": process,
        "pid": pid,
        "associated_clipboard_timestamp": clipboard_timestamp
    }
    append_to_json(EVENTS_JSON, data)
    return data["timestamp"]

def log_browser_row(browser, url, title_text, visit_count, last_visit_time):
    data = {
        "timestamp": now_iso(),
        "browser": browser,
        "url": url,
        "title": title_text,
        "visit_count": visit_count,
        "last_visit_time": last_visit_time
    }
    append_to_json(BROWSER_HISTORY_JSON, data)

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
def clipboard_monitor(stop_event):
    last_clip = None
    while not stop_event.is_set():
        try:
            clip = pyperclip.paste()
        except Exception:
            clip = None
        if clip and clip != last_clip:
            title, pid, process = get_active_window_info()
            clip_timestamp = log_clipboard(clip, title, pid, process)
            print(f"[CLIP] {now_iso()} - clipboard changed (len={len(clip)}) in window '{title}'")
            last_clip = clip
        time.sleep(CLIPBOARD_POLL_INTERVAL)

# ---------- Keyboard listener for copy/paste events ----------
def keyboard_listener_thread(stop_event):
    current_modifiers = set()

    def on_press(key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                current_modifiers.add('ctrl')
            if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                current_modifiers.add('cmd')
            
            if hasattr(key, 'char') and key.char:
                ch = key.char.lower()
                if ch == 'c' and ('ctrl' in current_modifiers or 'cmd' in current_modifiers):
                    title, pid, process = get_active_window_info()
                    try:
                        clip = pyperclip.paste()
                    except Exception:
                        clip = None
                    clip_timestamp = None
                    if clip:
                        clip_timestamp = log_clipboard(clip, title, pid, process)
                    event_timestamp = log_event('copy', title, pid, process, clipboard_timestamp=clip_timestamp)
                    print(f"[EVENT] {now_iso()} Copy event logged")
                    
                if ch == 'v' and ('ctrl' in current_modifiers or 'cmd' in current_modifiers):
                    title, pid, process = get_active_window_info()
                    try:
                        clip = pyperclip.paste()
                    except Exception:
                        clip = None
                    clip_timestamp = None
                    if clip:
                        clip_timestamp = log_clipboard(clip, title, pid, process)
                    event_timestamp = log_event('paste', title, pid, process, clipboard_timestamp=clip_timestamp)
                    print(f"[EVENT] {now_iso()} Paste event logged")
        except Exception:
            pass

    def on_release(key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                current_modifiers.discard('ctrl')
            if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                current_modifiers.discard('cmd')
        except Exception:
            pass
        if stop_event.is_set():
            return False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        while not stop_event.is_set():
            time.sleep(0.1)
        listener.stop()

# ---------- Browser history reader (Chrome, Firefox local) ----------
def read_chrome_history():
    home = os.path.expanduser("~")
    plat = platform.system()
    candidates = []
    
    if plat == "Windows":
        local = os.getenv('LOCALAPPDATA') or os.path.join(home, 'AppData', 'Local')
        candidates.append(os.path.join(local, "Google", "Chrome", "User Data", "Default", "History"))
        candidates.append(os.path.join(local, "Chromium", "User Data", "Default", "History"))
    elif plat == "Darwin":
        candidates.append(os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Default", "History"))
        candidates.append(os.path.join(home, "Library", "Application Support", "Chromium", "Default", "History"))
    else:
        candidates.append(os.path.join(home, ".config", "google-chrome", "Default", "History"))
        candidates.append(os.path.join(home, ".config", "chromium", "Default", "History"))

    for c in candidates:
        if os.path.exists(c):
            try:
                tmp = tempfile.mktemp()
                shutil.copy2(c, tmp)
                db = sqlite3.connect(tmp)
                cur = db.cursor()
                cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50")
                rows = cur.fetchall()
                for r in rows:
                    url, title_text, visit_count, last_visit_time = r
                    try:
                        webkit_epoch = datetime(1601, 1, 1)
                        last_visit_dt = webkit_epoch + timedelta(microseconds=int(last_visit_time))
                        last_visit_iso = last_visit_dt.isoformat() + "Z"
                    except Exception:
                        last_visit_iso = ""
                    log_browser_row("chrome", url, title_text, visit_count, last_visit_iso)
                db.close()
                os.remove(tmp)
                print(f"[BROWSER] Chrome history sampled ({len(rows)} rows)")
                return
            except Exception as e:
                print("[BROWSER] Chrome read error:", e)
    print("[BROWSER] No Chrome history found or could not read it.")

def read_firefox_history():
    home = os.path.expanduser("~")
    plat = platform.system()
    
    if plat == "Windows":
        local = os.getenv('APPDATA') or os.path.join(home, 'AppData', 'Roaming')
        profile_root = os.path.join(local, "Mozilla", "Firefox", "Profiles")
    elif plat == "Darwin":
        profile_root = os.path.join(home, "Library", "Application Support", "Firefox", "Profiles")
    else:
        profile_root = os.path.join(home, ".mozilla", "firefox")
        
    if os.path.isdir(profile_root):
        for fname in os.listdir(profile_root):
            p = os.path.join(profile_root, fname, "places.sqlite")
            if os.path.exists(p):
                try:
                    tmp = tempfile.mktemp()
                    shutil.copy2(p, tmp)
                    db = sqlite3.connect(tmp)
                    cur = db.cursor()
                    cur.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 50")
                    rows = cur.fetchall()
                    for r in rows:
                        url, title_text, visit_count, last_visit_date = r
                        try:
                            if last_visit_date:
                                last_visit_dt = datetime.fromtimestamp(last_visit_date / 1000000.0)
                                last_visit_iso = last_visit_dt.isoformat() + "Z"
                            else:
                                last_visit_iso = ""
                        except Exception:
                            last_visit_iso = ""
                        log_browser_row("firefox", url, title_text, visit_count, last_visit_iso)
                    db.close()
                    os.remove(tmp)
                    print(f"[BROWSER] Firefox history sampled ({len(rows)} rows)")
                    return
                except Exception as e:
                    print("[BROWSER] Firefox read error:", e)
    print("[BROWSER] No Firefox history found or could not read it.")

def browser_history_sampler(stop_event):
    while not stop_event.is_set():
        try:
            read_chrome_history()
            read_firefox_history()
        except Exception as e:
            print("[BROWSER] sampler error:", e)
        for _ in range(int(BROWSER_HISTORY_POLL_INTERVAL)):
            if stop_event.is_set():
                break
            time.sleep(1)

# ---------- Main controller ----------
def main():
    print("ProcessBot Local Demo Collector (JSON version)")
    print("This script collects active windows, clipboard contents, copy/paste events, and local browser history.")
    print(f"Data will be stored in separate JSON files:")
    print(f"  - {WINDOWS_JSON}")
    print(f"  - {CLIPBOARD_JSON}")
    print(f"  - {EVENTS_JSON}")
    print(f"  - {BROWSER_HISTORY_JSON}")
    
    ensure_json_files()
    
    stop_event = threading.Event()
    threads = []

    t_window = threading.Thread(target=active_window_monitor, args=(stop_event,), daemon=True)
    threads.append(t_window)
    t_clip = threading.Thread(target=clipboard_monitor, args=(stop_event,), daemon=True)
    threads.append(t_clip)
    t_kb = threading.Thread(target=keyboard_listener_thread, args=(stop_event,), daemon=True)
    threads.append(t_kb)
    #t_browser = threading.Thread(target=browser_history_sampler, args=(stop_event,), daemon=True)
    #threads.append(t_browser)

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
        print("Stopped. Data saved in JSON files.")
        sys.exit(0)

if __name__ == "__main__":
    main()