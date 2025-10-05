import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import networkx as nx
import time

class ProcessAnalyzer:
    def __init__(self, csv_path: str):
        """Inicjalizacja: wczytanie danych z CSV."""
        self.data = pd.read_csv(csv_path)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data.sort_values(by='timestamp', inplace=True)
    
    def calculate_time_spent(self, column: str = 'process') -> pd.DataFrame:
        """Liczy czas spędzony w każdym procesie na podstawie różnicy czasów."""
        df = self.data.copy()
        df['next_timestamp'] = df['timestamp'].shift(-1)
        df['duration'] = (df['next_timestamp'] - df['timestamp']).fillna(pd.Timedelta(seconds=0))
        
        # Grupowanie po procesach
        time_spent = df.groupby(column)['duration'].sum().reset_index()
        time_spent['minutes'] = time_spent['duration'].dt.total_seconds() / 60
        
        self.time_spent = time_spent
        return time_spent
    
    def plot_time_spent(self, output_html: str = None):
        """Tworzy interaktywny wykres Plotly i opcjonalnie zapisuje jako HTML."""
        if not hasattr(self, 'time_spent'):
            self.calculate_time_spent()
        
        # Sortowanie według czasu (minuty) malejąco
        sorted_df = self.time_spent.sort_values(by='minutes', ascending=False)

        fig = px.bar(
            sorted_df,
            x='process',
            y='minutes',
            color='process',
            title='Time spent on individual processes (minutes)',
            text_auto='.2f'
        )
        fig.update_layout(
            xaxis_title='Process',
            yaxis_title='Time [minutes]',
            showlegend=False,
            template='plotly_white',
            hovermode='x unified'
        )
        
        if output_html:
            fig.write_html(output_html)
            print(f"Wykres zapisano do pliku: {output_html}")
        return fig
    
    def plot_process_network(self, output_html: str = None, column: str = 'process'):
        """Tworzy interaktywny wykres sieci przejść między procesami."""
        df = self.data.copy()
        df['next_process'] = df[column].shift(-1)
        
        # usuwamy powtarzające się procesy z rzędu (brak "przejścia")
        df = df[df[column] != df['next_process']]
        
        # liczba przejść między procesami
        transitions = df.groupby([column, 'next_process']).size().reset_index(name='count')
        
        # budowa grafu NetworkX
        G = nx.DiGraph()
        for _, row in transitions.iterrows():
            G.add_edge(row[column], row['next_process'], weight=row['count'])
        
        pos = nx.spring_layout(G, seed=42)  # rozmieszczenie węzłów
        
        # przygotowanie danych do Plotly
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        node_x, node_y, node_text, degrees, hover_texts = [], [], [], [], []
        max_degree = max(dict(G.degree()).values())
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            degree = G.degree(node)
            degrees.append(degree)
            hover_texts.append(f"<b>{node}</b><br>Node Degree: {degree}")
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            hovertext=hover_texts,
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                color=degrees,
                size=degrees,
                sizemode='diameter',  # tryb skalowania
                sizemin=1,  # minimalny rozmiar węzła
                colorbar=dict(
                    title='Node Degree',
                    thickness=15,
                    xanchor='left'  
                ),
                line_width=2
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title='Network of passages between processes' if column == 'process' else 'Network of passages between windows',
                            title_x=0.5,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            template='plotly_white',
                            autosize=True 
                        ))
        
        if output_html:
            fig.write_html(output_html)
            print(f"Wykres sieci zapisano do pliku: {output_html}")
        return fig


if __name__ == "__main__":
    analyzer = ProcessAnalyzer("data/windows.csv")
    print(analyzer.calculate_time_spent())

    fig = analyzer.plot_time_spent("plotly/czas_procesy.html")
    fig = analyzer.plot_process_network("plotly/siec_titles.html", 'title')
    fig = analyzer.plot_process_network("plotly/siec_process.html")
