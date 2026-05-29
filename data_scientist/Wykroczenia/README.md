# Analiza i klasyfikacja zdarzeń drogowych
 
Identyfikacja kluczowych czynników infrastrukturalnych wpływających na różne typy wykroczeń.

Zamiast opierać się na podstawowych statystykach, zbudowałam wielowymiarowy pipeline analityczny, który łączy klasyczną ekonometrię z nowoczesnymi algorytmami uczenia maszynowego. Wytrenowane przeze mnie modele (Regresja Logistyczna OvR, MNLogit oraz Lasy Losowe) wyciągają wnioski z danych i klasyfikują typy zdarzeń drogowych - od problemów z dynamiką jazdy po wymuszenia pierwszeństwa i incydenty z udziałem pieszych.

Wszystkie skrypty i dane znajdują się w folderze Wykroczenia.

---

## Struktura logiczna

Mimo że wszystkie pliki znajdują się w jednym miejscu, logicznie dzielą się na cztery grupy:

### 1. Dane wejściowe
Tych plików system potrzebuje, aby w ogóle zacząć pracę:
* `Ostateczna_Baza_Analiza.csv` - Główny zbiór danych o zdarzeniach na skrzyżowaniach.
* `OR_interpretacje.csv` - Słownik z gotowymi, tekstowymi interpretacjami wyników biznesowych.

### 2. Skrypty Python (Logika i Modele)
Te pliki wykonują całą pracę matematyczną i analityczną:
* `01_trenowanie_modeli_i_eksport.py` - **GŁÓWNY SILNIK.** Ten skrypt wykorzystuje wcześniej przygotowane osobne skrypty modeli. Należy go uruchomić jako pierwszy. Trenuje modele: Regresję Logistyczną One-vs-Rest, wielomianowy model MNLogit oraz Lasy Losowe i generuje 5 plików csv (dane wyjściowe).

* `wykresy_1_ovr.py`, `wykresy_2_mnlogit.py`, `wykresy_3_rf.py` - Trzy moduły zawierające wyłącznie definicje wykresów (nie uruchamiać ich samodzielnie).

* `generator_wykresow.py` - **AUTOMAT.** Ten skrypt uruchamiamy jako drugi. Korzysta z trzech powyższych plików, by wygenerować pakiet kilkudziesięciu gotowych obrazków.

### 3. Pliki wyjściowe (Dane dla aplikacji)
Wyniki wyplute przez główny silnik:
* `eksport_ovr_pelny.csv`, `eksport_mnlogit_pelny.csv` - Wpływ cech infrastruktury na ryzyko (wzrosty/spadki).
* `eksport_rf_waznosc.csv` - Ranking siły wpływu poszczególnych cech na klasyfikację.
* `eksport_macierz.csv`, `eksport_raport.csv` - Twarde dowody na skuteczność (ewaluacja) algorytmu.

### 4. Wizualizacje
* `Gotowe_Wykresy/` - Folder, który tworzy się samoczynnie po odpaleniu generatora. Lądują w nim wszystkie wyrenderowane wykresy `.png`.

---

## Instrukcja dla zespołu developerów

Silnik AI generuje łącznie ponad 30 wykresów. **Błędem architektonicznym byłoby wyświetlenie ich wszystkich na jednej stronie.** Dashboard musi być interaktywny i reagować na zapytania użytkownika. 

Proponowana architektura widoków w aplikacji:

### Widok 1:
W tym miejscu ładujemy tylko statyczne wykresy oceniające cały ekosystem skrzyżowania:
* `Gotowe_Wykresy/7_Ranking_Waznosci.png`
* `Gotowe_Wykresy/8_Macierz_Bledow.png` oraz `9_Metryki_Klasyfikacji.png`
* `Gotowe_Wykresy/10_Macierz_Korelacji.png`
* `Gotowe_Wykresy/5_Mapa_Ciepla.png` 
* `Gotowe_Wykresy/4_Kierunek_Przesuniecia.png`

### Widok 2: Szczegóły Zdarzenia (Zakładki)
Zalecam stworzenie 4 zakładek w interfejsie (Piesi, Wymuszenia, Dynamika, Manewry). W zależności od klikniętej zakładki, frontend renderuje dwa wykresy:
* `Gotowe_Wykresy/1_Forest_[KATEGORIA].png`
* `Gotowe_Wykresy/2_Diverging_Bar_[KATEGORIA].png`

### Widok 3: Interaktywna Infrastruktura (Lista rozwijana)
To jest najważniejszy punkt aplikacji. Użytkownik nie może widzieć 20 wykresów na raz.
1. Frontend powinien dynamicznie zaciągać listę 19 cech (np. `sygnalizacja_obecna`, `sciezka_rowerowa` itd.) bezpośrednio z kolumny "Cecha" z pliku `eksport_rf_waznosc.csv`.
2. Kiedy użytkownik wybierze konkretną opcję z listy rozwijanej, strona powinna odszukać w folderze i wyświetlić odpowiednie pliki:
   - `Gotowe_Wykresy/3_Radar_[WYBRANA_CECHA].png`
   - `Gotowe_Wykresy/6_Wplyw_[WYBRANA_CECHA].png`

---

**1. Instalacja środowiska:**
```bash
pip install -r requirements.txt
