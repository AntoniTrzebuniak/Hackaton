from flask import Flask, request
from flask_cors import CORS
import csv
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

CSV_FILE = "../Data_html.csv"

# Nagłówek jeśli plik nie istnieje
if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["eventType","domain","seconds","timestamp"])

@app.route("/log", methods=["POST"])
def log_time():
    data = request.json
    domain = data.get("domain")
    seconds = data.get("seconds")
    eventType = data.get("eventType")
    ts = data.get("ts")
    received_at = datetime.now().isoformat()

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([eventType, domain, seconds, ts])

    print(f"[+] Zapisano: {eventType}, {domain}, {seconds}s, {ts}")
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
