"""
Strona główna dashboardu – najważniejsze cechy i wzorce w danych o zdarzeniach
drogowych pokazane na "dużych" wykresach (cały zbiór, wszystkie skrzyżowania).

Uruchomienie:
    streamlit run strona_glowna_streamlit.py

Wymagany plik (w tym samym folderze co skrypt):
    - wyczyszczone_dane.csv
"""

from pathlib import Path
import textwrap

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Strona główna – zdarzenia drogowe",
    layout="wide",
    initial_sidebar_state="expanded",
)

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

# Spójna paleta kolorów dla całej strony
GLOWNY = "#1f77b4"
AKCENT = "#ff6b6b"
ZIELONY = "#2ecc71"
POMARANCZ = "#f39c12"

DNI_TYGODNIA = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
MIESIACE = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]


def _znajdz_plik(nazwa: str) -> Path:
    """Szuka pliku obok skryptu, a następnie w typowych folderach repozytorium."""
    tutaj = Path(__file__).resolve().parent
    kandydaci = [
        tutaj / nazwa,
        tutaj.parent.parent / "dashboard_devs" / nazwa,
        tutaj.parent.parent / "data_engineer" / "nowe_dane" / nazwa,
        Path.cwd() / nazwa,
    ]
    for sciezka in kandydaci:
        if sciezka.exists():
            return sciezka
    raise FileNotFoundError(f"Nie znaleziono pliku '{nazwa}'. Umieść go w folderze ze skryptem.")


@st.cache_data
def wczytaj_dane() -> pd.DataFrame:
    df = pd.read_csv(_znajdz_plik("wyczyszczone_dane.csv"), sep=",", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["rok"] = df["data"].dt.year
    df["miesiac"] = df["data"].dt.month
    df["dzien_tygodnia"] = df["data"].dt.dayofweek
    return df


def _styl_osi(ax):
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


# --- Wykresy ---------------------------------------------------------------

def wykres_trend_roczny(df: pd.DataFrame):
    dane = df.groupby("rok").size()
    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(dane.index, dane.values, marker="o", color=GLOWNY, linewidth=2.5)
    ax.fill_between(dane.index, dane.values, color=GLOWNY, alpha=0.12)
    for x, y in zip(dane.index, dane.values):
        ax.text(x, y, f"{int(y)}", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#34495e")
    ax.set_title("Liczba zdarzeń w czasie (wszystkie skrzyżowania)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Rok")
    ax.set_ylabel("Liczba zdarzeń")
    ax.set_xticks(dane.index)
    _styl_osi(ax)
    fig.tight_layout()
    return fig


def wykres_top_skrzyzowania(df: pd.DataFrame, top_n: int = 15):
    dane = df["skrzyzowanie"].value_counts().head(top_n).sort_values()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    slupki = ax.barh(dane.index.astype(str), dane.values, color=GLOWNY, edgecolor="black", linewidth=0.6)
    ax.bar_label(slupki, padding=4, fontsize=9, fontweight="bold")
    ax.set_title(f"Skrzyżowania z największą liczbą zdarzeń (Top {len(dane)})", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Liczba zdarzeń")
    _styl_osi(ax)
    fig.tight_layout()
    return fig


def _wykres_poziomy(seria: pd.Series, tytul: str, kolor: str, szerokosc_zawijania: int = 28):
    etykiety = [textwrap.fill(str(x), szerokosc_zawijania) for x in seria.index]
    fig, ax = plt.subplots(figsize=(7, 5))
    slupki = ax.barh(etykiety, seria.values, color=kolor, edgecolor="black", linewidth=0.5)
    ax.bar_label(slupki, padding=4, fontsize=9, fontweight="bold")
    ax.set_title(tytul, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Liczba zdarzeń")
    _styl_osi(ax)
    fig.tight_layout()
    return fig


def wykres_top_wykroczenia(df: pd.DataFrame, top_n: int = 10):
    dane = df["wykroczenie"].value_counts().head(top_n).sort_values()
    return _wykres_poziomy(dane, "Najczęstsze wykroczenia", AKCENT)


def wykres_rodzaje_zdarzen(df: pd.DataFrame, top_n: int = 8):
    dane = df["rodzaj_zdarzenia"].value_counts().head(top_n).sort_values()
    return _wykres_poziomy(dane, "Najczęstsze rodzaje zdarzeń", GLOWNY)


def wykres_dni_tygodnia(df: pd.DataFrame):
    dane = df["dzien_tygodnia"].value_counts().reindex(range(7), fill_value=0).sort_index()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    slupki = ax.bar(DNI_TYGODNIA, dane.values, color=ZIELONY, edgecolor="black", linewidth=0.5)
    ax.bar_label(slupki, padding=3, fontsize=9, fontweight="bold")
    ax.set_title("Zdarzenia wg dnia tygodnia", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Liczba zdarzeń")
    ax.tick_params(axis="x", rotation=30)
    _styl_osi(ax)
    fig.tight_layout()
    return fig


def wykres_sezonowosc(df: pd.DataFrame):
    dane = df["miesiac"].value_counts().reindex(range(1, 13), fill_value=0).sort_index()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    slupki = ax.bar(MIESIACE, dane.values, color=POMARANCZ, edgecolor="black", linewidth=0.5)
    ax.bar_label(slupki, padding=3, fontsize=8, fontweight="bold")
    ax.set_title("Sezonowość – zdarzenia wg miesięcy", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Liczba zdarzeń")
    _styl_osi(ax)
    fig.tight_layout()
    return fig


def wykres_cecha(df: pd.DataFrame, kolumna: str, tytul: str, kolor: str):
    dane = df[kolumna].value_counts().head(6).sort_values()
    return _wykres_poziomy(dane, tytul, kolor, szerokosc_zawijania=22)


# --- Interfejs -------------------------------------------------------------

df = wczytaj_dane()

st.title("Bezpieczeństwo ruchu – przegląd ogólny")
st.caption("Najważniejsze cechy i wzorce we wszystkich danych o zdarzeniach drogowych.")

st.sidebar.header("Filtry i ustawienia")
lata = sorted(df["rok"].dropna().astype(int).unique())
rok_min, rok_max = int(lata[0]), int(lata[-1])
zakres = st.sidebar.slider("Zakres lat", rok_min, rok_max, (rok_min, rok_max))
top_n = st.sidebar.slider("Liczba skrzyżowań (Top N)", 5, len(df["skrzyzowanie"].unique()), 15)

df = df[(df["rok"] >= zakres[0]) & (df["rok"] <= zakres[1])]

if df.empty:
    st.warning("Brak zdarzeń w wybranym zakresie lat.")
    st.stop()

# KPI
najczestsze_wykroczenie = df["wykroczenie"].mode().iloc[0] if not df["wykroczenie"].dropna().empty else "brak danych"
najgorsze_skrzyzowanie = df["skrzyzowanie"].value_counts().index[0]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Liczba zdarzeń", f"{len(df):,}".replace(",", " "))
k2.metric("Liczba skrzyżowań", df["id_skrzyzowania"].nunique())
k3.metric("Zakres lat", f"{zakres[0]}–{zakres[1]}")
k4.metric("Najczęstsze wykroczenie", najczestsze_wykroczenie)
k5.metric("Najwięcej zdarzeń", najgorsze_skrzyzowanie)

st.markdown("---")

# Zdarzenia w czasie – duży wykres na całą szerokość
st.pyplot(wykres_trend_roczny(df))

st.markdown("---")

# Gdzie najczęściej dochodzi do zdarzeń – duży wykres na całą szerokość
st.pyplot(wykres_top_skrzyzowania(df, top_n))

st.markdown("### Co i jak często się dzieje")
col_a, col_b = st.columns(2)
with col_a:
    st.pyplot(wykres_top_wykroczenia(df))
with col_b:
    st.pyplot(wykres_rodzaje_zdarzen(df))

st.markdown("### Kiedy dochodzi do zdarzeń (cykliczność)")
col_c, col_d = st.columns(2)
with col_c:
    st.pyplot(wykres_dni_tygodnia(df))
with col_d:
    st.pyplot(wykres_sezonowosc(df))

st.markdown("### Warunki w chwili zdarzenia")
col_e, col_f, col_g = st.columns(3)
with col_e:
    st.pyplot(wykres_cecha(df, "sygnalizacja", "Sygnalizacja świetlna", GLOWNY))
with col_f:
    st.pyplot(wykres_cecha(df, "warunki_oswietleniowe", "Warunki oświetleniowe", POMARANCZ))
with col_g:
    st.pyplot(wykres_cecha(df, "warunki_pogodowe", "Warunki pogodowe", ZIELONY))

with st.expander("O danych"):
    st.write(
        f"Źródło: `wyczyszczone_dane.csv` – {len(wczytaj_dane()):,}".replace(",", " ")
        + f" zdarzeń z {len(lata)} lat ({rok_min}–{rok_max}) dla {df['id_skrzyzowania'].nunique()} skrzyżowań. "
        "Wykresy pokazują cały zbiór; szczegóły pojedynczego skrzyżowania znajdują się w pozostałych zakładkach dashboardu."
    )
