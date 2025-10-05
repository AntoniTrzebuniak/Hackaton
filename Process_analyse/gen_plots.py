from .proc_analysis import ProcessAnalyzer
from .web_analys import DomainTransitionAnalyzer
import time
from datetime import date

def generate_plots():
    """Funkcja generująca wykresy w tle co 10 sekund"""
    SLEEP_INTERVAL = 300  # sekund
    while True:
        try:
            analyzer = ProcessAnalyzer("data/windows.csv")
            analyzer.calculate_time_spent()

            analyzer.plot_time_spent("plotly/czas_procesy.html")
            analyzer.plot_process_network("plotly/siec_titles.html", 'title')
            analyzer.plot_process_network("plotly/siec_process.html")
            

            analyzer = DomainTransitionAnalyzer("./data/data_html.csv")
            transitions = analyzer.count_transitions(analyzer.data, main_col="domain")
            transitions.head()

            analyzer.plot_heatmap(main_col="domain")
            analyzer.plot_heatmap(main_col="domain", day=date.today())  
            analyzer.plot_total_time_barplot()
            time.sleep(SLEEP_INTERVAL)
        except Exception as e:
            print(f"Błąd podczas generowania wykresów: {e}")
            time.sleep(SLEEP_INTERVAL)