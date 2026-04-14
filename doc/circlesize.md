# Struktura danych (z shots.h lub varz.h)

```c
typedef struct {
    // ... inne pola ...

    // Dla pocisków okrężnych (circlesize)
    JE_boolean shotComplicated;   // !=0 gdy circlesize > 0
    JE_integer shotDevX;          // aktualne odchylenie X od środka
    JE_integer shotDevY;          // aktualne odchylenie Y od środka
    JE_byte shotDirX;             // kierunek zmiany odchylenia X (+1 lub -1)
    JE_byte shotDirY;             // kierunek zmiany odchylenia Y (+1 lub -1)
    JE_byte shotCirSizeX;         // promień orbity w osi X (w pikselach)
    JE_byte shotCirSizeY;         // promień orbity w osi Y (w pikselach)

    JE_integer shotX;             // bezwzględna pozycja X pocisku
    JE_integer shotY;             // bezwzględna pozycja Y pocisku

    // ... reszta pól ...
} PlayerShotDataType;
```

## Inicjalizacja (z shots.c – funkcja player_shot_create)

```c
// Inicjalizacja pocisku okrężnego
shot->shotComplicated = weapon->circlesize != 0;

if (weapon->circlesize == 0)
{
    // Normalny pocisk - leci prosto
    shot->shotDevX = 0;
    shot->shotDirX = 0;
    shot->shotDevY = 0;
    shot->shotDirY = 0;
    shot->shotCirSizeX = 0;
    shot->shotCirSizeY = 0;
}
else
{
    JE_byte circsize = weapon->circlesize;

    if (circsize > 19)
    {
        // Kodowanie elipsy: (Y*20 + X)
        // Przykład: 41 = (2*20 + 1) → promień Y=2, promień X=1
        JE_byte circsize_mod20 = circsize % 20;
        shot->shotCirSizeX = circsize_mod20;
        shot->shotDevX = circsize_mod20 >> 1;   // dzielenie całkowite przez 2

        circsize = circsize / 20;
        shot->shotCirSizeY = circsize;
        shot->shotDevY = circsize >> 1;         // dzielenie całkowite przez 2
    }
    else
    {
        // Dla wartości 1-19: okrąg (romb) o jednakowych promieniach
        shot->shotCirSizeX = circsize;
        shot->shotCirSizeY = circsize;
        shot->shotDevX = circsize >> 1;   // np. 5>>1 = 2
        shot->shotDevY = circsize >> 1;   // np. 5>>1 = 2
    }

    // Początkowy kierunek ruchu: w prawo (+1) i w górę (-1)
    // Uwaga: w układzie ekranowym Y rośnie w dół, więc -1 oznacza ruch do góry
    shot->shotDirX = 1;
    shot->shotDirY = -1;
}

// Ustawienie pozycji bezwzględnej (środek orbity + offset początkowy)
shot->shotX = PX + weapon->bx[...];  // środek X
shot->shotY = PY + tmp_by;            // środek Y
// Uwaga: shotX i shotY są później modyfikowane przez shotDevX i shotDevY
```

## Aktualizacja w każdej klatce (z shots.c – funkcja player_shot_move_and_draw)

```c
// To jest wykonywane co klatkę dla każdego aktywnego pocisku
if (shot->shotComplicated != 0)
{
    // === OŚ X ===
    // Zwiększ odchylenie o kierunek
    shot->shotDevX += shot->shotDirX;
    // Dodaj odchylenie do pozycji bezwzględnej
    shot->shotX += shot->shotDevX;

    // Sprawdź czy osiągnięto granicę (wierzchołek rombu)
    if (abs(shot->shotDevX) == shot->shotCirSizeX)
        shot->shotDirX = -shot->shotDirX;  // odwróć kierunek

    // === OŚ Y ===
    // Zwiększ odchylenie o kierunek
    shot->shotDevY += shot->shotDirY;
    // Dodaj odchylenie do pozycji bezwzględnej
    shot->shotY += shot->shotDevY;

    // Sprawdź czy osiągnięto granicę (wierzchołek rombu)
    if (abs(shot->shotDevY) == shot->shotCirSizeY)
        shot->shotDirY = -shot->shotDirY;  // odwróć kierunek
}
```

# Dodatkowe informacje kontekstowe

## 1. Kolejność wykonywania

```
1. Inicjalizacja (raz, przy wystrzeleniu pocisku)
   ↓
2. [PĘTLA GŁÓWNA] co klatkę:
   - Aktualizacja pozycji (powyższy kod)
   - Sprawdzenie kolizji
   - Renderowanie
   ↓
3. Powtarzaj aż do wygaśnięcia (shotAvail[shot_id] == 0)
```

## 2. Związek między zmiennymi

```
Pozycja bezwzględna = środek orbity + aktualne odchylenie

gdzie:
- środek orbity = pozycja w momencie wystrzelenia (stała)
- aktualne odchylenie = shotDevX/Y (zmienia się co klatkę)
```

UWAGA: W kodzie oryginalnym shotX i shotY są jednocześnie środkiem i pozycją bezwzględną, ponieważ do nich dodawane jest shotDevX/Y. To znaczy, że shotX po inicjalizacji zawiera środek, a po pierwszej aktualizacji zawiera już środek + odchylenie.

## 3. Kształt toru (dlaczego to romb, nie okrąg)

```c
// Gdyby to był okrąg, wzór wyglądałby tak:
offset_x = radius * cos(angle)
offset_y = radius * sin(angle)

// Ale w oryginale jest to:
offset_x += direction_x
if (abs(offset_x) == radius) direction_x = -direction_x
```

Różnica: w oryginale offset zmienia się liniowo (o ±1 co klatkę), nie sinusoidalnie. To daje romb (kwadrat obrócony o 45°), a nie okrąg.

## 4. Przykład dla circleSize = 5 (krok po kroku)

```
Klatka | shotDevX | shotDirX | shotX (względem środka)
-----------------------------------------------------
0      | 2        | +1       | 2
1      | 3        | +1       | 3
2      | 4        | +1       | 4
3      | 5        | -1       | 5   ← odbicie (|5| == 5)
4      | 4        | -1       | 4
5      | 3        | -1       | 3
6      | 2        | -1       | 2
7      | 1        | -1       | 1
8      | 0        | -1       | 0
9      | -1       | -1       | -1
10     | -2       | -1       | -2
11     | -3       | -1       | -3
12     | -4       | -1       | -4
13     | -5       | +1       | -5  ← odbicie (|-5| == 5)
14     | -4       | +1       | -4
... i tak dalej
```

## 5. Pełny cykl

Dla promienia R, pełny cykl trwa R × 4 klatek.

- R=5 → 20 klatek
- R=10 → 40 klatek
- R=15 → 60 klatek

## 6. Kodowanie elips (circlesize > 19)

Wartość circlesize jest kodowana jako: (promień_Y × 20) + promień_X

Przykłady:

- 41 = (2×20 + 1) → promień X=1, promień Y=2 (elipsa pionowa)
- 143 = (7×20 + 3) → promień X=3, promień Y=7 (elipsa pozioma)
- 84 = (4×20 + 4) → promień X=4, promień Y=4 (romb, odpowiednik circlesize=4)

