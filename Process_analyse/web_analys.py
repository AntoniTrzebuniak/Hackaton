import pandas as pd
from pathlib import Path
from typing import Optional
import plotly.express as px
from datetime import date

class DomainTransitionAnalyzer:
    def __init__(self, csv_path: str):
        """Wczytuje dane i przygotowuje DataFrame."""
        self.data = pd.read_csv(csv_path)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], errors='coerce')
        self.data = self.data.dropna(subset=['timestamp'])
        self.data = self.data.sort_values('timestamp').reset_index(drop=True)

    @staticmethod
    def count_transitions(
        df: pd.DataFrame,
        main_col: str,
        top_n: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Liczy przejścia między kolejnymi rekordami w DataFrame.
        Zwraca DataFrame z kolumnami ['from', 'to', 'count'].
        """
        df_copy = df.copy()
        df_copy["prev"] = df_copy[main_col].shift(1)
        transitions = df_copy.dropna(subset=["prev"]).copy()
        transitions = transitions[transitions[main_col] != transitions["prev"]]

        transition_counts = (
            transitions.groupby(["prev", main_col])
            .size()
            .reset_index(name="count")
            .rename(columns={"prev": "from", main_col: "to"})
            .sort_values(by="count", ascending=False)
            .reset_index(drop=True)
        )

        if top_n is not None:
            transition_counts = transition_counts.head(top_n)

        return transition_counts

    def plot_heatmap(
        self,
        main_col: str = "domain",
        day = None,
        save_dir: str = "plots"
    ):
        """
        Tworzy interaktywną heatmapę przejść 'from -> to'.
        Jeśli `day` jest podany, filtruje dane tylko dla tego dnia.
        W przeciwnym razie używa wszystkich danych.
        """
        df = self.data.copy()
        df = df.dropna(subset=[main_col, "timestamp"])
        df["day"] = df["timestamp"].dt.date

        # wybór zakresu danych
        if day is not None:
            df = df[df["day"] == day]
            label = f"dnia {day}"
        else:
            label = "całego okresu"

        if df.empty:
            print(f"⚠️ Brak danych do narysowania heatmapy dla {label}.")
            return None

        transitions = self.count_transitions(df, main_col)
        if transitions.empty:
            print(f"⚠️ Brak przejść do narysowania dla {label}.")
            return None

        # pivot na macierz przejść
        matrix = transitions.pivot(index="to", columns="from", values="count").fillna(0)

        # Plotly heatmap
        fig = px.imshow(
            matrix,
            labels=dict(x="Z (from)", y="Do (to)", color="Liczba przejść"),
            x=matrix.columns,
            y=matrix.index,
            color_continuous_scale="Blues",
            title=f"Heatmapa przejść domen — {label}"
        )

        fig.update_layout(
            xaxis=dict(tickangle=45),
            yaxis=dict(autorange="reversed"),
            template="plotly_white",
            margin=dict(l=60, r=60, t=80, b=60)
        )

        # zapis jako HTML
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        suffix = "today" if day is not None else "all"
        output_file = Path(save_dir) / f"heatmapa_przejsc_{suffix}.html"
        fig.write_html(output_file)
        print(f"✅ Interaktywna heatmapa zapisana: {output_file}")

        return fig
    

    def plot_total_time_barplot(
        self,
        main_col: str = "domain",
        save_dir: str = "plots",
        top_n: int = 12
    ):
        """
        Tworzy interaktywny barplot pokazujący łączny czas spędzony na różnych domenach.
        Wybiera top-N domen o największym czasie (domyślnie 12).
        """
        df = self.data.copy()

        if "seconds" not in df.columns:
            raise ValueError("Brak kolumny 'seconds' w danych!")

        df = df.dropna(subset=[main_col, "seconds"])
        df["seconds"] = pd.to_numeric(df["seconds"], errors="coerce").fillna(0)

        # sumowanie czasu
        total_time = (
            df.groupby(main_col)["seconds"]
            .sum()
            .reset_index()
            .sort_values("seconds", ascending=False)
            .head(top_n)
        )

        # konwersja sekund -> minut
        total_time["minutes"] = total_time["seconds"] / 60

        fig = px.bar(
            total_time,
            x="minutes",
            y=main_col,
            orientation="h",
            color="minutes",
            text_auto=".1f",
            title=f"Top {top_n} domen według czasu spędzonego (minuty)",
            color_continuous_scale="Blues"
        )

        fig.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            xaxis_title="Czas spędzony (minuty)",
            yaxis_title="Domena",
            template="plotly_white",
            margin=dict(l=60, r=60, t=80, b=60)
        )

        Path(save_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(save_dir) / f"barplot_top_{top_n}_domains.html"
        fig.write_html(output_file)
        print(f"✅ Barplot zapisany: {output_file}")

        return fig

if __name__ == "__main__":
    analyzer = DomainTransitionAnalyzer("./data/data_html.csv")
    transitions = analyzer.count_transitions(analyzer.data, main_col="domain")
    print(transitions.head())

    analyzer.plot_heatmap(main_col="domain")
    analyzer.plot_heatmap(main_col="domain", day=date.today())  
    analyzer.plot_total_time_barplot()
