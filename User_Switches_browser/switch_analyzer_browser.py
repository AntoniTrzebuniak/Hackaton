# User_Switch_html/analyzer.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
from pathlib import Path


def load_and_sort_logs(path: str, ts_col: str = "timestamp") -> pd.DataFrame:
    """Loads CSV and sorts by timestamp column ascending."""

    # Read only specific columns we need
    df = pd.read_csv(
        path,
        usecols=["event", "domain", "time", "timestamp"],
        on_bad_lines='skip'  # Skip problematic lines
    )
    
    if ts_col not in df.columns:
        raise ValueError(f"Missing timestamp column in file: {path}")

    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    df = df.dropna(subset=[ts_col])
    df = df.sort_values(by=ts_col).reset_index(drop=True)
    
    print(f"Successfully loaded {len(df)} rows from {path}")
    return df


def detect_main_column(df: pd.DataFrame) -> str:
    """
    Wybiera kolumnę do analizy przejść.
    Preferuje 'title', jeśli nie ma to 'domain'.
    """
    if "title" in df.columns:
        return "title"
    elif "domain" in df.columns:
        return "domain"
    else:
        raise ValueError("Brak kolumny 'title' ani 'domain' w danych.")


def count_transitions(
        df: pd.DataFrame,
        main_col: str,
        top_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Liczy przejścia między kolejnymi rekordami w DataFrame.

    Args:
        df (pd.DataFrame): Posortowany DataFrame
        main_col (str): Nazwa kolumny do śledzenia przejść
        top_n (int, optional): Jeśli podane, zwraca tylko top-N przejść

    Returns:
        pd.DataFrame: Kolumny ['from', 'to', 'count']
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


def plot_heatmaps_per_day(df: pd.DataFrame, main_col: str, save_dir: str = "../plots"):
    """
    Tworzy heatmapy przejść 'from -> to' dla każdego dnia i zapisuje je jako pliki PNG.
    """
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=[main_col, "timestamp"])

    # Grupowanie po dniu
    df["day"] = df["timestamp"].dt.date

    Path(save_dir).mkdir(parents=True, exist_ok=True)

    for day, group in df.groupby("day"):
        group_copy = group.copy()
        group_copy["prev"] = group_copy[main_col].shift(1)
        transitions = group_copy.dropna(subset=["prev"])
        transitions = transitions[transitions[main_col] != transitions["prev"]]

        transition_counts = (
            transitions.groupby(["prev", main_col])
            .size()
            .reset_index(name="count")
            .rename(columns={"prev": "from", main_col: "to"})
        )

        if transition_counts.empty:
            print(f"Brak przejść do narysowania dla dnia {day}")
            continue

        matrix = transition_counts.pivot(index="to", columns="from", values="count").fillna(0)

        plt.figure(figsize=(12, 8))
        sns.heatmap(matrix, annot=True, fmt=".0f", cmap="Blues", cbar=True)
        plt.title(f"Heatmapa przejść — {day}")
        plt.xlabel("from")
        plt.ylabel("to")
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()

        output_file = Path(save_dir) / f"heatmapa_przejsc_{day}.png"
        plt.savefig(output_file)
        plt.close()

        print(f"✅ Heatmapa zapisana dla dnia {day} -> {output_file}")

def plot_time_spent_histograms_per_day(csv_path: str, top_n: int = 10, save_dir: str = "../plots"):
    """
    Tworzy osobne histogramy czasu spędzonego na stronach dla każdego dnia
    (grupując po pierwszych 9 znakach timestamp)
    i zapisuje je jako pliki PNG.
    """

    df = pd.read_csv(csv_path, header=None, names=["event", "domain", "time", "timestamp"])
    df = df[df["event"] == "time_spent"].copy()

    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df = df.dropna(subset=["time", "timestamp"])

    # Pobieramy tylko pierwsze 10 znaków timestamp (YYYY-MM-DD)
    df["day"] = df["timestamp"].str[:10]

    # Debug: sprawdź, jakie "dni" wykryto
    print("Wykryte dni:", df["day"].unique())

    Path(save_dir).mkdir(parents=True, exist_ok=True)
    results = []

    for day, group in df.groupby("day"):
        print(f"Dzień: {day}, liczba rekordów: {len(group)}")
        summary = (
            group.groupby("domain")["time"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
        )

        plt.figure(figsize=(10, 6))
        sns.barplot(x="time", y="domain", data=summary, palette="viridis")
        plt.xlabel("Łączny czas spędzony (sekundy)")
        plt.ylabel("Strona (domena)")
        plt.title(f"Top {top_n} stron — {day}")
        plt.tight_layout()

        output_file = Path(save_dir) / f"time_spent_{day}.png"
        plt.savefig(output_file)
        plt.close()

        results.append((day, output_file))

    print(f"✅ Zapisano {len(results)} wykresów w folderze: {save_dir}")
    return results


if __name__ == "__main__":
    path_csv = "./data/data_html.csv"
    df = load_and_sort_logs(path_csv)
    main_col = detect_main_column(df)
    transitions = count_transitions(df, main_col)
    plot_heatmaps_per_day(df, main_col, save_dir="./plots")
    summary = plot_time_spent_histograms_per_day(path_csv, top_n=10)
    print(summary)
