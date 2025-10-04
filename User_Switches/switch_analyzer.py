# User_Switch/analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional

def load_and_sort_logs(path: str, ts_col: str = "timestamp") -> pd.DataFrame:
    """Wczytuje CSV i sortuje po kolumnie timestamp rosnąco."""
    df = pd.read_csv(path)
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    df = df.dropna(subset=[ts_col])
    df = df.sort_values(by=ts_col).reset_index(drop=True)
    return df


def count_transitions(
    df: pd.DataFrame,
    title_col: str = "title",
    top_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Liczy przejścia między kolejnymi rekordami w DataFrame.

    Args:
        df (pd.DataFrame): Posortowany DataFrame
        title_col (str): Nazwa kolumny z tytułem aplikacji/strony
        top_n (int, optional): Jeśli podane, zwraca tylko top-N przejść

    Returns:
        pd.DataFrame: Kolumny ['from', 'to', 'count']
    """
    df_copy = df.copy()
    df_copy["prev"] = df_copy[title_col].shift(1)
    transitions = df_copy.dropna(subset=["prev"]).copy()

    transition_counts = (
        transitions.groupby(["prev", title_col])
        .size()
        .reset_index(name="count")
        .rename(columns={"prev": "from", title_col: "to"})
        .sort_values(by="count", ascending=False)
        .reset_index(drop=True)
    )

    if top_n is not None:
        transition_counts = transition_counts.head(top_n)

    return transition_counts


def plot_topN_heatmap(transitions: pd.DataFrame, top_n: int = 10):
    """
    Rysuje heatmapę dla najczęstszych przejść 'from' -> 'to'.

    Args:
        transitions (pd.DataFrame): Dane z kolumnami ['from', 'to', 'count']
        top_n (int): Ile najczęstszych przejść uwzględnić
    """
    top = transitions.head(top_n)
    matrix = top.pivot(index="to", columns="from", values="count").fillna(0)

    plt.figure(figsize=(10, 7))
    sns.heatmap(matrix, annot=True, fmt=".0f", cmap="Blues", cbar=True)
    plt.title(f"Heatmapa {top_n} najczęstszych przejść (from → to)")
    plt.xlabel("from")
    plt.ylabel("to")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()
