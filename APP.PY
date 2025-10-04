from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import csv
from datetime import datetime
import os
import threading
import time

app = Flask(__name__)
CORS(app)
CSV_FILE_2 = "data/data_html.csv"
CSV_FILE = "data/logs.csv"
os.makedirs("data", exist_ok=True)

# Tworzymy plik CSV jeśli nie istnieje
if not os.path.exists(CSV_FILE_2) or os.path.getsize(CSV_FILE) == 0:
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["eventType", "domain", "seconds","timestamp"])

# Wątek monitorujący w tle (np. automatyczne dane)
def monitor_loop():
    counter = 0
    while True:
        counter += 1
        event = ["monitoring_event", f"example.com", counter]
        timestamp = datetime.now().isoformat()
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, *event])
        print(f"[+] Wątek w tle zapisuje: {timestamp}, {event}")
        time.sleep(10)

threading.Thread(target=monitor_loop, daemon=True).start()

# Endpoint do logowania POST ze strony / skryptu JS
@app.route("/log", methods=["POST"])
def log_time():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Brak danych"}), 400

    domain = data.get("domain", "unknown")
    seconds = data.get("seconds", 0)
    eventType = data.get("eventType", "unknown")
    ts = data.get("ts", datetime.now().isoformat())

    # Tworzymy folder data jeśli nie istnieje
    os.makedirs("data", exist_ok=True)

    # Dopisywanie nowego wpisu do data/data_html.csv
    file_exists = os.path.exists(CSV_FILE_2)
    with open(CSV_FILE_2, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(CSV_FILE_2) == 0:
            writer.writerow([ "eventType", "domain", "seconds", "timestamp" ])
        writer.writerow([ eventType, domain, seconds, ts])

    print(f"[+] POST dopisany:  {eventType}, {domain}, {seconds} , {ts} ")
    return jsonify({"status": "ok"})

# Dashboard
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint API zwracający logi w JSON
@app.route('/api/logs')
def api_logs():
    logs = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE_2, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    return jsonify(logs)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
