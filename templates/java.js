<script>
async function loadHeatmaps() {
    try {
        const response = await fetch('/api/plots');
        const plots = await response.json();
        const container = document.getElementById('heatmaps-container');
        container.innerHTML = '';  // usuń "Loading..."

        if (plots.length === 0) {
            container.innerHTML = '<p>No heatmaps available yet.</p>';
            return;
        }

        plots.forEach(plot => {
            const div = document.createElement('div');
            div.style.marginBottom = '20px';

            const img = document.createElement('img');
            img.src = `/plots/${plot}`; // używa endpointu Flask
            img.style.maxWidth = '100%';
            div.appendChild(img);

            const caption = document.createElement('p');
            caption.textContent = plot;
            div.appendChild(caption);

            container.appendChild(div);
        });
    } catch (err) {
        console.error('Error loading heatmaps:', err);
    }
}

// Wywołanie po załadowaniu strony
window.addEventListener('DOMContentLoaded', () => {
    loadHeatmaps();
});
</script>