import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
import warnings

warnings.filterwarnings('ignore')

def plot_7_ranking_waznosci() -> Figure:
    df = pd.read_csv('eksport_rf_waznosc.csv').sort_values(by='Waga', ascending=True).tail(15)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(df['Cecha'], df['Waga'], color='#2c82c9')
    ax.set_title("Ważność permutacyjna cech w modelu Lasów Losowych", fontweight='bold')
    ax.set_xlabel("Spadek skuteczności modelu po wyłączeniu cechy")
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    fig.tight_layout()
    return fig

def plot_8_macierz_bledow() -> Figure:
    df = pd.read_csv('eksport_macierz.csv', index_col=0)

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(df, annot=True, fmt=".1f", cmap="Blues", cbar_kws={'label': 'Trafność (%)'}, ax=ax)
    ax.set_title("Ewaluacja Klasyfikatora (Macierz Błędów w %)", fontweight='bold')
    ax.set_ylabel("Prawdziwa Kategoria Zdarzenia", fontweight='bold')
    ax.set_xlabel("Decyzja Algorytmu", fontweight='bold')
    fig.tight_layout()
    return fig

def plot_9_metryki_klasyfikacji() -> Figure:
    df = pd.read_csv('eksport_raport.csv', index_col=0)
    kategorie = ['Manewry', 'Dynamika', 'Wymuszenia', 'Piesi']
    df_metryki = df.loc[kategorie, ['precision', 'recall']]
    df_metryki.columns = ['Precyzja', 'Czułość']

    fig, ax = plt.subplots(figsize=(10, 6))
    df_metryki.plot(kind='bar', ax=ax, colormap='Set1')
    ax.set_title("Osiągi Modelu: Precyzja i Czułość", fontweight='bold')
    ax.set_ylabel("Wartość metryki (0 - 1.0)")
    plt.xticks(rotation=0)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=2)
    fig.tight_layout()
    return fig

def plot_10_macierz_korelacji() -> Figure:
    df = pd.read_csv('Ostateczna_Baza_Analiza.csv')

    zmienne_do_usuniecia = ['data', 'skrzyzowanie', 'wykroczenie', 'sygnalizacja', 'warunki_pogodowe',
                            'warunki_oswietleniowe', 'stan_nawierzchni', 'ustap_pierwszenstwa_lz',
                            'koniec_drogi_z_pierwszenstwem_lz', 'tramwaj']
    df = df.drop(columns=[col for col in zmienne_do_usuniecia if col in df.columns], errors='ignore')

    df_korelacja = pd.get_dummies(df, columns=['Y_kategoria'], dtype=int)

    kolumny_y = [col for col in df_korelacja.columns if col.startswith('Y_kategoria_')]
    kolumny_x = [col for col in df_korelacja.columns if col not in kolumny_y]

    df_korelacja[kolumny_x] = df_korelacja[kolumny_x].apply(pd.to_numeric, errors='coerce').fillna(0)

    pelna_macierz = df_korelacja.corr()
    macierz_xy = pelna_macierz.loc[kolumny_x, kolumny_y]

    macierz_xy.columns = [col.replace('Y_kategoria_', '') for col in macierz_xy.columns]

    fig, ax = plt.subplots(figsize=(14, 10))

    sns.heatmap(
        macierz_xy,
        annot=True,
        cmap='coolwarm',
        fmt=".2f",
        linewidths=0.3,
        vmin=-0.3,
        vmax=0.3,
        cbar_kws={"shrink": .7},
        annot_kws={"size": 6},
        ax=ax
    )

    ax.set_title(
        'Korelacja czynników infrastrukturalnych i pogodowych z typem wykroczenia',
        fontsize=12,
        pad=12,
        fontweight='bold'
    )

    plt.xticks(rotation=0)
    plt.yticks(fontsize=8)
    fig.tight_layout()

    return fig

if __name__ == "__main__":
    plot_7_ranking_waznosci()
    plot_8_macierz_bledow()
    plot_9_metryki_klasyfikacji()
    plot_10_macierz_korelacji()
    plt.show()