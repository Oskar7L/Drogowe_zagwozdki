# Analiza i predykcja zdarzeń drogowych na skrzyżowaniach

### Identyfikacja ryzyka strukturalnego oraz modelowanie intensywności wypadków metodą Negative Binomial

System w pierwszej kolejności dokonuje segmentacji skrzyżowań pod kątem ich fizycznego profilu bezpieczeństwa, a następnie precyzyjnie szacuje, jak poszczególne elementy infrastruktury (oznakowanie, obecność torowisk, geometria jezdni) wpływają na oczekiwaną liczbę wypadków w mieście.

Wszystkie skrypty i dane znajdują się w głównym katalogu roboczym.

---

## Struktura logiczna i modułowa

### 1. Dane wejściowe

Tych plików system potrzebuje do rozpoczęcia pracy i poprawnego przejścia przez potok przetwarzania:

* `DATA.csv` 
* `DATA2.csv` 
* `DATA3.csv`

### 2. Skrypty Python (Logika, Modele i Wizualizacje)

* `main.py` — **GŁÓWNY KONTROLER**. Serce aplikacji i pętla sterująca. Importuje gotowe funkcje z pozostałych czterech modułów i wywołuje je w ściśle określonej sekwencji. Jest to jedyny skrypt, który użytkownik lub system automatyzacji powinien bezpośrednio uruchamiać.
* `data_processing.py` — **MODUŁ ETL**. Odpowiada za wczytanie trzech plików wejściowych, czyszczenie danych, transformacje typów tekstowych na binarne `0/1`, przeliczenie jednostek natężenia ruchu, agregację danych na poziomie unikalnych skrzyżowań oraz usunięcie zmiennych zbędnych w procesie optymalizacji.
* `clustering_model.py` — **MODUŁ SEGMENTACJI**. Odpowiada za uczenie nienadzorowane. Skaluje zmienne, wywołuje algorytm K-Means dla optymalnej liczby klastrów ($k=2$), przypisuje profil ryzyka do każdego obiektu i wypisuje charakterystykę średnich cech w terminalu.
* `regression_model.py` — **SILNIK STATYSTYCZNY**. Obsługuje zaawansowaną matematykę ekonometryczną. Wylicza współczynniki inflacji wariancji (VIF) w celu eliminacji współliniowości cech oraz estymuje parametry finalnego modelu regresji dwumianowej ujemnej (NB), wypluwając pełny raport statystyczny (`Summary`).
* `charts_visual.py` — **MODUŁ RENDERUJĄCY**. Zawiera wyłącznie czyste definicje funkcji rysujących wykresy w Seaborn i Matplotlib. Wszystkie wykresy prognostyczne i diagnostyczne zostały wewnętrznie zabezpieczone przed parametrami dyspersji modelu (takimi jak `alpha` lub `lnalpha`), dzięki czemu nie generują błędów dopasowania macierzy.

---

## Architektura działania

Uruchomienie pliku `main.py` inicjuje automatyczny potok procesowy:

1. **Ekstrakcja danych:** `data_processing` buduje spójną, oczyszczoną tabelę analityczną indeksowaną nazwami skrzyżowań.
2. **Klastrowanie i Profilowanie:** Dane trafiają do `clustering_model`, gdzie algorytm odseparowuje obiekty stabilne od skrzyżowań wysokiego ryzyka.
3. **Weryfikacja Założeń:** Moduł `regression_model` oblicza wskaźniki VIF przed dopuszczeniem cech do modelu.
4. **Estymacja i Predykcja:** Dopasowywany jest model Negative Binomial (NB).
5. **Generowanie Grafiki:** Moduł `charts_visual` renderuje komplet wykresów i wyświetla je użytkownikowi.
