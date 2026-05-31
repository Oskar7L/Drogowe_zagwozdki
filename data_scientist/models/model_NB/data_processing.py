import pandas as pd


def load_and_clean_data(data_path: str, data2_path: str, data3_path: str) -> pd.DataFrame:
    data = pd.read_csv(data_path, sep=";", encoding="utf-8")
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
        rodzaj_jezdni=("waga_geometrii_drogi", "max"),
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
    full_numeric = merged.select_dtypes(include=["number"])

    dropped_cols = ["Średnie_dobowe[poj./24h]", "Suma_z_okresu[poj.]", "odległość_od_centrum", "ustap_pierwszenstwa",
                    "Punkt APR", "pierwszenstwo", "przejscie_dla_pieszych",
                    "inne_znaki", "koniec_drogi_z_pierwszenstwem", "nakaz_wjazdu", "tramwaje_znak", "suma"]
    manual_data = full_numeric.drop(columns=[col for col in dropped_cols if col in full_numeric.columns])
    return manual_data