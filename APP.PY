from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
from Collector import collector_to_csv
import csv
from datetime import datetime
import os
from flask import send_from_directory
from Process_analyse import gen_plots

app = Flask(__name__)
CORS(app)

PLOT_FOLDER = os.path.join(os.getcwd(), "plots")  # <-- poprawnie
CSV_FILE_2 = "data/data_html.csv"
CSV_FILE = "data/logs.csv"
os.makedirs("data", exist_ok=True)

# ---------- Wątek monitorujący procesy w tle (ten z ProcessBot) ----------
def start_processbot():
    collector_to_csv.main()  # uruchamiamy monitor w tle

threading.Thread(target=start_processbot, daemon=True).start()
threading.Thread(target=gen_plots.generate_plots, daemon=True).start()
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
@app.route('/index')
def index():
    # Lista plików w folderze plots
    plots = sorted(os.listdir(PLOT_FOLDER))
    return render_template('index.html', plots=plots)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/plotly/<path:filename>')
def serve_plotly(filename):
    return send_from_directory('plotly', filename)

@app.route('/api/plots')
def api_plots():
    if not os.path.exists(PLOT_FOLDER):
        return jsonify([])
    plots = [f for f in os.listdir(PLOT_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    plots.sort()
    return jsonify(plots)


@app.route('/plots/<filename>')
def plot_file(filename):
    return send_from_directory(PLOT_FOLDER, filename)

# ---------- Uruchomienie Flask ----------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
