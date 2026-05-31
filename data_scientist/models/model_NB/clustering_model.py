import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

#klastrowanie
def perform_clustering(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    print(f"  ANALIZA KLASTROWANIA (K-Means, k={n_clusters})")

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

    return df_clust