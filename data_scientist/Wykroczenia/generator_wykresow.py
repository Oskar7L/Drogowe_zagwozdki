import os
import pandas as pd
import matplotlib.pyplot as plt
import wykresy_1_ovr
import wykresy_2_mnlogit
import wykresy_3_rf

os.makedirs('Gotowe_Wykresy', exist_ok=True)

kategorie = ['Piesi', 'Wymuszenia', 'Dynamika', 'Manewry']

tabela_waznosci = pd.read_csv('eksport_rf_waznosc.csv')
cechy_infrastruktury = tabela_waznosci['Cecha'].unique()

fig_ranking = wykresy_3_rf.plot_7_ranking_waznosci()
fig_ranking.savefig('Gotowe_Wykresy/7_Ranking_Waznosci.png', bbox_inches='tight', dpi=300)
plt.close(fig_ranking)

fig_macierz = wykresy_3_rf.plot_8_macierz_bledow()
fig_macierz.savefig('Gotowe_Wykresy/8_Macierz_Bledow.png', bbox_inches='tight', dpi=300)
plt.close(fig_macierz)

fig_metryki = wykresy_3_rf.plot_9_metryki_klasyfikacji()
fig_metryki.savefig('Gotowe_Wykresy/9_Metryki_Klasyfikacji.png', bbox_inches='tight', dpi=300)
plt.close(fig_metryki)

fig_korelacja = wykresy_3_rf.plot_10_macierz_korelacji()
fig_korelacja.savefig('Gotowe_Wykresy/10_Macierz_Korelacji.png', bbox_inches='tight', dpi=300)
plt.close(fig_korelacja)

fig_przesuniecie = wykresy_2_mnlogit.plot_4_kierunek_przesuniecia()
fig_przesuniecie.savefig('Gotowe_Wykresy/4_Kierunek_Przesuniecia.png', bbox_inches='tight', dpi=300)
plt.close(fig_przesuniecie)

fig_mapa = wykresy_2_mnlogit.plot_5_mapa_ciepla()
fig_mapa.savefig('Gotowe_Wykresy/5_Mapa_Ciepla.png', bbox_inches='tight', dpi=300)
plt.close(fig_mapa)

for kat in kategorie:
    fig_forest = wykresy_1_ovr.plot_1_forest_plot(kat)
    fig_forest.savefig(f'Gotowe_Wykresy/1_Forest_{kat}.png', bbox_inches='tight', dpi=300)
    plt.close(fig_forest)

    fig_div_bar = wykresy_1_ovr.plot_2_diverging_bar(kat)
    fig_div_bar.savefig(f'Gotowe_Wykresy/2_Diverging_Bar_{kat}.png', bbox_inches='tight', dpi=300)
    plt.close(fig_div_bar)

for cecha in cechy_infrastruktury:
    bezpieczna_nazwa = cecha.replace('/', '_')
    fig_radar = wykresy_1_ovr.plot_3_radar_chart(cecha)
    fig_radar.savefig(f'Gotowe_Wykresy/3_Radar_{bezpieczna_nazwa}.png', bbox_inches='tight', dpi=300)
    plt.close(fig_radar)

for cecha in cechy_infrastruktury:
    bezpieczna_nazwa = cecha.replace('/', '_')
    fig_wplyw = wykresy_2_mnlogit.plot_6_wplyw_cechy(cecha)
    fig_wplyw.savefig(f'Gotowe_Wykresy/6_Wplyw_{bezpieczna_nazwa}.png', bbox_inches='tight', dpi=300)
    plt.close(fig_wplyw)