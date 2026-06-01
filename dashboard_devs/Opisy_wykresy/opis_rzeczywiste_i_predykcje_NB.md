## Opis wykresu - rzeczywiste i predykcje

Ten wykres zestawia ze sobą rzeczywistą liczbę wypadków z prognozą modelu.

* Przypadki niedoszacowania:
Taka sytuacja ukazuje się głównie przy skrzyżowaniach Aleje Jerozolimskie / Marszałkowska oraz Aleja Wilanowska / Puławska. Model przeanalizował geometrię tych skrzyżowań i uznał, że powinno być tam bezpieczniej, niż jest w rzeczywistości. Oznacza to, że są zmienne nieuwzględnione w procesie modelowania, które mają zasadniczy wpływ na te skrzyżowania. Mogą to być zmienne takie jak natężenie ruchu pieszych i sygnalizacja strzałkowa (zielone strzałki skrętu).

* Przypadki przeszacowania:

Odwrotną sytuację widzimy na skrzyżowaniach Wawelska / Grójecka oraz Prosta / Towarowa. Model na podstawie danych zmiennych uznał, że te skrzyżowania powinny mieć większą liczbę wypadków niż mają w rzeczywistości. Taki rozjazd to zazwyczaj dowód na sukces inżynierii ruchu drogowego. Oznacza to, że dane skrzyżowanie ma fatalny i niebezpieczny układ bazowy, ale miasto wprowadziło tam rozwiązania poprawiające bezpieczeństwo, których nasz model nie widzi. Mogą to być: unikalne sterowania sygnalizacją, fotoradary w okolicy lub fizyczne, rzadkie zmiany geometrii skrzyżowania (wyspy dla pieszych).

* Kluczowy wniosek z analizy rozjazdów: Te rozbieżności dają systemowi ogromną wartość biznesową. Miejsca, gdzie model niedoszacował ryzyka, to sygnał dla analityków, że są one z jakiegoś powodu problematyczne i należałoby się nad nimi pochylić. Z kolei miejsca przeszacowane wymagają dalszej analizy, by sprawdzić, dlaczego akurat na tych skrzyżowaniach liczba wypadków jest mniejsza i potencjalnie skopiowanie tych rozwiązań na inne skrzyżowania.