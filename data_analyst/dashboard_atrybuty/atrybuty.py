import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

def wizualizuj_atrybuty(sciezka_do_pliku, id_szukane):
    try:
        df = pd.read_csv(sciezka_do_pliku, sep=';')
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku '{sciezka_do_pliku}'.")
        return

    df = df.dropna(subset=['id_skrzyzowania'])
    df['id_skrzyzowania'] = df['id_skrzyzowania'].astype(int)

    if id_szukane not in df['id_skrzyzowania'].values:
        print(f"Błąd: Skrzyżowanie o ID {id_szukane} nie istnieje w bazie.")
        return

    skrzyzowanie_docelowe = df[df['id_skrzyzowania'] == id_szukane].iloc[0]
    nazwa_skrzyzowania = skrzyzowanie_docelowe['skrzyzowanie']

    kolumny_do_analizy = ['pdp', 'up', 'mp', 'nj', 'tramwaje_znak', 
                          'inne', 'kdzp', 'zw', 'stop', 'zakaz s/z', 'rondo']
    
    for col in kolumny_do_analizy:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    wartosci_cel = skrzyzowanie_docelowe[kolumny_do_analizy].values
    srednia_reszta = df[df['id_skrzyzowania'] != id_szukane][kolumny_do_analizy].mean().values
    

    df['suma'] = pd.to_numeric(df['suma'], errors='coerce').fillna(0)
    suma_cel = skrzyzowanie_docelowe['suma']
    srednia_suma_warszawa = df['suma'].mean()

    x = np.arange(len(kolumny_do_analizy))
    szerokosc = 0.35

    fig, ax = plt.subplots(figsize=(14, 7)) 
    
    slupki_cel = ax.bar(x - szerokosc/2, wartosci_cel, szerokosc, 
                        label=f'Skrzyżowanie ID {id_szukane}', color='#1f77b4', edgecolor='black', linewidth=0.7)
    slupki_srednia = ax.bar(x + szerokosc/2, srednia_reszta, szerokosc, 
                            label='Średnia pozostałych skrzyżowań', color='#d3d3d3', edgecolor='gray', linewidth=0.7)

    ax.set_ylabel('Liczba wystąpień / znaków', fontsize=12, fontweight='bold')
    ax.set_title(f'Analiza porównawcza infrastruktury dla: {nazwa_skrzyzowania}', fontsize=14, fontweight='bold', pad=25)
    ax.set_xticks(x)
    ax.set_xticklabels(kolumny_do_analizy, rotation=35, ha='right', fontsize=11, fontweight='bold')
    

    ax.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=2)

    ax.bar_label(slupki_cel, padding=3, fontsize=10)
    ax.bar_label(slupki_srednia, padding=3, fmt='%.1f', fontsize=9, color='dimgray')


    tekst_znaki = (
        f"ŁĄCZNA LICZBA ZNAKÓW\n"
        f"====================\n"
        f"To skrzyżowanie: {int(suma_cel)}\n"
        f"Średnia Warszawa: {srednia_suma_warszawa:.1f}\n"
        f"Różnica: {(((suma_cel - srednia_suma_warszawa)/srednia_suma_warszawa)*100):+.1f}%"
    )
    props = dict(boxstyle='round,pad=1', facecolor='#e6f2ff', edgecolor='#1f77b4', alpha=0.95)
    ax.text(0.98, 0.95, tekst_znaki, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', horizontalalignment='right', bbox=props, family='monospace')


    plt.subplots_adjust(bottom=0.22)
    plt.show()

def analiza_szczegolowa_wypadkow(plik_atrybuty, plik_wypadki, id_szukane):

    try:
        df_atr = pd.read_csv(plik_atrybuty, sep=';').dropna(subset=['id_skrzyzowania'])
        df_atr['id_skrzyzowania'] = df_atr['id_skrzyzowania'].astype(int)
        skrzyzowanie_docelowe = df_atr[df_atr['id_skrzyzowania'] == id_szukane].iloc[0]
        nazwa_skrzyzowania = skrzyzowanie_docelowe['skrzyzowanie']
        
        dystans = str(skrzyzowanie_docelowe['odległość od centrum [km]']).replace(',', '.')
        rower = str(skrzyzowanie_docelowe['ścieżka rowerowa']).strip().lower()
        tramwaj = str(skrzyzowanie_docelowe['tramwaj']).strip().lower()
    except IndexError:
        print(f"Błąd: Nie znaleziono skrzyżowania o ID {id_szukane} w atrybutach.")
        return

    try:
        df_wypadki = pd.read_csv(plik_wypadki, sep=',') 
        df_wypadki.columns = df_wypadki.columns.str.strip()
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {plik_wypadki}.")
        return

    ranking_wypadkow = df_wypadki['id_skrzyzowania'].value_counts().reset_index()
    ranking_wypadkow.columns = ['id_skrzyzowania', 'liczba_wypadkow']

    ranking_wypadkow['pozycja'] = ranking_wypadkow['liczba_wypadkow'].rank(ascending=False, method='min').astype(int)
    
    pozycja_row = ranking_wypadkow[ranking_wypadkow['id_skrzyzowania'] == id_szukane]
    
    if len(pozycja_row) > 0:
        miejsce_w_rankingu = pozycja_row['pozycja'].values[0]
        wszystkich_skrzyzowan_w_bazie = len(ranking_wypadkow)
        tekst_rankingu = f"{miejsce_w_rankingu} / {wszystkich_skrzyzowan_w_bazie} (w bazie wypadków)"
    else:
        tekst_rankingu = "Bezpieczne (0 wypadków w bazie)"

    wypadki_cel = df_wypadki[df_wypadki['id_skrzyzowania'] == id_szukane]
    liczba_wypadkow = len(wypadki_cel)

    if liczba_wypadkow == 0:
        print(f"\n Dla skrzyżowania {nazwa_skrzyzowania} nie odnotowano żadnych wypadków.")
        return

    top_3_wypadki = wypadki_cel['rodzaj_zdarzenia'].value_counts().head(3)


    fig, ax = plt.subplots(figsize=(12, 6))

    y_pos = np.arange(len(top_3_wypadki))
    wartosci = top_3_wypadki.values[::-1]
    etykiety = top_3_wypadki.index[::-1]

    slupki = ax.barh(y_pos, wartosci, color='#ff6b6b', height=0.5, edgecolor='darkred', linewidth=0.8)
    ax.bar_label(slupki, padding=8, fontsize=12, fontweight='bold', color='darkred')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(etykiety, fontsize=11, fontweight='bold')
    ax.set_xlabel('Liczba zdarzeń', fontsize=12)
    ax.set_title(f'Profil bezpieczeństwa: {nazwa_skrzyzowania}', fontsize=15, fontweight='bold', pad=25)
    
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    tekst_info = (
        f"Suma wypadków: {liczba_wypadkow}\n"
        f"MIEJSCE W RANKINGU: {tekst_rankingu}\n"
        f"Odległość od centrum: {dystans} km\n"
        f"Ścieżka rowerowa: {rower.upper()}\n"
        f"Linia tramwajowa: {tramwaj.upper()}"
    )
    
    props = dict(boxstyle='round,pad=0.8', facecolor='#fff5f5', edgecolor='#ff6b6b', alpha=0.95)
    ax.text(0.95, 0.05, tekst_info, transform=ax.transAxes, fontsize=11,
            verticalalignment='bottom', horizontalalignment='right', bbox=props, family='monospace')

    plt.tight_layout()
    plt.show()
    
def analiza_grup_znakow(sciezka_do_pliku, id_szukane):
    try:
        df = pd.read_csv(sciezka_do_pliku, sep=';')
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku '{sciezka_do_pliku}'.")
        return

    df = df.dropna(subset=['id_skrzyzowania'])
    df['id_skrzyzowania'] = df['id_skrzyzowania'].astype(int)

    if id_szukane not in df['id_skrzyzowania'].values:
        print(f"Błąd: Skrzyżowanie o ID {id_szukane} nie istnieje w bazie.")
        return

    skrzyzowanie_docelowe = df[df['id_skrzyzowania'] == id_szukane].iloc[0].copy()
    nazwa_skrzyzowania = skrzyzowanie_docelowe['skrzyzowanie']

    wszystkie_znaki = ['pdp', 'up', 'mp', 'nj', 'tramwaje_znak', 'inne', 'kdzp', 'zw', 'stop', 'zakaz s/z', 'rondo']
    for col in wszystkie_znaki:
        skrzyzowanie_docelowe[col] = pd.to_numeric(skrzyzowanie_docelowe[col], errors='coerce')
        if pd.isna(skrzyzowanie_docelowe[col]):
            skrzyzowanie_docelowe[col] = 0

    podzial = {
        'Znaki ostrzegawcze': skrzyzowanie_docelowe['up'] + skrzyzowanie_docelowe['tramwaje_znak'],
        'Znaki zakazu': skrzyzowanie_docelowe['zw'] + skrzyzowanie_docelowe['zakaz s/z'] + skrzyzowanie_docelowe['stop'],
        'Znaki nakazu': skrzyzowanie_docelowe['nj'] + skrzyzowanie_docelowe['rondo'],
        'Znaki informacyjne': skrzyzowanie_docelowe['pdp'] + skrzyzowanie_docelowe['mp'] + skrzyzowanie_docelowe['kdzp'] + skrzyzowanie_docelowe['inne']
    }

    grupy_sumy = {kategoria: suma for kategoria, suma in podzial.items() if suma > 0}

    if not grupy_sumy:
        print(f"Brak zarejestrowanych znaków pionowych dla ID {id_szukane}.")
        return


    mapa_kolorow = {
        'Znaki ostrzegawcze': '#f39c12', 
        'Znaki zakazu': '#e74c3c',        
        'Znaki nakazu': '#2ecc71',        
        'Znaki informacyjne': '#3498db'  
    }


    dane_wykres = pd.Series(grupy_sumy)
    kolory_wykresu = [mapa_kolorow[kat] for kat in dane_wykres.index]

    fig, ax = plt.subplots(figsize=(12, 7))
    
    wedges, texts, autotexts = ax.pie(
        dane_wykres, 
        autopct=lambda p: f'{p:.1f}%\n({int(p*dane_wykres.sum()/100)} szt.)',
        startangle=140,
        colors=kolory_wykresu,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2),
        pctdistance=0.75
    )

    ax.set_title(
        f"Struktura oznakowania pionowego\nSkrzyżowanie: {nazwa_skrzyzowania}", 
        fontsize=15, 
        fontweight='bold', 
        pad=30
    )

    for at in autotexts:
        at.set_fontsize(11)
        at.set_fontweight('bold')
        at.set_color('black')


    ax.legend(
        wedges, 
        dane_wykres.index,
        title="Grupy znaków",
        title_fontproperties={'weight': 'bold', 'size': 12},
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=11
    )

    plt.tight_layout()
    plt.show()
    
def wykres_slownika_oznaczen():

    fig, ax = plt.subplots(figsize=(10, 7), facecolor='white')
    ax.axis('off')
    
    slownik_tekst = (
        " LEGENDA OZNACZEŃ ATYBUTÓW I ZNAKÓW DROGOWYCH\n"
        "=========================================================\n\n"
        "  pdp ->   Przejście dla pieszych (Znak D-6)\n\n"
        "  up  ->   Ustąp pierwszeństwa przejazdu (Znak A-7)\n\n"
        "  mp  ->   Droga z pierwszeństwem (Znak D-1)\n\n"
        "  nj  ->   Nakaz jazdy po prawej stronie znaku (Znak C-9)\n\n"
        "  tramwaje_znak ->   Znak ostrzegawczy \"Tramwaje\" (Znak A-21)\n\n"
        "  inne ->   Inne tablice (np. Tonaż, znaki informacyjne, oznaczenia)\n\n"
        "  kdzp ->   Koniec drogi z pierwszeństwem (Znak D-2)\n\n"
        "  zw   ->   Zakaz wjazdu (Znak B-2)\n\n"
        "  stop ->   Znak STOP (Znak B-20)\n\n"
        "  zakaz s/z ->   Zakaz skrętu / Zakaz zawracania (Znaki B-21, B-23)\n\n"
        "  rondo ->   Skrzyżowanie o ruchu okrężnym (Znak C-12)\n\n"
        "=========================================================\n"
       
    )
    
    ax.text(
        0.05, 0.95,               
        slownik_tekst, 
        fontsize=12, 
        fontweight='bold', 
        family='monospace',       
        verticalalignment='top', 
        horizontalalignment='left',
        color='#2c3e50'           
    )
    
    plt.tight_layout()
    plt.show()
    
plik_art = 'atrybuty skrzyzowan.csv' 
plik_wypadki = 'wyczyszczone_dane.csv'

try:
    id_podane = int(input("Podaj ID skrzyżowania do wizualizacji (np. 20): "))
    wizualizuj_atrybuty(plik_art, id_podane)
    wykres_slownika_oznaczen()
    analiza_szczegolowa_wypadkow(plik_art, plik_wypadki, id_podane)
    analiza_grup_znakow(plik_art, id_podane)
except ValueError:
    print("Podano nieprawidłowe ID. Musi to być liczba całkowita.")