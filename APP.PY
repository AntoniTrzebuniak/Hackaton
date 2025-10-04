from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
from Collector import collector_to_csv
from Process_analyse import proc_analysis
import csv
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

CSV_FILE_2 = "data/data_html.csv"
CSV_FILE = "data/logs.csv"
os.makedirs("data", exist_ok=True)

# ---------- Wątek monitorujący procesy w tle (ten z ProcessBot) ----------
def start_processbot():
    collector_to_csv.main()  # uruchamiamy monitor w tle

threading.Thread(target=start_processbot, daemon=True).start()

# ---------- Wątek monitorujący "internetowe" logi ----------


# ---------- Flask endpoints ----------
@app.route("/log", methods=["POST"])
def log_time():
    data = request.json
    if not data:
        return {"status": "error", "message": "Brak danych"}, 400

    domain = data.get("domain", "unknown")
    seconds = data.get("seconds", 0)
    eventType = data.get("eventType", "unknown")
    ts = data.get("ts", datetime.now().isoformat())

    with open(CSV_FILE_2, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([eventType, domain, seconds, ts])

    return {"status": "ok"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs')
def api_logs():
    logs = []
    if os.path.exists(CSV_FILE_2):
        with open(CSV_FILE_2, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    return jsonify(logs)

# ---------- Uruchomienie Flask ----------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
