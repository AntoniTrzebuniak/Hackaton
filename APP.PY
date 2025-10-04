"""
ProcessBot Dashboard - Flask Web Application
Visualizes user activity data and suggests automation opportunities
"""

from flask import Flask, render_template, jsonify
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
import json

app = Flask(__name__)

# Configuration
DATA_DIR = Path("./data")
WINDOWS_CSV = DATA_DIR / "windows.csv"
CLIPBOARD_CSV = DATA_DIR / "clipboard.csv"
EVENTS_CSV = DATA_DIR / "events.csv"
BROWSER_HISTORY_CSV = DATA_DIR / "browser_history.csv"

def load_windows_data():
    """Load windows activity data"""
    try:
        df = pd.read_csv(WINDOWS_CSV)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"Error loading windows data: {e}")
        return pd.DataFrame()

def calculate_window_transitions():
    """Calculate transitions between windows for Sankey diagram"""
    df = load_windows_data()
    
    if df.empty:
        return {"nodes": [], "links": []}
    
    # Clean up window titles - simplify them
    df['simple_title'] = df['title'].apply(lambda x: simplify_window_title(str(x)))
    
    # Remove consecutive duplicates (same window)
    df = df[df['simple_title'] != df['simple_title'].shift()]
    
    # Create transitions
    transitions = []
    for i in range(len(df) - 1):
        source = df.iloc[i]['simple_title']
        target = df.iloc[i + 1]['simple_title']
        if source != target:  # Only count actual switches
            transitions.append((source, target))
    
    # Count transitions
    transition_counts = Counter(transitions)
    
    # Get top transitions (limit to avoid clutter)
    top_transitions = transition_counts.most_common(20)
    
    # Build nodes and links for Sankey
    unique_windows = set()
    for (source, target), count in top_transitions:
        unique_windows.add(source)
        unique_windows.add(target)
    
    # Create node list with IDs
    nodes = [{"id": i, "name": name} for i, name in enumerate(sorted(unique_windows))]
    node_map = {node["name"]: node["id"] for node in nodes}
    
    # Create links
    links = []
    for (source, target), count in top_transitions:
        links.append({
            "source": node_map[source],
            "target": node_map[target],
            "value": count
        })
    
    return {"nodes": nodes, "links": links}

def simplify_window_title(title):
    """Simplify window titles to make them more readable"""
    if pd.isna(title) or title == '' or title == '0':
        return "Unknown"
    
    # Extract application name from common patterns
    if " - " in title:
        parts = title.split(" - ")
        # Usually app name is at the end
        app = parts[-1].strip()
        # But if it's too long, take first part
        if len(app) > 30:
            app = parts[0].strip()[:30]
        return app
    
    # Truncate long titles
    if len(title) > 30:
        return title[:30] + "..."
    
    return title

def get_activity_stats():
    """Calculate basic activity statistics"""
    df = load_windows_data()
    
    if df.empty:
        return {
            "total_switches": 0,
            "unique_apps": 0,
            "most_used_app": "N/A",
            "avg_focus_time": 0
        }
    
    df['simple_title'] = df['title'].apply(simplify_window_title)
    
    # Remove consecutive duplicates
    df_switches = df[df['simple_title'] != df['simple_title'].shift()]
    
    total_switches = len(df_switches) - 1
    unique_apps = df['simple_title'].nunique()
    
    # Most used app
    app_counts = df['simple_title'].value_counts()
    most_used_app = app_counts.index[0] if len(app_counts) > 0 else "N/A"
    
    # Average focus time (time between switches)
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    avg_focus_time = df['time_diff'].mean() if len(df) > 1 else 0
    
    return {
        "total_switches": total_switches,
        "unique_apps": unique_apps,
        "most_used_app": most_used_app,
        "avg_focus_time": round(avg_focus_time, 1)
    }

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/window-transitions')
def api_window_transitions():
    """API endpoint for window transitions data"""
    data = calculate_window_transitions()
    return jsonify(data)

@app.route('/api/stats')
def api_stats():
    """API endpoint for activity statistics"""
    stats = get_activity_stats()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)