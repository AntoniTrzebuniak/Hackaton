import pandas as pd
import plotly.express as px
from datetime import timedelta

class ProcessAnalyzer:
    def __init__(self, csv_path: str):
        """Inicjalizacja: wczytanie danych z CSV."""
        self.data = pd.read_csv(csv_path)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data.sort_values(by='timestamp', inplace=True)
    
    def calculate_time_spent(self):
        """Liczy czas spędzony w każdym procesie na podstawie różnicy czasów."""
        df = self.data.copy()
        df['next_timestamp'] = df['timestamp'].shift(-1)
        df['duration'] = (df['next_timestamp'] - df['timestamp']).fillna(pd.Timedelta(seconds=0))
        
        # Grupowanie po procesach
        time_spent = df.groupby('process')['duration'].sum().reset_index()
        time_spent['minutes'] = time_spent['duration'].dt.total_seconds() / 60
        
        self.time_spent = time_spent
        return time_spent
    
    def plot_time_spent(self, output_html: str = None):
        """Tworzy interaktywny wykres Plotly i opcjonalnie zapisuje jako HTML."""
        if not hasattr(self, 'time_spent'):
            self.calculate_time_spent()
        
        fig = px.bar(
            self.time_spent,
            x='process',
            y='minutes',
            color='process',
            title='Czas spędzony w poszczególnych procesach (minuty)',
            text_auto='.2f',
        )
        fig.update_layout(
            xaxis_title='Proces',
            yaxis_title='Czas [minuty]',
            showlegend=False,
            template='plotly_dark',
            hovermode='x unified'
        )
        
        if output_html:
            fig.write_html(output_html)
            print(f"Wykres zapisano do pliku: {output_html}")
        return fig


if __name__ == "__main__":
    analyzer = ProcessAnalyzer("data/windows.csv")
    print(analyzer.calculate_time_spent())

    fig = analyzer.plot_time_spent("plotly/czas_procesy.html")
    fig.show()
