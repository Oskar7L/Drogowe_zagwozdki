import pandas as pd
import charts_visual as visual
from data_processing import load_and_clean_data
from clustering_model import perform_clustering
from regression_model import estimate_count_models

# GŁÓWNA PĘTLA PROGRAMU
if __name__ == "__main__":
    pd.set_option('display.max_columns', None)

    manual_data = load_and_clean_data("DATA.csv", "DATA2.csv", "DATA3.csv")

    visual.plot_correlation_matrix(manual_data, title="Pełna macierz korelacji cech")

    data_with_clusters = perform_clustering(manual_data, n_clusters=2)
    visual.plot_cluster_boxplot(data_with_clusters)
    visual.plot_cluster_profiles_heatmap(data_with_clusters)

    y_manual = manual_data["ilosc_wypadkow"]
    X_manual = manual_data.drop(columns=["ilosc_wypadkow"])

    fitted_model = estimate_count_models(X_manual, y_manual, label="SELEKCJA RĘCZNA")

    if fitted_model is not None:
        visual.plot_feature_importance(fitted_model)
        visual.plot_actual_vs_predicted(data_with_clusters, fitted_model)
    else:
        print("\nModel nie został dopasowany, pomijam wykresy ważności i predykcji.")