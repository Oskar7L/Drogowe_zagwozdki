import streamlit as st
import wykresy_3

st.set_page_config(
    page_title="Panel Analizy Bezpieczeństwa Ruchu",
    layout="wide",
    initial_sidebar_state="expanded"
)

_, mapa_skrzyzowan = wykresy_3.load_traffic_data()

st.sidebar.header("Filtry i ustawienia")

opcje_skrzyzowan = [f"{id_skr}: {nazwa}" for id_skr, nazwa in mapa_skrzyzowan.items()]

wybór = st.sidebar.selectbox(
    "Wybierz skrzyżowanie do analizy:",
    options=opcje_skrzyzowan
)

wybrane_id = wybór.split(":")[0]
nazwa_skrzyzowania = mapa_skrzyzowan[wybrane_id]


st.title("Panel Bezpieczeństwa i Natężenia Ruchu")

st.subheader(f"Wybrana lokalizacja: {nazwa_skrzyzowania} (ID: {wybrane_id})")

st.markdown("---")


col1, col2, col3 = st.columns(3)

with col1:
    fig_trend = wykresy_3.plot_trend_zdarzen(wybrane_id)
    st.pyplot(fig_trend)

with col2:
    fig_tydzien = wykresy_3.plot_roklad_tygodniowy(wybrane_id)
    st.pyplot(fig_tydzien)

with col3:
    fig_przyczyny = wykresy_3.plot_najczestsze_przyczyny(wybrane_id)
    st.pyplot(fig_przyczyny)

st.markdown("### Porównanie zdarzeń z natężeniem ruchu drogowego")

tab1, tab2 = st.tabs(["Widok Długoterminowy (SDR)", "Widok Szczegółowy (Dobowy)"])

with tab1:
    try:
        fig_okres = wykresy_3.plot_natezenie_vs_wypadki_okres(wybrane_id)
        st.pyplot(fig_okres)
    except Exception as e:
        st.warning(f"Informacja: {e}")

with tab2:
    try:
        fig_miesiac = wykresy_3.plot_natezenie_vs_wypadki_miesiac(wybrane_id, "2025-06")
        st.pyplot(fig_miesiac)
    except Exception as e:
        st.warning(f"Informacja: {e}")



st.markdown("### Analiza cykliczności i środowiska")
col4, col5, col6 = st.columns(3)

with col4:
    fig_sezon = wykresy_3.plot_sezonowosc_roczna(wybrane_id)
    st.pyplot(fig_sezon)

with col5:
    fig_rodzaj = wykresy_3.plot_rodzaj_zdarzenia(wybrane_id)
    st.pyplot(fig_rodzaj)

with col6:
    fig_pogoda = wykresy_3.plot_warunki_pogodowe(wybrane_id)
    st.pyplot(fig_pogoda)