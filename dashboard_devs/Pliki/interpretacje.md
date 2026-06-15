## Sekcja 1: Ogólne podsumowanie

W tej sekcji interpretujemy zachowanie modeli, ogólne zależności w ruchu drogowym oraz jakość predykcji. Należy pamiętać, że modele wskazują na asocjacje i wzorce w danych, które nie zawsze muszą oznaczać bezpośredni związek przyczynowo-skutkowy.

### Ważność permutacyjna cech w modelu Lasów Losowych

![Ważność permutacyjna cech - Lasy Losowe](Gotowe_Wykresy/7_Ranking_Waznosci.png)

Wykres przedstawia ważność permutacyjną cech w modelu Lasów Losowych, wskazując, jak silnie algorytm opierał swoje predykcje na poszczególnych zmiennych podczas klasyfikacji zdarzeń. Najsilniejszym predyktorem ułatwiającym modelowi podział danych okazała się trudna nawierzchnia, zaraz za którą uplasowała się zła widoczność oraz obecne oświetlenie w nocy. Wskazuje to, że stan nawierzchni oraz warunki widoczności dostarczały modelowi najbardziej użytecznych informacji pozwalających rozróżniać analizowane klasy zdarzeń. Spośród oznakowania, model najwyżej ocenił przydatność liczby znaków nakazu jazdy po prawej stronie. Należy jednocześnie zauważyć, że cechy znajdujące się w dolnej części wykresu, przyjmujące wartości ujemne (takie jak liczba znaków STOP, torowisk tramwajowych czy zakazów skrętu i zawracania), z perspektywy tego konkretnego algorytmu mogły wprowadzać szum informacyjny. Ich obecność nie pomagała w klasyfikacji, a ich ewentualne wyłączenie ze zbioru testowego mogłoby wręcz minimalnie zwiększyć ogólną skuteczność predykcji.

---

### Ewaluacja Klasyfikatora (Macierz Błędów w %)

![Macierz Błędów](Gotowe_Wykresy/8_Macierz_Bledow.png)

Wykres przedstawia znormalizowaną macierz błędów klasyfikatora, obrazującą procentowy rozkład decyzji modelu względem rzeczywistych kategorii zdarzeń. Najwyższą skuteczność klasyfikacji uzyskano dla kategorii manewry i naruszenia przepisów, dla której poprawnie sklasyfikowano 62,6% przypadków. Niewiele niższą trafność osiągnięto dla kategorii zdarzenia z udziałem pieszych i rowerzystów (59,1%) oraz wymuszenia pierwszeństwa (pojazdy) (55,7%). Analiza macierzy wskazuje na wyraźne trudności modelu w rozróżnianiu kategorii wymuszenia pierwszeństwa (pojazdy) oraz zdarzenia z udziałem pieszych i rowerzystów. 27,3% rzeczywistych zdarzeń z udziałem pieszych i rowerzystów zostało błędnie zaklasyfikowanych do kategorii wymuszeń pierwszeństwa, natomiast 18,9% rzeczywistych wymuszeń pierwszeństwa przypisano do kategorii zdarzeń z pieszymi. Wyniki wskazują, że model ma wyraźne trudności z poprawną identyfikacją zdarzeń związanych z dynamiką ruchu i odległością (skuteczność zaledwie 13,5%), które system najczęściej błędnie interpretuje jako ogólne manewry (36,8%).

---

### Osiągi Modelu: Precyzja i Czułość

![Precyzja i Czułość](Gotowe_Wykresy/9_Metryki_Klasyfikacji.png)

Wykres prezentuje zestawienie metryk precyzji oraz czułości, ułatwiając dogłębną ocenę zdolności decyzyjnych klasyfikatora dla poszczególnych kategorii zdarzeń. Model wykazuje najwyższą precyzję (powyżej 0,70) oraz satysfakcjonującą czułość (powyżej 0,6) dla kategorii manewry i przepisy, co jest typowym rezultatem dla klasy dominującej liczebnie, oferującej najbogatszy zbiór wzorców treningowych. Kategorią o najbardziej zrównoważonych i stabilnych parametrach jest kategoria wymuszenie pierwszeństwa (pojazdy), gdzie obie metryki oscylują na zbliżonym poziomie (powyżej 0,55). Analiza potwierdza poważne trudności algorytmu w identyfikacji zdarzeń z grupy dynamika i odległość, dla której odnotowano najniższą czułość (poniżej 0,15) przy precyzji rzędu 0,25. Niezwykle interesujący, skrajnie asymetryczny rozkład metryk zaobserwowano dla kategorii zdarzenia z pieszymi i rowerzystami. Bardzo niska precyzja (w okolicach 0,10) połączona ze stosunkowo wysoką czułością (blisko 0,60) jest zjawiskiem charakterystycznym dla nielicznych klas mniejszościowych. Oznacza to, że model w toku uczenia przyjął strategię asekuracyjną - z powodzeniem wykrywa znaczną część rzeczywistych zagrożeń dla pieszych, jednak osiąga to kosztem wysokiego odsetka tzw. fałszywych alarmów, błędnie kwalifikując do tej grupy inne sytuacje drogowe.

---

### Korelacja czynników infrastrukturalnych i pogodowych z typem wykroczenia

![Macierz Korelacji](Gotowe_Wykresy/10_Macierz_Korelacji.png)

Wykres przedstawia siłę liniowych powiązań między infrastrukturą i pogodą a typami zdarzeń. Współczynniki są relatywnie niskie (od -0,28 do +0,28), co uzasadnia użycie w projekcie zaawansowanych algorytmów nieliniowych. Widać jednak kilka wyraźnych asocjacji. Zwiększona liczba rond dodatnio koreluje (0,28) z błędami w manewrowaniu, ale ujemnie (-0,28) z wymuszeniami, co sugeruje, że takie skrzyżowania uspokajają ruch, ale prowokują drobniejsze pomyłki. Z kolei wyższa liczba znaków STOP wiąże się ze wzrostem wymuszeń (0,24). Obecność ścieżki rowerowej koreluje ujemnie z wymuszeniami (-0,24), a dodatnio z manewrami (0,17). Zmienne oświetleniowe i pogodowe mają tu korelację bliską zeru - ich rzeczywisty wpływ wychwytują dopiero modele nieliniowe.

---

### Mapa Ciepła Asocjacji (Log-Odds)

![Mapa Ciepła Asocjacji](Gotowe_Wykresy/5_Mapa_Ciepla.png)

Wykres prezentuje mapę ciepła obrazującą, jak dany element infrastruktury lub warunki pogodowe zmieniają szanse wystąpienia konkretnego wypadku w porównaniu do kategorii referencyjnej, czyli kategorii manewry i naruszenia przepisów. Największy wpływ wykazuje awaria sygnalizacji świetlnej - w takiej sytuacji szansa na wymuszenie pierwszeństwa jest aż 11-krotnie wyższa (log-odds = 2,4; OR = 11,0) niż na zwykłe błędy w manewrowaniu. Z kolei przy złej widoczności szansa na incydenty z udziałem pieszych i rowerzystów staje się trzykrotnie wyższa (log-odds = 1,1; OR = 3,0). Niezwykle ciekawe wnioski płyną z analizy sprawnie działającej sygnalizacji: jej obecność sprawia, że szansa na klasyczne wymuszenie drastycznie spada (log-odds = -1,3; OR = 0,27), ale jednocześnie dwukrotnie wyższa (log-odds = 0,7; OR = 2,0) staje się szansa na zdarzenia związane z dynamiką i odległością. Podobnie podwyższoną szansę na wymuszenia (log-odds = 0,6; OR = 1,8) generuje każdy kolejny znak STOP na analizowanym skrzyżowania. Natomiast wyznaczenie ścieżki rowerowej sprawia, że szansa na wymuszenia (log-odds = -1,6; OR = 0,20) oraz zdarzenia z pieszymi (log-odds = -0,9; OR = 0,4) jest znacznie niższa, przez co profil ryzyka takiego skrzyżowania przesuwa się niemal całkowicie w stronę ogólnych błędów w manewrowaniu.

---

### Kierunek przesunięcia ryzyka (względem Manewrów)

![Kierunek Przesunięcia Ryzyka](Gotowe_Wykresy/4_Kierunek_Przesuniecia.png)

Wykres prezentuje piętnaście najsilniejszych efektów z modelu wielomianowego, porządkując je według kierunku wpływu na profil zdarzeń względem kategorii referencyjnej (manewry i naruszenia przepisów). Wartości dodatnie (prawa strona osi) oznaczają relatywny wzrost szansy na dany typ wypadku. W tej grupie bezwzględnie dominuje awaria sygnalizacji świetlnej, silnie zwiększając względne szanse wystąpienia wymuszeń względem kategorii referencyjnej. Silny wektor wzrostu szans generuje również zła widoczność (incydenty z pieszymi) oraz każdy kolejny znak STOP (wymuszenia). Z kolei wartości ujemne (lewa strona osi) oznaczają spadek szansy na konkretne zdarzenie. W tym obszarze wyróżnia się wyznaczona ścieżka rowerowa oraz sprawnie działająca sygnalizacja, które najmocniej redukują ryzyko klasycznych wymuszeń. Obecność tych elementów infrastruktury skutecznie tłumi specyficzne zagrożenia, sprawiając, że profil wypadkowy skrzyżowania powraca do błędów w ogólnym manewrowaniu.

---

## Sekcja 2: Szczegółowa analiza czynników ryzyka (Ilorazy Szans)

W poniższej sekcji wykorzystano wyniki regresji logistycznej One-vs-Rest. Do wizualizacji ilorazów szans (Odds Ratios) oraz ich przedziałów ufności zastosowano wykresy typu Forest Plot. Prezentują one wyizolowany wpływ poszczególnych cech na szansę wystąpienia konkretnego typu wypadku. Oś pionowa (OR = 1) stanowi granicę braku wpływu - wartości po prawej stronie oznaczają wzrost szansy na dane zdarzenie, natomiast po lewej jej spadek. Kluczowym kryterium analitycznym jest istotność statystyczna (p-value < 0.05). Poniższe wnioski uwzględniają wyłącznie te zmienne, których wpływ został bezsprzecznie potwierdzony statystycznie.

### Iloraz Szans - Wymuszenia pierwszeństwa

![Forest Plot Wymuszenia](Gotowe_Wykresy/1_Forest_Wymuszenia.png)

Analiza jednoznacznie wskazuje na kluczową rolę infrastruktury kierującej ruchem.

**Czynniki silnie zwiększające szansę na zdarzenie:**
* **Awaria sygnalizacji:** Wystąpienie awarii świateł sprawia, że szansa na wymuszenie jest aż 7,83 razy większa.
* **Znak STOP:** Każdy dodatkowy znak STOP na skrzyżowaniu podbija szansę na to wykroczenie o 82,9%.
* **Znaki przejścia dla pieszych oraz prędkość:** Każdy znak przejścia podnosi ryzyko o 7,7%, a wzrost limitu prędkości o 1 km/h zwiększa je o 3,1%.

**Czynniki istotnie zmniejszające szansę na zdarzenie:**
* **Dedykowana infrastruktura:** Wyznaczona ścieżka rowerowa (spadek szansy o 78,8%) oraz działająca sygnalizacja świetlna (spadek o 74,4%) najskuteczniej chronią przed klasycznymi wymuszeniami.
* **Ograniczenia kierunków jazdy:** Każdy znak ostrzegający o tramwajach (-21,8%), nakaz jazdy po prawej stronie (-18,9%), zakaz skrętu/zawracania (-17,7%) oraz znak ronda (-16,5%) systematycznie wymuszają ostrożność, obniżając ryzyko błędnej oceny pierwszeństwa.
* **Lokalizacja:** Każdy kilometr oddalenia od ścisłego centrum miasta redukuje szansę na wymuszenie o 14,4%.

---

### Iloraz Szans - Dynamika i odległość

![Forest Plot Dynamika](Gotowe_Wykresy/1_Forest_Dynamika.png)

W przypadku zdarzeń związanych z fizyką jazdy (np. najechania na tył, gwałtowne hamowania), profil ryzyka drastycznie różni się od wymuszeń.

**Czynniki silnie zwiększające szansę na zdarzenie:**
* **Sygnalizacja i infrastruktura rowerowa:** Działające światła zwiększają szansę na ten typ zdarzenia 2,69 razy (np. hamowanie przed zmianą cyklu), a obecność ścieżki rowerowej 2,38 razy.
* **Trudna nawierzchnia:** Złe warunki drogowe (mokro, ślisko) podbijają ryzyko błędów z odległością 1,54 razy.
* **Poczucie pierwszeństwa i prędkość:** Każdy znak "masz pierwszeństwo" (wzrost o 11,0%) oraz wyższy limit prędkości (wzrost o 2,6% na każdy 1 km/h) sprzyjają nadmiernej dynamice jazdy.

**Czynniki istotnie zmniejszające szansę na zdarzenie:**
* **Dobra widoczność i spowolnienie:** Podróż w nocy przy dobrym oświetleniu obniża ryzyko o 34,4%. Ponadto, każda infrastruktura wymuszająca uwagę obniża ryzyko błędów dynamiki: znaki tramwajowe (-30,9%), zakazy skrętu (-17,4%), znaki STOP (-10,4%) oraz ronda (-5,0%).

---

### Iloraz Szans - Manewry i naruszenia przepisów

![Forest Plot Manewry](Gotowe_Wykresy/1_Forest_Manewry.png)

Wykres dowodzi, że ogólne błędy w manewrowaniu (zmiana pasa, nieprawidłowe skręcanie) najczęściej współwystępują z nagromadzeniem bodźców i skomplikowaną infrastrukturą drogową.

**Czynniki silnie zwiększające szansę na zdarzenie:**
* **Złożoność skrzyżowania:** Ścieżka rowerowa (szansa wyższa 2,61 razy), każdy znak o tramwajach (+63,5%) oraz działająca sygnalizacja (+44,4%) wyraźnie sprzyjają pomyłkom manewrowym.
* **Restrykcje i geometria:** Zakazy skrętu (+36,6%), ronda (+17,4%) oraz zakazy wjazdu (+13,9%) potęgują ryzyko błędnego ustawienia się na drodze.
* **Lokalizacja:** Każdy kilometr oddalenia od centrum zwiększa szansę na ten typ błędów o 20,9%.

**Czynniki istotnie zmniejszające szansę na zdarzenie:**
* **Sytuacje pełnego skupienia:** Awaria sygnalizacji drastycznie (o 80,9%) redukuje swobodne, błędne manewry - kierowcy koncentrują się na bezkolizyjnym opuszczeniu skrzyżowania.
* **Infrastruktura zatrzymująca:** Każdy znak STOP (spadek o 32,2%), wyższa prędkość przelotowa (-5,2% na 1 km/h) oraz gorsza pogoda (zła widoczność redukuje błędy manewrowe o 24,1%) zniechęcają do ryzykownych zachowań.

---

### Iloraz Szans - Zdarzenia z pieszymi

![Forest Plot Piesi](Gotowe_Wykresy/1_Forest_Piesi.png)

Kategoria zdarzeń z udziałem niechronionych uczestników ruchu okazuje się niezwykle wrażliwa na jakość widoczności oraz prędkość najazdową, a mniej na samą sygnalizację (której wpływ okazał się nieistotny statystycznie).

**Czynniki silnie zwiększające szansę na zdarzenie:**
* **Warunki środowiskowe:** Zła widoczność (mgła, oślepiające słońce) sprawia, że szansa na potrącenie pieszego jest aż 2,90 razy większa.
* **Oznakowanie i prędkość:** Każdy dodatkowy znak przejścia na skrzyżowaniu (co w naturalny sposób zwiększa ekspozycję pieszych) podbija szansę na zdarzenie o 15,6%. Każdy dodatkowy 1 km/h limitu prędkości zwiększa to ryzyko o 8,0%.

**Czynniki istotnie zmniejszające szansę na zdarzenie:**
* **Elementy spowalniające ruch:** Trudna nawierzchnia zmusza kierowców do ostrożności, redukując szansę na potrącenie o 57,6%. Podobnie działają znaki o tramwajach (-50,9%), zakazy skrętu (-43,2%) oraz ronda (-18,6%).
* **Lokalizacja:** Im dalej od ścisłego centrum miasta (gdzie natężenie ruchu pieszego jest mniejsze), tym szansa na takie zdarzenie systematycznie spada (o 19,7% z każdym kilometrem).

---

## Sekcja 3: Co najbardziej zwiększa, a co zmniejsza ryzyko?

Poniższe wykresy pokazują 10 najważniejszych cech (np. elementów drogi czy pogody), które najsilniej wpływają na dany typ zdarzenia.
* **Czerwone słupki (po prawej)** - to cechy, które **zwiększają** ryzyko. Im dłuższy słupek, tym większe niebezpieczeństwo.
* **Zielone słupki (po lewej)** - to cechy, które **zmniejszają** ryzyko (działają ochronnie).

### Najważniejsze czynniki - Wymuszenia pierwszeństwa

![Diverging Bar Wymuszenia](Gotowe_Wykresy/2_Diverging_Bar_Wymuszenia.png)

* **Czynniki zmniejszające ryzyko (zielone):** Wydzielona ścieżka rowerowa oraz działająca sygnalizacja świetlna najskuteczniej chronią przed wymuszeniami. Pozytywny wpływ mają również elementy wymuszające ostrożność, takie jak tory tramwajowe czy znaki zakazujące skrętu lub zawracania, a także trudna nawierzchnia jezdni.
* **Czynniki zwiększające ryzyko (czerwone):** Awaria sygnalizacji świetlnej drastycznie zwiększa ryzyko wymuszenia pierwszeństwa. Kolejnym istotnym problemem jest nagromadzenie znaków STOP, które zazwyczaj instalowane są na skrzyżowaniach o utrudnionej widoczności lub skomplikowanej geometrii.

---

### Najważniejsze czynniki - Dynamika i odległość

![Diverging Bar Dynamika](Gotowe_Wykresy/2_Diverging_Bar_Dynamika.png)

* **Czynniki zmniejszające ryzyko (zielone):** Awaria sygnalizacji świetlnej skutecznie redukuje tego typu kolizje, ponieważ zmusza kierowców do znacznego obniżenia prędkości i ostrożnego wjazdu na skrzyżowanie. Ryzyko spada również w nocy przy dobrym oświetleniu oraz w miejscach wymagających naturalnego spowolnienia, takich jak przejazdy tramwajowe.
* **Czynniki zwiększające ryzyko (czerwone):** Działająca sygnalizacja świetlna oraz obecność ścieżek rowerowych wyraźnie zwiększają ryzyko kolizji, ponieważ często wymuszają na kierowcach nagłe hamowanie (np. przy zmianie cyklu świateł). Istotnym zagrożeniem jest również trudna nawierzchnia (np. mokra), która wydłuża drogę hamowania.

---

### Najważniejsze czynniki - Błędy w manewrowaniu 

![Diverging Bar Manewry](Gotowe_Wykresy/2_Diverging_Bar_Manewry.png)

* **Czynniki zmniejszające ryzyko (zielone):** Sytuacje wymagające podwyższonego skupienia, takie jak awaria świateł, zła widoczność, opady czy znaki STOP, sprawiają, że kierowcy jeżdżą ostrożniej i rzadziej popełniają nieostrożne błędy manewrowe.
* **Czynniki zwiększające ryzyko (czerwone):** Złożona infrastruktura skrzyżowania. Obecność ścieżek rowerowych, torów tramwajowych, sygnalizacji i zakazów skrętu stwarza środowisko pełne bodźców. W takim otoczeniu kierowcy częściej ulegają dezorientacji i podejmują błędne decyzje podczas zmiany pasa czy wyboru kierunku jazdy.

---

### Najważniejsze czynniki - Zdarzenia z pieszymi

![Diverging Bar Piesi](Gotowe_Wykresy/2_Diverging_Bar_Piesi.png)

* **Czynniki zmniejszające ryzyko (zielone):** Elementy infrastruktury wymuszające wolniejszą jazdę, takie jak trudna nawierzchnia, ronda, tory tramwajowe czy zakazy skrętu, dają kierowcom więcej czasu na reakcję, co znacząco chroni pieszych.
* **Czynniki zwiększające ryzyko (czerwone):** Zła widoczność jest głównym czynnikiem prowadzącym do potrąceń. Ryzyko rośnie również przy opadach deszczu lub śniegu, a także przy działającej sygnalizacji, która niekiedy daje uczestnikom ruchu fałszywe poczucie bezpieczeństwa.

---

## Sekcja 4: Profile Ryzyka (Wykresy Radarowe)

Wykresy radarowe (pajęczynowe) pozwalają na błyskawiczną ocenę "kształtu" zagrożenia, jakie generuje dana cecha infrastruktury lub pogody. Oś o wartości 1.0 (zaznaczona przerywaną linią) stanowi granicę neutralności. Jeśli wykres mocno wychodzi poza to koło w danym kierunku, oznacza to relatywny wzrost szansy na ten typ wypadku. Jeśli kurczy się do środka - oznacza to efekt ochronny. Poniżej zaprezentowano 8 najbardziej asymetrycznych i kluczowych dla inżynierii ruchu profili.

### 1. Awaria sygnalizacji świetlnej

![Radar Awaria Sygnalizacji](Gotowe_Wykresy/3_Radar_sygnalizacja_awaria.png)

Wykres przypomina ostrą strzałkę skierowaną w górę. Wizualizuje on sytuację skrajną - awaria świateł całkowicie marginalizuje błędy z zakresu dynamiki czy ogólnego manewrowania (wykres kurczy się do środka w tych kierunkach), a całe ryzyko niemal ośmiokrotnie wystrzeliwuje w stronę klasycznych wymuszeń pierwszeństwa.

---

### 2. Działająca sygnalizacja świetlna

![Radar Działająca Sygnalizacja](Gotowe_Wykresy/3_Radar_sygnalizacja_obecna.png)

Wykres jest silnie rozciągnięty w dół osi - w stronę błędów związanych z Dynamiką. Sygnalizacja świetnie eliminuje klasyczne wymuszenia (wciągając górną część profilu mocno do środka), ale w zamian przenosi ciężar zdarzeń na inne zagrożenia. Światła prowokują częstsze najechania na tył pojazdów (np. w wyniku gwałtownego hamowania przed zmianą cyklu) oraz zauważalnie zwiększają szansę na pomyłki w ogólnym manewrowaniu w obrębie skrzyżowania.

---

### 3. Dedykowana ścieżka rowerowa

![Radar Ścieżka Rowerowa](Gotowe_Wykresy/3_Radar_sciezka_rowerowa.png)

Wykres jest rozciągnięty w lewą stronę oraz w dół. Obecność wyznaczonej infrastruktury rowerowej bardzo skutecznie odciąga kierowców od wymuszania pierwszeństwa na autach, jednak nagromadzenie bodźców generuje nowe zagrożenia. Drastycznie potęguje ryzyko popełnienia błędów w ogólnym manewrowaniu (np. zła zmiana pasa w obrębie skomplikowanego węzła), a ze względu na konieczność ciągłego ustępowania i przyspieszania, silnie podbija również ryzyko kolizji związanych z zaburzoną dynamiką jazdy.

---

### 4. Znak STOP

![Radar Znak STOP](Gotowe_Wykresy/3_Radar_stop_lz.png)

Wykres w kształcie "latawca" wyciągniętego w górę. Pokazuje on, że każdy kolejny znak STOP na węźle drogowym paradoksalnie podbija ryzyko wymuszenia pierwszeństwa. Zjawisko to sugeruje, że znaki te są akumulowane w miejscach z natury trudnej geometrii lub bardzo słabej widoczności, gdzie kierowcy i tak regularnie popełniają błędy w ocenie sytuacji.

---

### 5. Zła widoczność

![Radar Zła Widoczność](Gotowe_Wykresy/3_Radar_pogoda_zla_widocznosc.png)

Profil skrajnie asymetryczny, wystrzeliwujący ostro w prawą stronę. To dowód na to, jak ogromny wpływ ma percepcja kierowcy na relacje z niechronionymi uczestnikami ruchu. Podczas mgły czy oślepiającego słońca spadają szanse na błędy ogólne (kierowcy jadą ostrożniej), jednak szansa na potrącenie pieszego szybuje w górę niemal trzykrotnie.

---

### 6. Trudna nawierzchnia

![Radar Trudna Nawierzchnia](Gotowe_Wykresy/3_Radar_nawierzchnia_trudna.png)

Wykres wyraźnie "ciągnie" w dół osi (w stronę Dynamiki), jednocześnie silnie kurcząc się po prawej stronie (Piesi). Doskonale obrazuje to fizykę jazdy: mokry, zaśnieżony lub śliski asfalt weryfikuje błędy związane z utrzymaniem bezpiecznej odległości i wydłużoną drogą hamowania. Jednocześnie wymusza na kierowcach ostrożność i na tyle duże spowolnienie, że ryzyko potrącenia pieszego zauważalnie spada.

---

### 7. Liczba torowisk tramwajowych

![Radar Torowiska](Gotowe_Wykresy/3_Radar_tramwaje_lz.png)

Profil zauważalnie rozciągnięty w lewą stronę osi (Manewry). To świetny analityczny dowód na to, jak przeplatanie się ruchu kołowego z szynowym dezorientuje kierowców. Obecność tramwajów i specyficznego dla nich oznakowania w obrębie skrzyżowania prowokuje częstsze błędy przy zmianie pasa lub skręcaniu, choć - podobnie jak trudna nawierzchnia, redukuje ryzyko innych zdarzeń.

---

### 8. Rondo

![Radar Rondo](Gotowe_Wykresy/3_Radar_rondo_lz.png)

Ten wykres charakteryzuje się najbardziej symetrycznym, wyrównanym kształtem ze wszystkich analizowanych cech. Nie widać tu drastycznych "strzał" ani ekstremalnych, jednostronnych odchyleń - profil łagodnie oscyluje wokół granicy neutralności, lekko poszerzając się jedynie na osi Manewrów - skrzyżowanie o ruchu okrężnym harmonijnie uspokaja i porządkuje ruch. Równomiernie redukuje groźne incydenty i wymusza jedynie niewielki kompromis w postaci drobnych, niegroźnych pomyłek przy zjazdach z wyspy.

---

## Sekcja 5: Relatywny wpływ cech na profil zdarzeń

Ostatnia grupa wizualizacji prezentuje wpływ poszczególnych cech na profil wypadkowy skrzyżowania w ujęciu relatywnym. Kategorią referencyjną (bazową) są tu ogólne błędy w manewrowaniu i naruszenia przepisów. Słupki czerwone (wartości dodatnie) oznaczają, że dana cecha zwiększa szansę na specyficzny wypadek względem błędu manewrowego. Słupki zielone (wartości ujemne) oznaczają sytuację odwrotną - cecha tłumi dane zagrożenie, przez co profil skrzyżowania przesuwa się w stronę zwykłych, najczęściej niegroźnych pomyłek manewrowych. Do poniższego zestawienia wyselekcjonowano 8 najciekawszych cech.

### 1. Odległość od centrum

![Wpływ Odległość od centrum](Gotowe_Wykresy/6_Wplyw_odległosc_od_centrum%20[km].png)

Wykres ten prezentuje zależność geograficzną - wszystkie słupki są skierowane w dół (kolor zielony). Oznacza to, że z każdym kolejnym kilometrem oddalania się od ścisłego centrum miasta, ryzyko potrąceń pieszych, wymuszeń i błędów dynamiki systematycznie spada na rzecz zwykłych błędów manewrowych. Jest to bezpośrednie odzwierciedlenie faktu, że na przedmieściach ruch pieszy i rowerowy jest mniejszy, a infrastruktura skrzyżowań często ulega uproszczeniu, co naturalnie redukuje najpoważniejsze konflikty krzyżowe.

---

### 2. Ograniczenie prędkości

![Wpływ Ograniczenie prędkości](Gotowe_Wykresy/6_Wplyw_ograniczenie_predkosci.png)

Na wykresie wszystkie słupki są dodatnie (czerwone). Analityka bezwzględnie potwierdza tu prawa fizyki: każdy dodatkowy 1 km/h w limicie prędkości na skrzyżowaniu systematycznie przesuwa profil zdarzeń ze zwykłych, drobnych błędów manewrowych, zamieniając je w groźne w skutkach potrącenia pieszych (najwyższy słupek), problemy z wyhamowaniem (Dynamika) oraz błędną ocenę luki w ruchu (Wymuszenia).

---

### 3. Skrzyżowanie o ruchu okrężnym

![Wpływ Rondo](Gotowe_Wykresy/6_Wplyw_rondo_lz.png)

Obecność ronda generuje wyłącznie ujemne (zielone) logity dla wszystkich analizowanych kategorii. Wymuszenie fizycznego spowolnienia pojazdów przed rondem sprawia, że szansa na groźne wymuszenia, potrącenia czy najechania drastycznie spada. Rondo nie eliminuje wypadków całkowicie, ale skutecznie zamienia je w najmniej groźną kategorię referencyjną - czyli drobne pomyłki przy manewrowaniu.

---

### 4. Liczba torowisk tramwajowych

![Wpływ Torowiska](Gotowe_Wykresy/6_Wplyw_tramwaje_lz.png)

Na wykresie widać jedynie wartości ujemne, z gigantycznym spadkiem ryzyka dla zdarzeń z pieszymi. Konieczność przecięcia torowiska wymusza na kierowcach drastyczne obniżenie prędkości i wzmożoną ostrożność. W efekcie skrzyżowania z infrastrukturą szynową są miejscami powolnymi, gdzie brakuje przestrzeni na błędy fizyki jazdy (Dynamika) czy klasyczne wymuszenia, a większość zdarzeń ogranicza się do pomyłek manewrowych w skomplikowanym układzie linii i znaków.

---

### 5. Zła widoczność

![Wpływ Zła widoczność](Gotowe_Wykresy/6_Wplyw_pogoda_zla_widocznosc.png)

Ten wykres to doskonały przykład wysoce specyficznego czynnika ryzyka. Choć zła widoczność nie wykazuje istotnego statystycznie, wyizolowanego wpływu na wymuszenia czy dynamikę (brak słupków), to generuje gigantyczny, ponadprzeciętny wzrost (wysoki czerwony słupek) ryzyka dla niechronionych uczestników ruchu. Stanowi to twardy dowód na to, że ograniczenia percepcyjne (mgła, oślepiające słońce) uderzają niemal wyłącznie w bezpieczeństwo pieszych i rowerzystów.

---

### 6. Awaria sygnalizacji świetlnej

![Wpływ Awaria sygnalizacji](Gotowe_Wykresy/6_Wplyw_sygnalizacja_awaria.png)

Wysoki, czerwony słupek dla kategorii "Wymuszenia" udowadnia, że awaria świateł całkowicie dominuje profil zdarzeń, przenosząc środek ciężkości ze zwykłych manewrów na wymuszenia pierwszeństwa. Brak kierowania ruchem w miejscu do tego przystosowanym to główny czynnik najpoważniejszych zderzeń związanych z wymuszeniem pierwszeństwa.

---

### 7. Ścieżka rowerowa

![Wpływ Ścieżka rowerowa](Gotowe_Wykresy/6_Wplyw_sciezka_rowerowa.png)

Wykres dla infrastruktury rowerowej wykazuje silnie ujemne (zielone) słupki dla wymuszeń pierwszeństwa i zdarzeń z pieszymi. Oznacza to, że obecność dedykowanej przestrzeni rowerowej porządkuje ruch, skutecznie tłumiąc najgroźniejsze wypadki. W zamian za to, ze względu na dużą ilość bodźców, profil całego węzła przesuwa się w stronę naszej kategorii bazowej - czyli częstszych pomyłek przy manewrowaniu i zmianie pasa.

---

### 8. Trudna nawierzchnia

![Wpływ Trudna nawierzchnia](Gotowe_Wykresy/6_Wplyw_nawierzchnia_trudna.png)

Ten wykres doskonale obrazuje, jak warunki fizyczne różnicują ryzyko. Z jednej strony widzimy zielony słupek dla pieszych - trudna nawierzchnia (np. śnieg, lód) sprawia, że kierowcy jadą wolniej i uważniej, co zmniejsza ryzyko potrąceń w stosunku do manewrów. Z drugiej strony, pojawia się wyraźny czerwony słupek dla "Dynamiki". Śliska jezdnia bezlitośnie weryfikuje wydłużoną drogę hamowania, potęgując liczbę najechań na tył i problemów z utrzymaniem dystansu.