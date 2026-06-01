import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import warnings

warnings.filterwarnings('ignore')


def plot_1_forest_plot(kategoria: str) -> Figure:
    df = pd.read_csv('eksport_ovr_pelny.csv')
    df_kat = df[df['Kategoria'] == kategoria].copy()
    df_kat = df_kat.sort_values(by='OR', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.errorbar(df_kat['OR'], df_kat['Cecha'], xerr=0.1, fmt='o', color='#006d77', ecolor='#006d77', capsize=4)
    ax.axvline(1.0, color='red', linestyle='--')
    ax.set_title(f"Ilorazy Szans (Forest Plot) dla: {kategoria}", fontweight='bold')
    ax.set_xlabel("OR > 1 (wzrost ryzyka) | OR < 1 (spadek ryzyka)")
    fig.tight_layout()
    return fig


def plot_2_diverging_bar(kategoria: str) -> Figure:
    df = pd.read_csv('eksport_ovr_pelny.csv')
    df_kat = df[df['Kategoria'] == kategoria].copy()
    df_kat['Log_OR'] = np.log(df_kat['OR'])
    df_kat['Abs_Log_OR'] = df_kat['Log_OR'].abs()
    df_top = df_kat.sort_values(by='Abs_Log_OR', ascending=False).head(10)
    df_top = df_top.sort_values(by='Log_OR')

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#1e7145' if val < 0 else '#b30000' for val in df_top['Log_OR']]
    ax.barh(df_top['Cecha'], df_top['Log_OR'], color=colors)
    ax.axvline(0, color='black', linewidth=1.5)
    ax.set_title(f"Top 10 cech infrastruktury dla: {kategoria}", fontweight='bold')
    ax.set_xlabel("Wzrost / Spadek mnożnika ryzyka (Log-Odds)")
    fig.tight_layout()
    return fig


def plot_3_radar_chart(cecha: str) -> Figure:
    df = pd.read_csv('eksport_ovr_pelny.csv')
    df_cecha = df[df['Cecha'] == cecha]

    kategorie = df_cecha['Kategoria'].tolist()
    wartosci = df_cecha['OR'].tolist()

    if not wartosci:
        fig, ax = plt.subplots()
        return fig

    kategorie += kategorie[:1]
    wartosci += wartosci[:1]

    katy = np.linspace(0, 2 * np.pi, len(kategorie), endpoint=True)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(katy, wartosci, color='#d35400', linewidth=2)
    ax.fill(katy, wartosci, color='#d35400', alpha=0.3)
    ax.plot(katy, [1.0] * len(katy), color='black', linestyle='--', linewidth=1, alpha=0.5)

    ax.set_xticks(katy[:-1])
    ax.set_xticklabels(kategorie[:-1], fontweight='bold', fontsize=12)
    ax.set_title(f"Profil Ryzyka dla: {cecha}", fontweight='bold', pad=20)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    plot_1_forest_plot('Dynamika')
    plot_2_diverging_bar('Dynamika')
    plot_3_radar_chart('sygnalizacja_obecna')
    plt.show()