let logs = [];
let ports = [];

function saveLogs() {
    chrome.storage.local.set({ logs });
}

// Obsługa popup
chrome.runtime.onConnect.addListener((port) => {
    if (port.name === "popup") {
        ports.push(port);
        port.onDisconnect.addListener(() => {
            ports = ports.filter(p => p !== port);
        });
    }
});

// Odbieranie eventów z content_script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "event") {
        const entry = {
            eventType: msg.eventType,
            domain: msg.data.domain || msg.domain,
            url: msg.url,
            ts: msg.ts,
            data: msg.data
        };

        // Dodaj log tylko dla time_spent
        if (entry.eventType === "time_spent") {
            logs.push(entry);
            saveLogs();
            // Wyślij do popup
            ports.forEach(port => port.postMessage(entry));
        }
    } else if (msg.type === "getLogs") {
        chrome.storage.local.get(["logs"], (res) => {
            sendResponse({ logs: res.logs || [] });
        });
        return true; // async response
    } else if (msg.type === "resetLogs") {
        logs = [];
        saveLogs();
        sendResponse({ ok: true });
        return true;
    }
});
