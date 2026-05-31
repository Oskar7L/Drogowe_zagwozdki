## Opis wykresu - macierz korelacji
Wykres przedstawia korelację liniową pomiędzy poszczególnymi zmiennymi opisującymi skrzyżowania,a liczbą wypadków.

* Najsilniejszą dodatnią korelację na liczbę wypadków wykazała zmienna stop, czyli ilość znaków stop na skrzyżowaniu (0.53) oraz zmienna zakaz_skrętu (0.32). Sugeruje to, że skrzyżowania wymagające bardziej skomplikowanej organizacji ruchu lub wymuszające zatrzymanie są statystycznie bardziej wypadkowe.

* Najsilniejszą ujemną korelację na zmienną zależną wykazała zmienna rodzaj_jezdni. Jest to zmienna jakościowa opisująca rodzaje drogi na skrzyżowaniu. Przyjmuje 1 dla skrzyżowań niejednolitych, czyli takich, w których spotykają się różne rodzaje dróg, oraz 0 dla jednolitych. W przypadku naszych skrzyżowań oznacza to 1 dla spotkania drogi jednojezdniowej dwukierunkowej i dwóch jednokierunkowych oraz 0 dla spotkania dwóch jezdni jednokierunkowych. Korelacja tej zmiennej na poziomie -0.18 oznacza, że skrzyżowania o niejednolitej geometrii charakteryzują się statystycznie mniejszą liczbą wypadków niż skrzyżowania jednolite. Innymi słowy: wraz ze wzrostem wartości tej zmiennej (czyli przejściem z układu jednolitego na niejednolity), liczba wypadków ma tendencję do spadku.

Choć zależność ta jest stosunkowo słaba (współczynnik wynosi -0.18), to kierunek tego wpływu może wydawać się na pierwszy rzut oka zaskakujący (intuicyjnie spodziewalibyśmy się, że bardziej skomplikowane, niejednolite skrzyżowania będą bardziej niebezpieczne).

Można to zinterpretować na dwa sposoby:

Większa ostrożność kierowców: Skrzyżowania niejednolite (gdzie zmienia się przekrój drogi) mogą wymuszać na kierowcach intuicyjne zdjęcie nogi z gazu i podwyższoną czujność ze względu na nietypowy układ geometrii.

Charakterystyka skrzyżowań jednolitych (0): Skrzyżowania o układzie "dwóch jezdni jednokierunkowych" to często duże, wielopasmowe arterie miejskie. Mimo że ich geometria jest jednolita, to wysokie prędkości rozwijane na takich drogach oraz duża liczba punktów kolizyjnych (np. przy przeplataniu potoków ruchu) mogą generować znacznie więcej zdarzeń drogowych.

* Współliniowość cech: Widoczna jest silna korelacja między zmienną znakami zakaz_wjazdu oraz zakaz_skrętu (0.45). Jednak mimo tego korelacja nie osiągnęła poziomu usunięcia zmiennej z modelu.

