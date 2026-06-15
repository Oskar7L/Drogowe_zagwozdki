## Opis wykresu - wpływ czynnikow na liczbe wypadków

Ten wykres pokazuje o ile procent zmieni się spodziewana liczba wypadków na skrzyżowaniu, jeśli dodamy do niego jeden konkretny znak albo element infrastruktury. Ciemnoniebieskie słupki to czynniki, których model jest pewny (zmienne istotne). Jasnoszare słupki to z kolei zmienne nieistotne.

* Na samym szczycie mamy grupę czynników, które drastycznie zwiększają ryzyko:
rodzaj_jezdni (skok o 40%): Jeśli skrzyżowanie składa się z dwóch zestawów dróg jednokierunkowych oczekiwana liczba wypadków rośnie aż o ponad 40%.

tramwaj (skok o około 35%): Sama fizyczna obecność torowiska i ruch tramwajowy zwiększają ryzyko wypadku o ponad jedną trzecią. Duże pojazdy szynowe przecinające potoki samochodów drastycznie komplikują sytuację na skrzyżowaniu.

stop oraz zakaz_skrętu (wzrost o 20-24%): Obecność znaku STOP podnosi ryzyko o około 24%, a zakazu skrętu o 20%. Model potwierdza regułę: znaki STOP stoją w miejscach problematycznych, a zakazy skrętu tam, gdzie manewry kierowców regularnie doprowadzały do tragedii.

rondo (wzrost o około 8%): Ruch okrężny generuje więcej wypadków. Jest to sprzeczne z wynikiem klastrowania. Rondo jest w skali miejskiej generatorem drobnych, powtarzalnych stłuczek, co matematycznie wyłapuje model, dając współczynnik o 8%. Jednak z punktu widzenia inżynierii ruchu, łączny bilans tych zdarzeń na rondach wciąż pozostaje na tyle niski, że algorytm klastrowania bez wahania odseparował je od najbardziej krytycznych, wielopasmowych punktów zapalnych w mieście i umieścił w bezpieczniejszej grupie.

*Na samym dole, po lewej stronie wykresu, znajduje się główny hamulcowy dla statystyk wypadkowych:

zakaz_wjazdu (spadek o około 11%): Ten znak zmniejsza oczekiwaną liczbę wypadków o ponad jedną dziesiątą. Robiąc z danego wlotu ulicę jednokierunkową, inżynierowie fizycznie odcinają jeden strumień aut, likwidują punkty kolizyjne.

*Zmienne nieistotne:
Zarówno zmienna określająca natężenie ruchu, jak i ta określająca, czy na skrzyżowaniu pojawia się ścieżka rowerowa, zostały uznane jako nieistotne. Jest to sygnał dla analityków, że samo wybudowanie ścieżki rowerowej automatycznie nie zwiększy liczby wypadków drogowych, oraz że natężenie ruchu nie wpływa zasadniczo na ilość wypadków - tylko cechy skrzyżowań i czynniki zewnętrzne.

*W celach optymalizacyjnych, przy tworzeniu finalnej wersji produkcyjnej, deweloperzy mogą całkowicie wyrzucić z kodu zbędne przeliczanie parametrów dla Max_dobowe oraz ścieżka_rowerowa. Ponieważ ich wpływ wynosi zero lub jest nieistotny, usunięcie ich odciąży bazę danych, a sam algorytm NB będzie działał szybciej, skupiając się wyłącznie na pięciu potężnych, niebieskich czynnikach.
