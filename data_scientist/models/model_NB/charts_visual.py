import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm


def plot_correlation_matrix(df: pd.DataFrame, title: str = "Macierz korelacji"):
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.corr(), annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
    plt.title(title, fontsize=14, pad=15)
    plt.tight_layout()
    plt.show()


def plot_cluster_boxplot(df_clust):
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="klaster", y="ilosc_wypadkow", data=df_clust, hue="klaster", palette="Set2", legend=False)
    plt.title("Rozkład liczby wypadków w wydzielonych klastrach", fontsize=14)
    plt.xlabel("Numer klastra")
    plt.ylabel("Ilość wypadków na skrzyżowaniu")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


# wykres wpłytwu czynników
def plot_feature_importance(model_nb, title: str = "Wpływ czynników na liczbę wypadków"):
    params = model_nb.params.drop(["const", "alpha", "lnalpha"], errors="ignore")
    pvalues = model_nb.pvalues.drop(["const", "alpha", "lnalpha"], errors="ignore")

    importance = (np.exp(params) - 1) * 100

    df_imp = pd.DataFrame({
        "Zmienna": importance.index,
        "Wpływ (%)": importance.values,
        "Istotna": pvalues.apply(lambda x: "Tak (p < 0.05)" if x < 0.05 else "Nie (nieistotna)")
    }).sort_values(by="Wpływ (%)", ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(
        x="Wpływ (%)",
        y="Zmienna",
        data=df_imp,
        hue="Istotna",
        palette={"Tak (p < 0.05)": "#2b8cbe", "Nie (nieistotna)": "#a6bddb"}
    )

    plt.axvline(x=0, color="black", linestyle="--", alpha=0.7)
    plt.title(title, fontsize=14, pad=15)
    plt.xlabel("Oczekiwana procentowa zmiana liczby wypadków\n(przy wzroście zmiennej o jednostkę)", fontsize=11)
    plt.ylabel("Czynnik / Zmienna", fontsize=11)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


# wykresy ze średnimi wartościami wewnątrz klastrów
def plot_cluster_profiles_heatmap(df_clustered, title: str = "Profile Klastrów - Średnie wartości cech"):
    cluster_means = df_clustered.groupby("klaster").mean()

    if "ilosc_wypadkow" in cluster_means.columns:
        cluster_means = cluster_means.drop(columns=["ilosc_wypadkow"])

    cluster_means_scaled = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min() + 1e-5)

    plt.figure(figsize=(10, 5))
    sns.heatmap(
        cluster_means_scaled.T,
        annot=cluster_means.T,
        fmt=".2f",
        cmap="YlGnBu",
        cbar=False,
        linewidths=.5
    )
    plt.title(title, fontsize=14, pad=15)
    plt.xlabel("Numer Klastra", fontsize=11)
    plt.ylabel("Zmienna objaśniająca", fontsize=11)
    plt.tight_layout()
    plt.show()


def plot_actual_vs_predicted(df_with_clusters, model_nb,
                             title: str = "Top 20 Skrzyżowań: Rzeczywiste wypadki vs Predykcja z modelu"):
    df_plots = df_with_clusters.copy()
    all_params = model_nb.params.index
    valid_features = [col for col in all_params if col in df_plots.columns and col != "ilosc_wypadkow"]

    X = df_plots[valid_features]
    X_with_const = sm.add_constant(X, has_constant='add')

    df_plots["Predykcja"] = model_nb.predict(X_with_const)

    df_plots = df_plots.reset_index()
    df_plots = df_plots.sort_values(by="ilosc_wypadkow", ascending=False).head(20)
    df_melted = pd.melt(
        df_plots,
        id_vars=["skrzyzowanie"],
        value_vars=["ilosc_wypadkow", "Predykcja"],
        var_name="Typ danych",
        value_name="Liczba wypadków"
    )

    df_melted["Typ danych"] = df_melted["Typ danych"].map(
        {"ilosc_wypadkow": "Rzeczywista liczba wypadków", "Predykcja": "Prognoza z modelu"})

    plt.figure(figsize=(14, 7))
    sns.barplot(
        x="skrzyzowanie",
        y="Liczba wypadków",
        hue="Typ danych",
        data=df_melted,
        palette={"Rzeczywista liczba wypadków": "#e34a33", "Prognoza z modelu": "#2ca25f"}
    )

    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.title(title, fontsize=14, pad=15)
    plt.xlabel("Nazwa Skrzyżowania", fontsize=11)
    plt.ylabel("Liczba wypadków", fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()