
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="Analiza oznakowań na skrzyżowaniu", layout="wide")

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

@st.cache_data
def wczytaj_dane():
    plik_art = 'atrybuty skrzyzowan.csv' 
    plik_wypadki = 'wyczyszczone_dane.csv'
    
    try:
        df_atr = pd.read_csv(plik_art, sep=';').dropna(subset=['id_skrzyzowania'])
        df_atr['id_skrzyzowania'] = df_atr['id_skrzyzowania'].astype(int)
    except FileNotFoundError:
        st.error(f"Błąd: Nie znaleziono pliku '{plik_art}'.")
        return None, None

    try:
        df_wypadki = pd.read_csv(plik_wypadki, sep=',') 
        df_wypadki.columns = df_wypadki.columns.str.strip()
        df_wypadki['id_skrzyzowania'] = pd.to_numeric(df_wypadki['id_skrzyzowania'], errors='coerce').fillna(0).astype(int)
    except FileNotFoundError:
        st.error(f"Błąd: Nie znaleziono pliku '{plik_wypadki}'.")
        return df_atr, None

    return df_atr, df_wypadki

df_atr, df_wypadki = wczytaj_dane()

if df_atr is not None:
    # --- 2. PASEK BOCZNY ---
    st.sidebar.header("Panel Sterowania")
    
    df_atr = df_atr.sort_values('id_skrzyzowania')
    lista_opcji = [f"{int(row['id_skrzyzowania'])}: {row['skrzyzowanie']}" for _, row in df_atr.iterrows()]
    
    wybór = st.sidebar.selectbox("Wybierz skrzyżowanie do analizy:", lista_opcji)
    id_szukane = int(wybór.split(":")[0])

    skrzyzowanie_docelowe = df_atr[df_atr['id_skrzyzowania'] == id_szukane].iloc[0]
    nazwa_skrzyzowania = skrzyzowanie_docelowe['skrzyzowanie']

    # --- Tytuł główny ---
    st.title(f"Analiza oznakowań na skrzyżowaniu")
    st.subheader(f"Skrzyżowanie: {nazwa_skrzyzowania} (ID {id_szukane})")
    st.markdown("---")

    df_atr['suma'] = pd.to_numeric(df_atr['suma'], errors='coerce').fillna(0)
    suma_cel = pd.to_numeric(skrzyzowanie_docelowe['suma'], errors='coerce')
    suma_cel = 0 if pd.isna(suma_cel) else int(suma_cel)
    
    srednia_suma_warszawa = df_atr['suma'].mean()
    roznica_procentowa = ((suma_cel - srednia_suma_warszawa) / srednia_suma_warszawa) * 100 if srednia_suma_warszawa > 0 else 0

    liczba_wypadkow = 0
    tekst_rankingu = "Bezpieczne (0 wypadków)"
    
    if df_wypadki is not None:
        ranking_wypadkow = df_wypadki['id_skrzyzowania'].value_counts().reset_index()
        ranking_wypadkow.columns = ['id_skrzyzowania', 'liczba_wypadkow']
        ranking_wypadkow['pozycja'] = ranking_wypadkow['liczba_wypadkow'].rank(ascending=False, method='min').astype(int)
        
        pozycja_row = ranking_wypadkow[ranking_wypadkow['id_skrzyzowania'] == id_szukane]
        wypadki_cel = df_wypadki[df_wypadki['id_skrzyzowania'] == id_szukane]
        liczba_wypadkow = len(wypadki_cel)
        
        if len(pozycja_row) > 0:
            tekst_rankingu = f"{pozycja_row['pozycja'].values[0]} / {len(ranking_wypadkow)}"


    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Łączna liczba znaków", f"{suma_cel} szt.", f"{roznica_procentowa:+.1f}% vs średnia")
    k2.metric("Suma wypadków w bazie", f"{liczba_wypadkow} zdarzeń")
    k3.metric("Pozycja w rankingu ryzyka", tekst_rankingu)
    k4.metric("Odległość od centrum", f"{str(skrzyzowanie_docelowe['odległość od centrum [km]']).replace(',', '.')} km")

    # --- TUTAJ ZOSTAŁA DODANA INFRASTRUKTURA ROWEROWA I TRAMWAJOWA ---
    st.write("#### Wyposażenie skrzyżowania")
    rower = str(skrzyzowanie_docelowe['ścieżka rowerowa']).strip().upper()
    tramwaj = str(skrzyzowanie_docelowe['tramwaj']).strip().upper()
    
    infra_col1, infra_col2 = st.columns(2)
    with infra_col1:
        if "TAK" in rower:
            st.success("🚴 **Ścieżka rowerowa:** TAK ")
        else:
            st.error("🚴 **Ścieżka rowerowa:** NIE ")
            
    with infra_col2:
        if "TAK" in tramwaj:
            st.success("🚋 **Linia tramwajowa:** TAK ")
        else:
            st.error("🚋 **Linia tramwajowa:** NIE ")

    st.markdown("---")


    kolumny_do_analizy = ['pdp', 'up', 'mp', 'nj', 'tramwaje_znak', 'inne', 'kdzp', 'zw', 'stop', 'zakaz s/z', 'rondo']
    for col in kolumny_do_analizy:
        df_atr[col] = pd.to_numeric(df_atr[col], errors='coerce').fillna(0)

    # Bezpieczne wyciągnięcie wartości numerycznych dla konkretnego wiersza
    wartosci_cel = [pd.to_numeric(skrzyzowanie_docelowe[col], errors='coerce') for col in kolumny_do_analizy]
    wartosci_cel = [0 if pd.isna(v) else v for v in wartosci_cel]
    
    srednia_reszta = df_atr[df_atr['id_skrzyzowania'] != id_szukane][kolumny_do_analizy].mean().values

    x = np.arange(len(kolumny_do_analizy))
    szerokosc = 0.35

    fig1, ax1 = plt.subplots(figsize=(14, 5))
    slupki_cel = ax1.bar(x - szerokosc/2, wartosci_cel, szerokosc, label=f'Skrzyżowanie ID {id_szukane}', color='#1f77b4', edgecolor='black', linewidth=0.7)
    slupki_srednia = ax1.bar(x + szerokosc/2, srednia_reszta, szerokosc, label='Średnia pozostałych skrzyżowań', color='#d3d3d3', edgecolor='gray', linewidth=0.7)
    
    ax1.set_ylabel('Liczba wystąpień / znaków', fontsize=11, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(kolumny_do_analizy, rotation=25, ha='right', fontsize=10, fontweight='bold')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.bar_label(slupki_cel, padding=3, fontsize=9)
    ax1.bar_label(slupki_srednia, padding=3, fmt='%.1f', fontsize=8, color='dimgray')
    
    st.pyplot(fig1)

    st.markdown("---")

    col_lewa, col_prawa = st.columns(2)

    with col_lewa:
        st.write("### Top 3 rodzaje zdarzeń ")
        if df_wypadki is not None and liczba_wypadkow > 0:
            top_3_wypadki = wypadki_cel['rodzaj_zdarzenia'].value_counts().head(3)
            
            fig2, ax2 = plt.subplots(figsize=(7, 4.5))
            y_pos = np.arange(len(top_3_wypadki))
            slupki = ax2.barh(y_pos, top_3_wypadki.values[::-1], color='#ff6b6b', height=0.5, edgecolor='darkred', linewidth=0.8)
            ax2.bar_label(slupki, padding=8, fontsize=10, fontweight='bold', color='darkred')
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(top_3_wypadki.index[::-1], fontsize=9, fontweight='bold')
            ax2.set_xlabel('Liczba zdarzeń', fontsize=10)
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            
            st.pyplot(fig2)
        else:
            st.success("Brak odnotowanych wypadków dla tego obiektu – skrzyżowanie bezpieczne.")

    with col_prawa:
        st.write("### Struktura oznakowania pionowego")
        
        wszystkie_znaki = ['pdp', 'up', 'mp', 'nj', 'tramwaje_znak', 'inne', 'kdzp', 'zw', 'stop', 'zakaz s/z', 'rondo']
        skrzyzowanie_kopia = {}
        for col in wszystkie_znaki:
            v = pd.to_numeric(skrzyzowanie_docelowe[col], errors='coerce')
            skrzyzowanie_kopia[col] = 0 if pd.isna(v) else int(v)

        podzial = {
            'Znaki ostrzegawcze': skrzyzowanie_kopia['up'] + skrzyzowanie_kopia['tramwaje_znak'],
            'Znaki zakazu': skrzyzowanie_kopia['zw'] + skrzyzowanie_kopia['zakaz s/z'] + skrzyzowanie_kopia['stop'],
            'Znaki nakazu': skrzyzowanie_kopia['nj'] + skrzyzowanie_kopia['rondo'],
            'Znaki informacyjne': skrzyzowanie_kopia['pdp'] + skrzyzowanie_kopia['mp'] + skrzyzowanie_kopia['kdzp'] + skrzyzowanie_kopia['inne']
        }

        grupy_sumy = {k: v for k, v in podzial.items() if v > 0}

        if grupy_sumy:
            mapa_kolorow = {'Znaki ostrzegawcze': '#f39c12', 'Znaki zakazu': '#e74c3c', 'Znaki nakazu': '#2ecc71', 'Znaki informacyjne': '#3498db'}
            dane_wykres = pd.Series(grupy_sumy)
            kolory_wykresu = [mapa_kolorow[kat] for kat in dane_wykres.index]

            fig3, ax3 = plt.subplots(figsize=(7, 4.5))
            wedges, texts, autotexts = ax3.pie(
                dane_wykres, autopct=lambda p: f'{p:.1f}%\n({int(p*dane_wykres.sum()/100)} szt.)',
                startangle=140, colors=kolory_wykresu, wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2), pctdistance=0.7
            )
            for at in autotexts:
                at.set_fontsize(9)
                at.set_fontweight('bold')
            ax3.legend(wedges, dane_wykres.index, loc="center left", bbox_to_anchor=(0.9, 0.5), fontsize=9)
            
            st.pyplot(fig3)
        else:
            st.warning("Brak zarejestrowanych znaków pionowych.")

    st.markdown("---")

    with st.expander("Słownik"):
        st.code(
            "pdp           -> Przejście dla pieszych (Znak D-6)\n"
            "up            -> Ustąp pierwszeństwa przejazdu (Znak A-7)\n"
            "mp            -> Droga z pierwszeństwem (Znak D-1)\n"
            "nj            -> Nakaz jazdy po prawej stronie znaku (Znak C-9)\n"
            "tramwaje_znak -> Znak ostrzegawczy \"Tramwaje\" (Znak A-21)\n"
            "inne          -> Inne tablice (Tonaż, tablice informacyjne, oznaczenia)\n"
            "kdzp          -> Koniec drogi z pierwszeństwem (Znak D-2)\n"
            "zw            -> Zakaz wjazdu (Znak B-2)\n"
            "stop          -> Znak STOP (Znak B-20)\n"
            "zakaz s/z     -> Zakaz skrętu / Zakaz zawracania (Znaki B-21, B-23)\n"
            "rondo         -> Skrzyżowanie o ruchu okrężnym (Znak C-12)",
            language="text"
        )

