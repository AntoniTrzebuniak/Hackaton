from flask import Flask, request
from flask_cors import CORS
import csv
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

CSV_FILE = "../Data_html.csv"

# Jeśli plik nie istnieje, dodaj nagłówek
if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["domain", "seconds", "timestamp", "received_at"])

@app.route("/log", methods=["POST"])
def log_time():
    data = request.json
    domain = data.get("domain")
    seconds = data.get("seconds")
    ts = data.get("ts")
    received_at = datetime.now().isoformat()

    # 🔥 UWAGA: tutaj jest "a" (dopisywanie), nie "w" (nadpisywanie)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([domain, seconds, ts, received_at])

    print(f"[+] Zapisano: {domain}, {seconds}s, {ts}")
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
