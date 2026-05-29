import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
import warnings

warnings.filterwarnings('ignore')


def plot_4_kierunek_przesuniecia() -> Figure:
    df = pd.read_csv('eksport_mnlogit_pelny.csv')
    df['Abs_Efekt'] = df['Efekt_Log'].abs()
    df_top = df.sort_values(by='Abs_Efekt', ascending=False).head(15)
    df_top = df_top.sort_values(by='Efekt_Log')
    df_top['Etykieta'] = df_top['Cecha'] + ' -> ' + df_top['Kategoria']

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ['#2e7d32' if val < 0 else '#c62828' for val in df_top['Efekt_Log']]
    ax.barh(df_top['Etykieta'], df_top['Efekt_Log'], color=colors)
    ax.axvline(0, color='black', linewidth=1.5)
    ax.set_title("Kierunek przesunięcia ryzyka (względem Manewrów)", fontweight='bold')
    ax.set_xlabel("<- Zmniejsza ryzyko | Zwiększa ryzyko ->")
    fig.tight_layout()
    return fig


def plot_5_mapa_ciepla() -> Figure:
    df = pd.read_csv('eksport_mnlogit_pelny.csv')
    pivot_df = df.pivot(index='Cecha', columns='Kategoria', values='Efekt_Log').fillna(0)

    fig, ax = plt.subplots(figsize=(8, 10))
    sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Mapa Ciepła Asocjacji (Log-Odds)", fontweight='bold')
    fig.tight_layout()
    return fig


def plot_6_wplyw_cechy(cecha: str) -> Figure:
    df = pd.read_csv('eksport_mnlogit_pelny.csv')
    df_cecha = df[df['Cecha'] == cecha]

    # Zawsze wymuszamy 3 kategorie na osi X, żeby wykresy były spójne
    kategorie_docelowe = ['Dynamika', 'Wymuszenia', 'Piesi']
    wartosci = []

    for kat in kategorie_docelowe:
        wiersz = df_cecha[df_cecha['Kategoria'] == kat]
        if not wiersz.empty:
            wartosci.append(wiersz['Efekt_Log'].values[0])
        else:
            wartosci.append(0.0)  # Brak dowodów statystycznych = zero wpływu na wykresie

    fig, ax = plt.subplots(figsize=(8, 6))

    # Kolorujemy: zielony dla ochrony (spadek), czerwony dla zagrożenia (wzrost), szary dla zera
    kolory = ['#2e7d32' if w < 0 else ('#c62828' if w > 0 else '#9e9e9e') for w in wartosci]

    ax.bar(kategorie_docelowe, wartosci, color=kolory)
    ax.axhline(0, color='black', linewidth=1.5)
    ax.set_title(f"Wpływ cechy '{cecha}' na kategorie wypadków", fontweight='bold')
    ax.set_ylabel("Siła asocjacji (Log-Odds)")

    # Delikatnie rozszerzamy oś Y, żeby puste zera były lepiej widoczne w kontekście
    plt.margins(y=0.2)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    plot_4_kierunek_przesuniecia()
    plot_5_mapa_ciepla()
    plot_6_wplyw_cechy('stop_lz')
    plt.show()