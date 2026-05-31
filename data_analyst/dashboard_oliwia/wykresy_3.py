import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import textwrap


DATA_PATH = r"C:\Users\home\Pulpit\wyczyszczone_dane.csv"
EXCEL_PATH = r"C:\Users\home\Pulpit\Raport_natezenia_dobowe.xlsx"

MAPOWANIE_APR = {
    "WAWELSKA / GRÓJECKA": 3318,
    "IDZIKOWSKIEGO / WITOSA": 3359,
    "PŁASKOWICKIEJ / ROENTGENA": 5347,
    "DOLINA SŁUŻEWIECKA / NOWOURSYNOWSKA": 3379,
    "POLECZKI / PUŁAWSKA": 5398,
    "GÓRCZEWSKA / POWSTAŃCÓW ŚLĄSKICH": 3371,
    "ALEJE JEROZOLIMSKIE / MARSZAŁKOWSKA": 2306,
    "DOMANIEWSKA / WOŁOSKA": 3366,
    "MARSA / ŻOŁNIERSKA": 3306,
    "KŁOPOT / PAMIĘTAJCIE O OGRODACH": 5379,
    "GRÓJECKA / KOPIŃSKA": 5369,
    "NACZELNIKOWSKA / RADZYMIŃSKA": 5312,
    "PROSTA / TOWAROWA": 2303,
    "PROSTA / ŻELAZNA": 2304,
    "HYNKA / ŻWIRKI I WIGURY": 9399,
    "TORUŃSKA / ŁABISZYŃSKA": 3302,
    "ALEJA WILANOWSKA / PUŁAWSKA": 1365,
    "WAWELSKA / ŻWIRKI I WIGURY": 5368,
    "STRAŻACKA / ŻOŁNIERSKA": 1357,
    "MARSZAŁKOWSKA / ŚWIĘTOKRZYSKA": 2306,
    "KRÓLEWSKA / MARSZAŁKOWSKA": 2306, # Wcześniej: 2307
}

BG_COLOR = "#f5f7fb"
PANEL_COLOR = "#ffffff"
TEXT_MAIN = "#1f2937"
TEXT_MUTED = "#6b7280"
GRID_COLOR = "#e5e7eb"

PRIMARY = "#2563eb"
SECONDARY = "#0f766e"
ACCENT = "#d97706"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "axes.titlesize": 11,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})


def _apply_common_style(ax):
    ax.set_facecolor(PANEL_COLOR)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


# Ładowanie danych
def load_traffic_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["data"] = pd.to_datetime(df["data"])
    unique_intersections = sorted(df["skrzyzowanie"].dropna().unique())
    intersection_map = {str(i + 1): name for i, name in enumerate(unique_intersections)}
    inv_map = {v: k for k, v in intersection_map.items()}
    df["intersection_id"] = df["skrzyzowanie"].map(inv_map)
    df["rok_miesiac"] = df["data"].dt.to_period("M")
    df["dzien_tygodnia_num"] = df["data"].dt.dayofweek
    return df, intersection_map


def load_apr_data(apr_id: int) -> pd.DataFrame:
    """Wczytuje dane z konkretnego arkusza Excel, odporne na puste pola i stopki."""
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Nie znaleziono pliku Excel: {EXCEL_PATH}")

    df_raw = pd.read_excel(EXCEL_PATH, sheet_name=str(apr_id), header=None)
    skip = 0
    for idx, row in df_raw.iterrows():
        if len(row) > 0 and str(row[0]).strip() == "Daty":
            skip = idx
            break

    df_apr = pd.read_excel(EXCEL_PATH, sheet_name=str(apr_id), skiprows=skip)
    df_apr = df_apr[['Daty', 'Liczba pojazdów (suma)']].copy()

    df_apr['data'] = pd.to_datetime(df_apr['Daty'], errors='coerce')
    df_apr = df_apr.dropna(subset=['data']).copy()
    df_apr["rok_miesiac"] = df_apr["data"].dt.to_period("M")

    czyste_natezenie = df_apr['Liczba pojazdów (suma)'].astype(str).str.replace(r'[\s,]', '', regex=True)
    df_apr['natezenie'] = pd.to_numeric(czyste_natezenie, errors='coerce')

    return df_apr


# Wykres 1 - Trend (cały okres)
def plot_trend_zdarzen(intersection_id: str) -> Figure:
    df, intersection_map = load_traffic_data()
    selected = df[df["intersection_id"] == intersection_id].copy()
    trend_data = selected.groupby("rok_miesiac").size().to_frame("liczba_zdarzen")
    trend_data.index = trend_data.index.to_timestamp()

    fig, ax = plt.subplots(figsize=(4.5, 3.2), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax)
    ax.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    ax.plot(trend_data.index, trend_data["liczba_zdarzen"], color=PRIMARY, linewidth=2.2)
    ax.fill_between(trend_data.index, trend_data["liczba_zdarzen"], color=PRIMARY, alpha=0.10)
    ax.scatter(trend_data.index, trend_data["liczba_zdarzen"], s=24, color=PRIMARY, edgecolors="white", linewidth=1.0,
               zorder=3)

    ax.set_title("Trend zdarzeń w czasie", loc="left", color=TEXT_MAIN, fontweight="bold")
    ax.set_ylabel("Liczba zdarzeń", color=TEXT_MUTED)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))  # Brak ułamkowych wypadków
    ax.tick_params(axis="x", colors=TEXT_MUTED, rotation=15)

    if len(trend_data.index) > 5:
        ax.set_xticks(trend_data.index[::max(1, len(trend_data.index) // 4)])
    plt.tight_layout()
    return fig


# Wykres 2 - Podział na dni tygodnia
def plot_roklad_tygodniowy(intersection_id: str) -> Figure:
    df, intersection_map = load_traffic_data()
    selected = df[df["intersection_id"] == intersection_id].copy()
    weekday_data = selected.groupby("dzien_tygodnia_num").size().reindex(range(7), fill_value=0)
    dni_pl = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Niedz"]

    fig, ax = plt.subplots(figsize=(4.5, 3.2), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax)
    ax.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    bars = ax.bar(dni_pl, weekday_data.values, color=SECONDARY, width=0.55)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + (height * 0.02 + 0.1),
                str(int(height)), ha="center", va="bottom", fontsize=7.5, color=TEXT_MUTED)

    ax.set_title("Rozkład tygodniowy zdarzeń", loc="left", color=TEXT_MAIN, fontweight="bold")
    ax.set_ylabel("Liczba zdarzeń", color=TEXT_MUTED)
    plt.tight_layout()
    return fig


# Wykres 3 - Najczęstsze przyczyny
def plot_najczestsze_przyczyny(intersection_id: str) -> Figure:
    """Wykres poziomy najczęstszych przyczyn z zawijaniem długich tekstów."""
    df, intersection_map = load_traffic_data()
    selected = df[df["intersection_id"] == intersection_id].copy()

    # Pobieramy 6 najczęstszych wykroczeń
    wykroczenia_data = selected["wykroczenie"].value_counts().sort_values(ascending=True).tail(6)

    wrapped_labels = [textwrap.fill(str(label), width=22) for label in wykroczenia_data.index]

    fig, ax = plt.subplots(figsize=(5.2, 3.8), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax)
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    bars = ax.barh(wrapped_labels, wykroczenia_data.values, color=ACCENT, height=0.55)

    for bar in bars:
        width = bar.get_width()
        if width > 0:
            ax.text(width + (width * 0.02 + 0.1), bar.get_y() + bar.get_height() / 2,
                    f"{int(width)}", va="center", ha="left", fontsize=7.5, color=TEXT_MUTED)

    ax.set_title("Najczęstsze przyczyny zdarzeń", loc="left", color=TEXT_MAIN, fontweight="bold")
    ax.set_xlabel("Liczba wykroczeń", color=TEXT_MUTED)

    ax.tick_params(axis="x", colors=TEXT_MUTED)
    ax.tick_params(axis="y", colors=TEXT_MUTED, labelsize=7.5)

    plt.tight_layout(pad=1.2)
    return fig

# Pobieranie APR
def _get_apr_id_safely(skrzyzowanie_name: str) -> int:
    key = skrzyzowanie_name.strip().upper()
    if key not in MAPOWANIE_APR:
        raise ValueError(f"Skrzyżowanie '{skrzyzowanie_name}' nie ma przypisanego numeru arkusza w słowniku kodu!")
    return MAPOWANIE_APR[key]


# Wykres 4 - Natężenie vs wypadki (w 2025 roku, miesięcznie)
def plot_natezenie_vs_wypadki_okres(intersection_id: str) -> Figure:
    df_acc, intersection_map = load_traffic_data()
    if intersection_id not in intersection_map:
        raise ValueError(f"Brak danych dla ID: {intersection_id}")

    skrzyzowanie_name = intersection_map[intersection_id]
    apr_id = _get_apr_id_safely(skrzyzowanie_name)
    df_traf = load_apr_data(apr_id)

    selected_acc = df_acc[df_acc["intersection_id"] == intersection_id].copy()

    acc_monthly = selected_acc.groupby("rok_miesiac").size().to_frame("liczba_zdarzen")
    acc_monthly.index = acc_monthly.index.to_timestamp()

    traf_monthly = df_traf.groupby("rok_miesiac")["natezenie"].mean().round().to_frame("srednie_natezenie")
    traf_monthly.index = traf_monthly.index.to_timestamp()

    merged = traf_monthly.join(acc_monthly, how='outer').sort_index()

    min_date = traf_monthly.index.min() if not traf_monthly.empty else merged.index.min()
    max_date = traf_monthly.index.max() if not traf_monthly.empty else merged.index.max()
    merged = merged[(merged.index >= min_date) & (merged.index <= max_date)]
    merged["liczba_zdarzen"] = merged["liczba_zdarzen"].fillna(0)

    fig, ax1 = plt.subplots(figsize=(6, 3.5), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax1)
    ax1.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    ax1.bar(merged.index, merged["liczba_zdarzen"], width=20, color=SECONDARY, alpha=0.8, label="Liczba zdarzeń")
    ax1.set_ylabel("Suma zdarzeń", color=SECONDARY, fontweight="bold")
    ax1.tick_params(axis="y", colors=SECONDARY)
    ax1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    ax2 = ax1.twinx()
    for spine in ax2.spines.values():
        spine.set_visible(False)
    ax2.tick_params(length=0)

    ax2.plot(merged.index, merged["srednie_natezenie"], color=PRIMARY, marker='o', linewidth=2.5,
             label="Natężenie (SDR)")
    ax2.set_ylabel("Średnie dobowe natężenie (SDR)", color=PRIMARY, fontweight="bold")
    ax2.tick_params(axis="y", colors=PRIMARY)
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2,
               frameon=False, fontsize=8)

    ax1.set_title("Wypadki a natężenie ruchu (trend miesięczny)", loc="left", color=TEXT_MAIN, fontweight="bold",
                  y=1.15)
    ax1.tick_params(axis="x", colors=TEXT_MUTED, rotation=20)

    plt.tight_layout()
    return fig


# Wykres 5 - Natężenie vs wypadki (w wybranym miesiącu 2025 roku, dobowo)
def plot_natezenie_vs_wypadki_miesiac(intersection_id: str, miesiac: str = "2025-06") -> Figure:
    df_acc, intersection_map = load_traffic_data()
    if intersection_id not in intersection_map:
        raise ValueError(f"Brak danych dla ID: {intersection_id}")

    skrzyzowanie_name = intersection_map[intersection_id]
    apr_id = _get_apr_id_safely(skrzyzowanie_name)
    df_traf = load_apr_data(apr_id)

    miesiac_str = str(miesiac).strip()

    df_traf_miesiac = df_traf[df_traf["rok_miesiac"].astype(str) == miesiac_str].copy()
    if df_traf_miesiac.empty:
        raise ValueError(f"Brak danych natężenia w miesiącu {miesiac} dla skrzyżowania {skrzyzowanie_name}")

    selected_acc = df_acc[df_acc["intersection_id"] == intersection_id].copy()
    selected_acc_miesiac = selected_acc[selected_acc["rok_miesiac"].astype(str) == miesiac_str].copy()

    acc_daily = selected_acc_miesiac.groupby(selected_acc_miesiac["data"].dt.day).size().to_frame("liczba_zdarzen")

    df_traf_miesiac["dzien"] = df_traf_miesiac["data"].dt.day
    df_traf_miesiac.set_index("dzien", inplace=True)

    merged = df_traf_miesiac[["natezenie"]].join(acc_daily, how="outer").sort_index()
    merged["liczba_zdarzen"] = merged["liczba_zdarzen"].fillna(0)

    fig, ax1 = plt.subplots(figsize=(7, 3.5), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax1)
    ax1.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    dni_miesiaca = merged.index.tolist()

    ax1.bar(dni_miesiaca, merged["liczba_zdarzen"], color=SECONDARY, alpha=0.8, width=0.6, label="Liczba zdarzeń")
    ax1.set_ylabel("Liczba zdarzeń", color=SECONDARY, fontweight="bold")
    ax1.tick_params(axis="y", colors=SECONDARY)
    ax1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    ax2 = ax1.twinx()
    for spine in ax2.spines.values():
        spine.set_visible(False)
    ax2.tick_params(length=0)

    ax2.plot(dni_miesiaca, merged["natezenie"], color=PRIMARY, marker='.', linewidth=2, label="Natężenie")
    ax2.set_ylabel("Natężenie dobowe", color=PRIMARY, fontweight="bold")
    ax2.tick_params(axis="y", colors=PRIMARY)
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2,
               frameon=False, fontsize=8)

    ax1.set_title(f"Rozkład dobowy wypadków i ruchu ({miesiac})", loc="left", color=TEXT_MAIN, fontweight="bold",
                  y=1.15)

    ticks_to_show = [dni_miesiaca[i] for i in range(0, len(dni_miesiaca), 2)]
    ax1.set_xticks(ticks_to_show)
    ax1.tick_params(axis="x", colors=TEXT_MUTED)

    plt.tight_layout()
    return fig


# Wykres 6 - Podział na miesiące
def plot_sezonowosc_roczna(intersection_id: str) -> Figure:
    df, intersection_map = load_traffic_data()
    selected = df[df["intersection_id"] == intersection_id].copy()

    miesiac_data = selected.groupby(selected["data"].dt.month).size().reindex(range(1, 13), fill_value=0)
    miesioce_pl = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]

    fig, ax = plt.subplots(figsize=(4.5, 3.2), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax)
    ax.grid(axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    bars = ax.bar(miesioce_pl, miesiac_data.values, color=PRIMARY, width=0.6, alpha=0.9)
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height + (height * 0.02 + 0.1),
                    str(int(height)), ha="center", va="bottom", fontsize=7.5, color=TEXT_MUTED)

    ax.set_title("Sezonowość roczna (Zdarzenia wg miesięcy)", loc="left", color=TEXT_MAIN, fontweight="bold")
    ax.set_ylabel("Suma zdarzeń", color=TEXT_MUTED)
    ax.tick_params(axis="x", colors=TEXT_MUTED, rotation=30)
    ax.tick_params(axis="y", colors=TEXT_MUTED)

    plt.tight_layout()
    return fig


# Wykres 7 - Podział na rodzaje zdarzeń
def plot_rodzaj_zdarzenia(intersection_id: str) -> Figure:
    df, intersection_map = load_traffic_data()
    selected = df[df["intersection_id"] == intersection_id].copy()

    # Bierzemy 4 najczęstsze typy
    rodzaje_data = selected["rodzaj_zdarzenia"].value_counts().head(4)

    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(PANEL_COLOR)

    colors = [PRIMARY, SECONDARY, ACCENT, "#9ca3af"]

    wrapped_labels = [textwrap.fill(l, width=26) for l in rodzaje_data.index]

    wedges, texts, autotexts = ax.pie(
        rodzaje_data.values,
        autopct='%1.0f%%',
        startangle=140,
        colors=colors,
        pctdistance=0.8,  # Procenty ładnie wyśrodkowane na kolorowym pasku
        wedgeprops=dict(width=0.45, edgecolor=PANEL_COLOR, linewidth=1.5)
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(8)

    ax.set_title("Struktura rodzajów zdarzeń", loc="left", color=TEXT_MAIN, fontweight="bold")

    ax.legend(
        wedges,
        wrapped_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=1,
        frameon=False,
        fontsize=8,
        labelcolor=TEXT_MUTED
    )

    plt.subplots_adjust(bottom=0.35, top=0.9, left=0.1, right=0.9)

    return fig


# Wykres 8 - Podział na warunki pogodowe
def plot_warunki_pogodowe(intersection_id: str) -> Figure:
    df, intersection_map = load_traffic_data()
    selected = df[df["intersection_id"] == intersection_id].copy()

    # Filtrujemy pogodę (bierzemy top 4)
    pogoda_data = selected["warunki_pogodowe"].value_counts().sort_values(ascending=True).tail(4)

    fig, ax = plt.subplots(figsize=(4.8, 3.2), dpi=120)
    fig.patch.set_facecolor(BG_COLOR)
    _apply_common_style(ax)
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=0.8)

    bars = ax.barh(pogoda_data.index, pogoda_data.values, color=SECONDARY, height=0.5)
    for bar in bars:
        width = bar.get_width()
        if width > 0:
            ax.text(width + (width * 0.01 + 0.1), bar.get_y() + bar.get_height() / 2,
                    f"{int(width)}", va="center", ha="left", fontsize=7.5, color=TEXT_MUTED)

    ax.set_title("Zdarzenia a warunki pogodowe", loc="left", color=TEXT_MAIN, fontweight="bold")
    ax.set_xlabel("Liczba zdarzeń", color=TEXT_MUTED)
    ax.tick_params(axis="x", colors=TEXT_MUTED)
    ax.tick_params(axis="y", colors=TEXT_MUTED)

    plt.tight_layout()
    return fig