# 1. Struktura sposobu strzelania (Firing Mode / Weapon Pattern)

Ten fragment odpowiada za to, jak pociski są wystrzeliwane w danej chwili.

- `drain` – Zużycie energii (mocy) przy każdym strzale. W Twojej strukturze wynosi 0, co jest typowe dla broni przeciwników lub darmowych trybów.

- `shotRepeat` – Opóźnienie między kolejnymi seriami strzałów (częstotliwość).

- `multi` – Liczba pocisków wystrzeliwanych jednocześnie w jednej serii. Kod gry wykonuje pętlę `for (int tempCount = weapons[temp3].multi; tempCount > 0; tempCount--)`, aby stworzyć odpowiednią liczbę obiektów pocisków.

- `weapAni` – Maksymalna klatka animacji dla grafiki pocisku (używane do animowanych strzałów). W kodzie przypisywane do `enemyShot[b].animax`.

- `max` – Liczba zdefiniowanych punktów (wzorców) w tablicy patterns. Jeśli broń ma multi większe niż 1, gra przechodzi przez kolejne indeksy tej tablicy aż do wartości max.

- `tx`, `ty` – Parametry tekstury lub specjalnego efektu przesunięcia (często używane do centrowania grafiki strzału).

- `aim` – Wartość celowania. Jeśli aim > 0, gra oblicza wektor w stronę gracza, zamiast korzystać ze stałych wartości sx/sy. Wyższa wartość oznacza szybszy pocisk nakierowany na cel.

- `acceleration` / `accelerationx` – Dodatkowe przyspieszenie pocisku w osiach Y i X po wystrzeleniu.

- `sound` – Identyfikator dźwięku odtwarzanego przy wystrzale.

- `shipBlastFilter` – Filtr graficzny nakładany na statek w momencie strzału (np. błysk lufy).


# 2. Podstruktura patterns (Wzorce pojedynczych pocisków)

Definiuje właściwości konkretnego pocisku w serii:

- `attack` – Obrażenia zadawane przez ten konkretny pocisk.

- `del` (delay/duration) – Czas życia pocisku lub opóźnienie przed jego zniknięciem.

- `sx`, `sy` – Początkowa prędkość (pęd) pocisku w osiach X i Y.

- `bx`, `by` – Przesunięcie (offset) punktu startowego pocisku względem środka statku. Pozwala to na strzelanie np. z dwóch skrzydeł jednocześnie (bx ujemne dla lewego, dodatnie dla prawego).

- `sg` (shot graphic) – Identyfikator grafiki (sprite'a) używanego dla tego konkretnego pocisku.


# 3. Struktura samej broni (Weapon Item)

To jest "opakowanie", które trzyma statystyki rynkowe i odnośniki do powyższych trybów:

- `cost` – Cena zakupu broni w sklepie.

- `power_use` – Bazowe zapotrzebowanie na moc generatora.

- `item_graphic` – Ikona broni wyświetlana w menu wyposażenia (hangarze).

- `modes_count` – Liczba dostępnych poziomów ulepszeń (Level 1, Level 2 itd.).

- `firing_modes` – Tablice zawierające indeksy (ID) struktur strzelania. Każdy kolejny poziom ulepszenia broni (Power Level) aktywuje kolejny zestaw indeksów z tablicy mode_1.


# 4. ENEMY AIM LOGIC

- `aim > 0` – sprawdza, czy przeciwnik ma parametr aim (celowanie).

1. Wybierany jest cel (`targetX`, `targetY`).
2. Obliczana jest różnica pozycji celu i przeciwnika (`aimX`, `aimY`).
3. Normalizacja wektora – dzielenie przez `maxMagAim` (największa składowa).
4. Mnożenie przez `aim` – to daje prędkość pocisku w osiach X i Y w kierunku gracza.
5. Wynik zaokrąglany (`roundf`) i zapisywany jako `sxm`, `sym` (prędkość pocisku).

## Podsumowanie

Logika aim to proste celowanie w gracza – pocisk leci w kierunku pozycji gracza z prędkością zależną od wartości aim (im wyższa, tym szybszy i celniejszy lot).