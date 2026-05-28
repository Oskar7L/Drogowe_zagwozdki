import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np


def load_and_clean_data(data_path: str, data2_path: str, data3_path: str) -> pd.DataFrame:
    data = pd.read_csv(data_path, sep=";", encoding="cp1250")
    data2 = pd.read_csv(data2_path, sep=";", encoding="utf-8")
    data3 = pd.read_csv(data3_path, sep=";", encoding="utf-8")
    slownik_zagrozenia = {
        'Dwie jezdnie jednokierunkowe': 1,
        'Dwie jezdnie jednokierunkowe/Jednojezdniowa dwukierunkowa': 0
    }
    data['waga_geometrii_drogi'] = data['rodzaj_drogi'].map(slownik_zagrozenia)

    # Agregacja skrzyżowan
    data_agg = data.groupby("skrzyzowanie").agg(
        ilosc_wypadkow=("skrzyzowanie", "size"),
        waga_drogi=("waga_geometrii_drogi", "max"),
    ).reset_index()

    # Złączenie i czyszczenie zmiennych
    merged = pd.merge(data_agg, data2, on="skrzyzowanie", how="inner")
    merged = pd.merge(merged, data3, on="skrzyzowanie", how="inner")

    merged["Max_dobowe[1kpoj./24h]"] = merged["Max_dobowe[1kpoj./24h]"] / 1000
    merged["Średnie_dobowe[poj./24h]"] = merged["Średnie_dobowe[poj./24h]"] / 1000
    binary_map = {"tak": 1, "nie": 0}
    merged["ścieżka_rowerowa"] = merged["ścieżka_rowerowa"].map(binary_map)
    merged["tramwaj"] = merged["tramwaj"].map(binary_map)
    merged["odległość_od_centrum"] = merged["odległość_od_centrum"].str.replace(",", ".").astype(float)
    merged = merged.set_index("skrzyzowanie")
    return merged.select_dtypes(include=["number"])


def plot_correlation_matrix(df: pd.DataFrame, title: str = "Macierz korelacji"):
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.corr(), annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
    plt.title(title, fontsize=14, pad=15)
    plt.tight_layout()
    plt.show()


def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    X_with_const = sm.add_constant(X)
    vif_data = pd.DataFrame()
    vif_data["Zmienna"] = X_with_const.columns
    vif_data["VIF"] = [
        variance_inflation_factor(X_with_const.values, i)
        for i in range(X_with_const.shape[1])
    ]
    return vif_data[vif_data["Zmienna"] != "const"].reset_index(drop=True)


def estimate_count_models(X: pd.DataFrame, y: pd.Series, label: str):
    X_with_const = sm.add_constant(X)

    print(f"  ESTYMACJA MODELI: {label}")
    print("\nWSPÓŁCZYNNIKI INFLACJI WARIANCJI (VIF)")
    try:
        vif_df = calculate_vif(X)
        print(vif_df.to_string(index=False, formatters={"VIF": "{:.2f}".format}))
    except Exception as e:
        print(f"Nie udało się obliczyć VIF: {e}")
    print("-" * 50)

    # Model Negative Binomial
    try:
        model_nb = sm.NegativeBinomial(y, X_with_const).fit(disp=False)
        print("\n--- SUMMARY NEGATIVE BINOMIAL")
        print(model_nb.summary())
        return model_nb
    except Exception as e:
        print(f"\n Error {e}")
        return None

#klastrowanie
def perform_clustering(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    print(f"\n" + "=" * 50)
    print(f"  ANALIZA KLASTROWANIA (K-Means, k={n_clusters})")
    print("=" * 50)

    df_clust = df.copy()
    features = df_clust.drop(columns=["ilosc_wypadkow"])

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df_clust["klaster"] = kmeans.fit_predict(features_scaled)
    cluster_profile = df_clust.groupby("klaster").mean()
    cluster_profile["liczba_skrzyzowan"] = df_clust.groupby("klaster").size()

    print("\nCHARAKTERYSTYKA KLASTRÓW (ŚREDNIE WARTOŚCI)")
    print(cluster_profile.to_string(formatters={col: "{:.2f}".format for col in cluster_profile.columns}))

    plt.figure(figsize=(10, 6))
    sns.boxplot(x="klaster", y="ilosc_wypadkow", data=df_clust, hue="klaster", palette="Set2", legend=False)
    plt.title("Rozkład liczby wypadków w wydzielonych klastrach", fontsize=14)
    plt.xlabel("Numer klastra")
    plt.ylabel("Ilość wypadków na skrzyżowaniu")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    return df_clust

#wykres wpłytwu czynników
def plot_feature_importance(model_nb, title: str = "Wpływ czynników na liczbę wypadków"):
    params = model_nb.params.drop("const", errors="ignore")
    pvalues = model_nb.pvalues.drop("const", errors="ignore")

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

#wykresy ze średnimi wartościami wewnątrz klastrów
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


def plot_actual_vs_predicted(df_with_clusters, model_nb, title: str = "Top 20 Skrzyżowań: Rzeczywiste wypadki vs Predykcja z modelu"):

    df_plots = df_with_clusters.copy()
    X = df_plots.drop(columns=["ilosc_wypadkow", "klaster"], errors="ignore")
    X_with_const = sm.add_constant(X, has_constant='add')

    # Generowanie predykcji
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



# GŁÓWNA PĘTLA PROGRAMU

if __name__ == "__main__":
    pd.set_option('display.max_columns', None)

    full_data = load_and_clean_data("DATA.csv", "DATA2.csv", "DATA3.csv")

    dropped_cols = ["Średnie_dobowe[poj./24h]", "Suma_z_okresu[poj.]", "odległość_od_centrum", "ustap_pierwszenstwa",
                    "Punkt APR", "pierwszenstwo", "przejscie_dla_pieszych",
                    "inne_znaki", "koniec_drogi_z_pierwszenstwem", "nakaz_wjazdu"]
    manual_data = full_data.drop(columns=[col for col in dropped_cols if col in full_data.columns])

    # Klastrowanie
    data_with_clusters = perform_clustering(manual_data, n_clusters=2)
    plot_cluster_profiles_heatmap(data_with_clusters)

    # Modelowanie
    y_manual = manual_data["ilosc_wypadkow"]
    X_manual = manual_data.drop(columns=["ilosc_wypadkow"])

    fitted_model = estimate_count_models(X_manual, y_manual, label="SELEKCJA RĘCZNA")

    # Wykresy końcowe
    if fitted_model is not None:
        plot_feature_importance(fitted_model)
        plot_actual_vs_predicted(data_with_clusters, fitted_model)
    else:
        print("\n[BŁĄD] Model nie został dopasowany, pomijam wykresy ważności i predykcji.")




















