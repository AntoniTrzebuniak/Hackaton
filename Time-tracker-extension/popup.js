const exportBtn = document.getElementById("export");
const resetBtn = document.getElementById("reset");
const list = document.getElementById("list");

let logs = [];

// Funkcja aktualizuj¹ca listê w popup
function renderLogs() {
    if (logs.length === 0) {
        list.innerText = "Brak logów.";
    } else {
        const last10 = logs.slice(-100).reverse();
        list.innerHTML = last10.map(l => {
            return `<div><b>${l.domain}</b>: ${l.data.seconds} sekund<br><small>${l.ts}</small></div><hr>`;
        }).join("");
    }
}

// Pobierz pocz¹tkowe logi z background
chrome.runtime.sendMessage({ type: "getLogs" }, (res) => {
    logs = res.logs || [];
    renderLogs();
});

// Odbieranie nowych logów w czasie rzeczywistym
const port = chrome.runtime.connect({ name: "popup" });
port.onMessage.addListener((msg) => {
    logs.push(msg);
    renderLogs();
});

// Eksport CSV
exportBtn.addEventListener("click", () => {
    const now = new Date().toISOString();
    let csv = "domain,seconds,exported_at\n";
    logs.forEach(l => {
        csv += `${l.data.domain},${l.data.seconds},${now}\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "time_tracker_logs.csv";
    a.click();
    URL.revokeObjectURL(url);
});

// Reset logów
resetBtn.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "resetLogs" }, (res) => {
        logs = [];
        renderLogs();
        alert("Logi wyczyszczone!");
    });
});
