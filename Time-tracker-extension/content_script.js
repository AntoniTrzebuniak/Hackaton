(function () {
    function timestamp() { return new Date().toISOString(); }

    function logEvent(eventType, data) {
        chrome.runtime.sendMessage({
            type: "event",
            eventType,
            url: location.href,
            domain: location.hostname,
            ts: timestamp(),
            data
        });
    }

    let currentDomain = location.hostname;
    let startTime = Date.now();

    function logTimeSpent() {
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        if (seconds > 0) {
            const logData = {
                domain: currentDomain,
                seconds: seconds,
                ts: new Date().toISOString()
            };

            logEvent("time_spent", logData);

            // Wysyłka do lokalnego serwera Python
            fetch("http://127.0.0.1:5000/log", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(logData)
            }).catch(err => console.log("Błąd wysyłki logu:", err));
        }
        startTime = Date.now();
    }

    // Log page load dla domeny
    logEvent("page_load", { domain: currentDomain, title: document.title });

    // Zdarzenie przy zmianie widoczności (przełączenie na inną kartę)
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) logTimeSpent();
    });

    // Zdarzenie przy zamknięciu/odświeżeniu strony
    window.addEventListener("beforeunload", () => {
        logTimeSpent();
    });

    // SPA – zmiana domeny bez reload
    setInterval(() => {
        if (location.hostname !== currentDomain) {
            logTimeSpent();
            currentDomain = location.hostname;
            logEvent("page_load", { domain: currentDomain, title: document.title });
        }
    }, 1000);
})();
