# Dokumentacja Systemu Eventów i Spawnu Przeciwników

Zweryfikowano na podstawie kodu źródłowego `tyrian2.c` (OpenTyrian).

---

## Spis treści

1. [Format Binarny Eventu](#1-format-binarny-eventu)
2. [Typy Eventów — Przegląd](#2-typy-eventów--przegląd)
3. [Eventy Spawnu — Szczegóły](#3-eventy-spawnu--szczegóły)
   - [Sloty i offsety wrogów](#31-sloty-i-offsety-wrogów)
   - [Obliczenie pozycji X](#32-obliczenie-pozycji-x)
   - [Obliczenie pozycji Y](#33-obliczenie-pozycji-y)
   - [Inicjalizacja prędkości i pozostałych pól](#34-inicjalizacja-prędkości-i-pozostałych-pól)
   - [Tabela wszystkich typów spawnu](#35-tabela-wszystkich-typów-spawnu)
4. [Eventy Globalne — Modyfikacja Wrogów](#4-eventy-globalne--modyfikacja-wrogów)
5. [Eventy Środowiskowe i Sterujące](#5-eventy-środowiskowe-i-sterujące)
6. [Hierarchia Ruchu w Każdej Klatce](#6-hierarchia-ruchu-w-każdej-klatce)
7. [Mechanika `fixedmovey` — Stały Ruch Niezależny](#7-mechanika-fixedmovey--stały-ruch-niezależny)
8. [System `linknum` — Grupowanie Wrogów](#8-system-linknum--grupowanie-wrogów)
9. [Ograniczenia Odbicia — Bounce Params](#9-ograniczenia-odbicia--bounce-params)
10. [Sloty i Prędkości Scrollingu](#10-sloty-i-prędkości-scrollingu)
11. [Wartości Specjalne Pól](#11-wartości-specjalne-pól)
12. [Przykłady Konfiguracji](#12-przykłady-konfiguracji)
13. [Symulacja Matematyczna — Oś Y](#13-symulacja-matematyczna--oś-y)

---

## 1. Format Binarny Eventu

Każdy event w pliku `.lvl` zajmuje **11 bajtów** w formacie little-endian:

```python
event = struct.unpack('<H B h h b b b B', event_data)

# Mapowanie pól:
eventtime  = event[0]  # H — uint16  czas/pozycja mapy, przy której event się odpala
eventtype  = event[1]  # B — uint8   numer typu eventu
eventdat   = event[2]  # h — int16   pole danych 1
eventdat2  = event[3]  # h — int16   pole danych 2
eventdat3  = event[4]  # b — int8    pole danych 3
eventdat5  = event[5]  # b — int8    pole danych 5  ← uwaga: kolejność w pliku
eventdat6  = event[6]  # b — int8    pole danych 6
eventdat4  = event[7]  # B — uint8   pole danych 4  ← ostatnie w pliku
```

> **Ważne:** Pola `eventdat5` i `eventdat6` występują w pliku **przed** `eventdat4`.
> Kolejność w pliku: `dat`, `dat2`, `dat3`, `dat5`, `dat6`, `dat4`.

### Zasada przeciążania pól

Znaczenie pól `eventdat1`–`eventdat6` zmienia się całkowicie w zależności od `eventtype`. Dla eventów spawnu (typy 6, 7, 10, 15, 17, 18, 23, 32, 56) obowiązuje wspólny schemat opisany w sekcji 3.

---

## 2. Typy Eventów — Przegląd

### Eventy Spawnu Wrogów

| Type | Nazwa | Slot (enemyOffset) | Opis |
|------|-------|-------------------|------|
| 6  | Ground Enemy       | 25  | Wróg naziemny, spawnuje od góry |
| 7  | Top Enemy          | 50  | Wróg z tła trzeciego planu, od góry |
| 10 | Ground Enemy 2     | 75  | Drugi slot naziemny, od góry |
| 15 | Sky Enemy          | 0   | Wróg powietrzny, od góry |
| 17 | Ground Bottom      | 25  | Wróg naziemny, od dołu ekranu |
| 18 | Sky Enemy Bottom   | 0   | Wróg powietrzny, od dołu ekranu |
| 23 | Sky Enemy Bottom 2 | 50  | Wróg z tła trzeciego planu, od dołu |
| 32 | Special Top        | 50  | Jak typ 7, ale stała pozycja Y=190 |
| 56 | Ground2 Bottom     | 75  | Drugi slot naziemny, od dołu |
| 12 | 4×4 Ground Enemy   | varies | Tworzy 4 wrogów w kwadracie 2×2 |
| 49–52 | Custom Enemy   | varies | Wróg z inline-grafika z eventu |

### Eventy Globalne (modyfikacja żyjących wrogów)

| Type | Nazwa | Efekt |
|------|-------|-------|
| 19 | Global Move        | Nadpisuje prędkość (`exc`, `eyc`) i `fixedmovey` grupy |
| 20 | Global Accel       | Zmienia silnik wahadłowy (`excc`, `eycc`) grupy |
| 24 | Global Animate     | Zmienia animację grupy |
| 25 | Global Damage      | Ustawia `armorleft` grupy |
| 27 | Global AccelRev    | Zmienia limity prędkości (`exrev`, `eyrev`) i filtr koloru |
| 31 | Fire Override      | Zmienia częstotliwość strzelania grupy |
| 33 | Enemy From Enemy   | Przypisuje typ `enemydie` dla grupy |
| 39 | Linknum Change     | Przenosi wrogów między grupami |
| 47 | Armor Set          | Bezpośrednio ustawia `armorleft` grupy |
| 55 | Accel Override     | Zmienia `xaccel`/`yaccel` (losowe przyspieszenie) grupy |
| 60 | Assign Special     | Oznacza wroga jako "specjalny" (flagi globalne) |
| 74 | Bounce Params      | Ustawia granice odbicia (`xminbounce` itd.) grupy |

### Eventy Środowiskowe i Sterujące

| Type | Efekt |
|------|-------|
| 1  | Prędkość gwiazd w tle |
| 2  | Ustaw prędkość scrollingu (`backMove`, `backMove2`, `backMove3`) |
| 3  | Zwolnij scrolling (tryb opóźniony) |
| 4  | Zatrzymaj tła |
| 5  | Załaduj banki sprite'ów wrogów (do 4 banków) |
| 8  | Wyłącz pole gwiazd |
| 9  | Włącz pole gwiazd |
| 11 | Zakończ poziom |
| 13 | Dezaktywuj random-spawn wrogów |
| 14 | Aktywuj random-spawn wrogów |
| 16 | Wyświetl tekst w oknie |
| 21 | Tło 3 nad wrogami (tryb 1) |
| 22 | Tło 3 pod wrogami (tryb 0) |
| 26 | `smallEnemyAdjust` — przesuń małe wrogi o (-10, -7) |
| 28 | TopEnemy pod tłem |
| 29 | TopEnemy nad tłem |
| 30 | Ustaw prędkość scrollingu (wariant bez `explodeMove`) |
| 34 | Zacznij fade muzyki |
| 35 | Zmień utwór muzyczny |
| 36 | Ustaw `readyToEndLevel` |
| 37 | Ustaw częstotliwość random-spawnu (`levelEnemyFrequency`) |
| 38 | Skocz do czasu eventu (goto) |
| 40 | Włącz `enemyContinualDamage` |
| 41 | Usuń wszystkich wrogów ze slotu (0=wszystkie, 1=slot 0–24) |
| 42 | Tło 3 nad wrogami (tryb 2) |
| 43 | Ustaw `background2over` |
| 44 | Ustaw filtr koloru / jasność |
| 46 | Zmień poziom trudności i `damageRate` |
| 48 | Tło 2 nieprzezroczyste |
| 53 | `forceEvents` (kontynuuj eventy gdy scrolling=0) |
| 54 | Skocz do eventu (jump/return) |
| 57 | Ustaw `superEnemy254Jump` |
| 61 | Skocz jeśli flaga globalna ma daną wartość |
| 62 | Odtwórz efekt dźwiękowy |
| 63 | Pomiń eventy jeśli NIE tryb 2-graczy |
| 64 | Ustaw smoothie (efekt graficzny) |
| 65 | Przełącz `background3x1` |
| 66 | Pomiń eventy jeśli trudność ≤ wartości |
| 67 | Ustaw timer poziomu |
| 68 | Losowe eksplozje tła |
| 69 | Ustaw czas nietykalności gracza |
| 70 | Skocz jeśli wrogowie grupy nie istnieją |
| 71 | Skocz jeśli mapa dotarła do pozycji |
| 72 | `background3x1b` |
| 73 | `skyEnemyOverAll` |
| 74 | Ustaw parametry odbicia dla grupy |
| 75 | Wybierz losowego wroga ze statyczną `eyc==0` z zakresu grup |
| 76 | `returnActive = true` |
| 77 | Ustaw pozycję mapy Y |
| 78 | Zwiększ `galagaShotFreq` |
| 79 | Ustaw boss bar (link_num) |
| 80 | Pomiń eventy jeśli tryb 2-graczy |
| 81 | Ustaw zakres zawijania tła 2 (`BKwrap2`) |
| 82 | Daj graczowi specjalną broń |

---

## 3. Eventy Spawnu — Szczegóły

### Pola eventu spawnu (typy 6, 7, 10, 15, 17, 18, 23, 32, 56)

| Pole      | Nazwa robocza  | Typ   | Opis |
|-----------|---------------|-------|------|
| eventdat  | `enemy_id`    | int16 | ID przeciwnika w bazie danych (`enemyDat`) |
| eventdat2 | `x`           | int16 | Pozycja X spawnu; `-99` = nie modyfikuj X |
| eventdat3 | `y_vel`       | int8  | Modyfikator prędkości pionowej; `-99` = nie modyfikuj |
| eventdat4 | `link_num`    | uint8 | Numer grupy/formacji (`linknum`) |
| eventdat5 | `y_offset`    | int8  | Korekta pozycji startowej Y |
| eventdat6 | `fixed_move_y`| int8  | Stały ruch pionowy niezależny od fizyki |

---

### 3.1. Sloty i offsety wrogów

Silnik trzyma 100 wrogów w jednej tablicy, podzielonej na 4 sloty po 25:

| Slot | `enemyOffset` | Typ wrogów | Tła używane do scrollingu |
|------|--------------|------------|--------------------------|
| 0    | 0            | Sky (powietrzni, tło 1) | `backMove2` |
| 1    | 25           | Ground (naziemni, tło 1) | `backMove` |
| 2    | 50           | Top (tło 3) | `backMove3` |
| 3    | 75           | Ground 2 (naziemni, tło 1) | `backMove` |

Silnik szuka pierwszego wolnego slotu w zakresie `[enemyOffset, enemyOffset+25)`. Jeśli żaden nie jest wolny — event jest ignorowany.

---

### 3.2. Obliczenie pozycji X

Pozycja X jest obliczana **tylko gdy `eventdat2 != -99`**. Gdy `eventdat2 == -99`, pozycja X pochodzi wyłącznie z danych wroga (`startx` ± `startxc`).

```c
// Kod źródłowy JE_createNewEventEnemy:

switch (enemyOffset)
{
case 0:   // Sky
    enemy.ex = eventdat2 - (mapX - 1) * 24;
    break;

case 25:  // Ground
case 75:  // Ground 2
    enemy.ex = eventdat2 - (mapX - 1) * 24 - 12;
    break;

case 50:  // Top
    if (background3x1)
        enemy.ex = eventdat2 - (mapX - 1) * 24 - 12;
    else
        enemy.ex = eventdat2 - mapX3 * 24 - 24 * 2 + 6;

    if (background3x1b)
        enemy.ex -= 6;   // dodatkowa korekta
    break;
}
```

**Uproszczone wzory:**

| Slot | Wzór na `ex` (gdy `background3x1 = false`) |
|------|--------------------------------------------|
| Sky (0) | `eventdat2 - (mapX - 1) × 24` |
| Ground (25, 75) | `eventdat2 - (mapX - 1) × 24 - 12` |
| Top (50), tło niezłożone | `eventdat2 - mapX3 × 24 - 42` |
| Top (50), `background3x1 = true` | `eventdat2 - (mapX - 1) × 24 - 12` |
| Top (50), `background3x1b = true` | jak wyżej `-6` |

Gdzie `mapX` i `mapX3` to przesunięcia kolumn tła odczytane z nagłówka pliku `.lvl`.

**Efektywny zakres `eventdat2`:** Wartości 0–320 odpowiadają szerokości ekranu. Ujemne i powyżej 320 powodują spawn poza ekranem (dozwolone).

---

### 3.3. Obliczenie pozycji Y

Inicjalizacja Y przebiega w kilku etapach, w zależności od trybu spawnu:

#### A) Spawn od góry (typy 6, 7, 10, 15)

Wykonywany gdy `eventdat2 != -99`:

```c
// Etap 1: Bazowa pozycja — zawsze -28
enemy.ey = -28;

// Wyjątek: typ 7 (Top) z background3x1b=true
if (background3x1b && enemyOffset == 50)
    enemy.ey += 4;   // → ey = -24

// Etap 2: Odejmij prędkość scrollingu (wróg "wchodzi" z górnej krawędzi)
switch (enemyOffset) {
    case 0:       enemy.ey -= backMove2;   break;  // Sky
    case 25, 75:  enemy.ey -= backMove;    break;  // Ground
    case 50:      enemy.ey -= backMove3;   break;  // Top
}

// Etap 3 (opcjonalny): smallEnemyAdjust — tylko małe wrogie (esize==0)
if (smallEnemyAdjust && enemy.size == 0)
    enemy.ey -= 7;

// Etap 4: Dodaj y_offset z eventu
enemy.ey += eventdat5;
```

**Wzór końcowy (typowy przypadek, bez wyjątków):**

| Slot | Startowa pozycja Y |
|------|--------------------|
| Sky (0) | `-28 - backMove2 + eventdat5` |
| Ground (25, 75) | `-28 - backMove + eventdat5` |
| Top (50) | `-28 - backMove3 + eventdat5` |

Domyślne wartości `backMove`: `backMove=1`, `backMove2=2`, `backMove3=3`, więc przy `eventdat5=0`:
- Sky: `ey = -30`
- Ground: `ey = -29`
- Top: `ey = -31`

#### B) Spawn od dołu (typy 17, 18, 23, 32, 56)

```c
// Typ 17 (Ground Bottom) i 18 (Sky Bottom):
enemy.ey = 190 + eventdat5;

// Typ 23 (Sky Bottom 2, Top slot):
enemy.ey = 180 + eventdat5;

// Typ 32 (Special Top) i 56 (Ground2 Bottom):
enemy.ey = 190;   // eventdat5 IGNOROWANE
```

> Wrogowie od dołu NIE mają odjętego `backMove` — wchodzą z dokładnej pozycji Y.

#### C) Gdy `eventdat2 == -99`

Pozycja Y pochodzi wyłącznie z danych wroga (`starty` ± `startyc`), obliczona w `JE_makeEnemy`. Żadna z powyższych korekt nie jest stosowana, **z wyjątkiem**:
```c
enemy.ey += eventdat5;   // y_offset jest dodawany zawsze
enemy.eyc += eventdat3;  // y_vel jest dodawany zawsze
```

---

### 3.4. Inicjalizacja prędkości i pozostałych pól

Po ustaleniu pozycji, w `JE_createNewEventEnemy` wykonywane są (zawsze, niezależnie od `-99`):

```c
enemy.ey        += eventdat5;   // y_offset — dodaj do finalnej pozycji Y
enemy.eyc       += eventdat3;   // y_vel — dodaj do prędkości pionowej z danych wroga
enemy.linknum    = eventdat4;   // link_num — przypisz grupę
enemy.fixedmovey = eventdat6;   // fixed_move_y — ustaw stały ruch
```

**`y_vel` (eventdat3):** Wartość dodawana do `eyc` już zainicjalizowanego przez `ymove` z danych wroga:
```
eyc_finalne = ymove + y_vel
```
Gdy `eventdat3 == -99`: pole jest mimo to dodawane jako `-99`, co psuje prędkość — należy ustawiać `eventdat3 = 0` gdy nie chcemy modyfikować prędkości, a nie `-99`. Wartość `-99` jako „ignoruj" dotyczy tylko pola `x` (`eventdat2`).

---

### 3.5. Tabela wszystkich typów spawnu

| Type | Slot | `ey` bazowe | `ey -= backMove?` | `y_offset` stosowany? | Uwagi |
|------|------|-------------|-------------------|-----------------------|-------|
| 6  | 25 | -28 | `backMove` | tak | Standard ground |
| 7  | 50 | -28 (-24 gdy `bg3x1b`) | `backMove3` | tak | Top enemy |
| 10 | 75 | -28 | `backMove` | tak | Ground slot 2 |
| 15 | 0  | -28 | `backMove2` | tak | Sky enemy |
| 17 | 25 | `190 + y_offset` | nie | tak (w sumie) | Ground od dołu |
| 18 | 0  | `190 + y_offset` | nie | tak (w sumie) | Sky od dołu |
| 23 | 50 | `180 + y_offset` | nie | tak (w sumie) | Top od dołu |
| 32 | 50 | 190 (stałe) | nie | **nie** | Special top |
| 56 | 75 | 190 (stałe) | nie | **nie** | Ground2 od dołu |
| 12 | varies | -28 | `backMove` | tak | 4 wrogie, eventdat6=slot |
| 49–52 | varies | -28 | tak | tak | Custom inline grafika |

---

## 4. Eventy Globalne — Modyfikacja Wrogów

### Event 19 — Global Move

Nadpisuje prędkość i stały ruch grupy wrogów.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `exc` | Nowa prędkość X; `-99` = nie zmieniaj |
| eventdat2 | `eyc` | Nowa prędkość Y; `-99` = nie zmieniaj |
| eventdat3 | selector | Wybór zakresu wrogów (patrz niżej) |
| eventdat4 | `linknum` | Filtr grupy (gdy `eventdat3 == 0`) |
| eventdat5 | `enemycycle` | Gdy `> 0`: ustaw klatkę animacji |
| eventdat6 | `fixedmovey` | Nowy stały ruch Y; `0` = nie zmieniaj; `-99` = resetuj do 0 |

**Selektor zakresu (`eventdat3`):**

| Wartość | Zakres wrogów | Filtr linknum |
|---------|--------------|---------------|
| 0 | 0–99 (wszyscy) | tak (wg `eventdat4`) |
| 1 | 25–49 (Ground slot) | nie (wszyscy w zakresie) |
| 2 | 0–24 (Sky slot) | nie |
| 3 | 50–74 (Top slot) | nie |
| 99 | 0–99 (wszyscy) | nie |
| 80–89 | 0–99 | tak (wg `newPL[eventdat3-80]`) |

### Mechanika działania

**1. Zmiana prędkości:**
```c
if (eventdat != -99)
    enemy.exc = eventdat;  // prędkość X

if (eventdat2 != -99)
    enemy.eyc = eventdat2; // prędkość Y
```

**2. Zmiana stałego ruchu (`fixedmovey`):**
```c
if (eventdat6 == -99)
    enemy.fixedmovey = 0;      // reset
else if (eventdat6 != 0)
    enemy.fixedmovey = eventdat6; // ustaw nową wartość
// wartość 0 pozostawia fixedmovey bez zmian
```

**3. Filtrowanie wrogów:**
```c
for (temp = 0; temp < 100; temp++)
{
    // Sprawdzenie zakresu
    bool in_range = false;
    switch (eventdat3) {
        case 0: in_range = true; break;  // wszyscy
        case 1: in_range = (temp >= 25 && temp < 50); break; // Ground
        case 2: in_range = (temp < 25); break;  // Sky
        case 3: in_range = (temp >= 50 && temp < 75); break; // Top
        case 99: in_range = true; break; // wszyscy
        case 80-89: in_range = true; break; // wszyscy z newPL
    }

    // Sprawdzenie linknum (jeśli wymagane)
    if (in_range) {
        if (eventdat3 == 0 || eventdat3 >= 80) {
            if (eventdat4 == 0 || enemy[temp].linknum == eventdat4) {
                // zastosuj zmiany
            }
        } else {
            // zastosuj zmiany (bez filtra linknum)
        }
    }
}
```

### Wpływ na ruch

Event 19 bezpośrednio nadpisuje prędkość wrogów i ustawia stały ruch:

```c
// W każdej klatce:
enemy.ey += enemy.fixedmovey;  // stały ruch
enemy.ey += enemy.eyc;         // prędkość fizyczna
enemy.ey += tempBackMove;      // scrolling
```

Wartości typowe dla `exc`:
- `exc = 0`: wróg nie porusza się w poziomie
- `exc = -2`: wróg porusza się w lewo
- `exc = 2`: wróg porusza się w prawo

Wartości typowe dla `eyc`:
- `eyc = 0`: wróg nie porusza się w pionie (przez prędkość fizyczną)
- `eyc = -1`: wróg porusza się w górę
- `eyc = 1`: wróg porusza się w dół
- `eyc = 6`: szybki ruch w dół (jak w Twoim JSON)

Wartości typowe dla `fixedmovey`:
- `fixedmovey = 0`: brak stałego ruchu
- `fixedmovey = -1`: stały dryf w górę
- `fixedmovey = 1`: stały dryf w dół

### Animacja (eventdat5)

```c
if (eventdat5 > 0)
    enemy.enemycycle = eventdat5;  // ustaw klatkę animacji
```

### Typowe zastosowania

**1. Zatrzymanie wrogów w poziomie:**
```json
{
  "event_type": 19,
  "new_exc": 0,
  "new_eyc": 6,
  "link_num": 7
}
```
Wrogowie z `link_num=7` nie będą się poruszać w poziomie (`exc=0`), ale będą szybko poruszać się w dół (`eyc=6`).

**2. Stały dryf w górę:**
```json
{
  "event_type": 19,
  "new_exc": 0,
  "new_eyc": 0,
  "new_fixedmovey": -1,
  "link_num": 8
}
```
Wrogowie z `link_num=8` będą stale dryfować w górę (`fixedmovey=-1`), niezależnie od prędkości fizycznej.

**3. Reset stałego ruchu:**
```json
{
  "event_type": 19,
  "new_exc": 0,
  "new_eyc": 0,
  "new_fixedmovey": -99,
  "link_num": 9
}
```
Zatrzymuje stały ruch dla wrogów z `link_num=9` (reset `fixedmovey` do 0).

**4. Zmiana prędkości dla całego slotu:**
```json
{
  "event_type": 19,
  "new_exc": 0,
  "new_eyc": 6,
  "scope_selector": 1
}
```
Zmienia prędkość dla wszystkich wrogów w Ground slot (25-49), bez filtra linknum.

### Ograniczenia

- **Wartość -99:** Oznacza "nie zmieniaj" dla `exc` i `eyc`, "reset do 0" dla `fixedmovey`
- **Wartość 0 dla fixedmovey:** Pozostawia `fixedmovey` bez zmian (nie resetuje!)
- **Selektor vs linknum:** Gdy `eventdat3 != 0` i `eventdat3 < 80`, linknum jest ignorowany
- **Nadpisanie:** Event 19 nadpisuje prędkość, nie dodaje do niej

---

### Event 20 — Global Accel

Zmienia silnik wahadłowy (przyspieszenie stałe) grupy wrogów. Przy zmianie `excc` silnik **resetuje całkowicie** stan wahadła.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `excc` | Nowe stałe przyspieszenie X; `-99` = nie zmieniaj |
| eventdat2 | `eycc` | Nowe stałe przyspieszenie Y; `-99` = nie zmieniaj |
| eventdat3 | selector | Selektor zakresu / filtru (jak w event 19) |
| eventdat4 | `linknum` | Filtr grupy (lub `0` = wszyscy) |
| eventdat5 | `animin`/`enemycycle` | Gdy `eventdat6 > 0`: nowe `animin`; gdy `eventdat6 == 0` i `> 0`: ustaw `enemycycle` |
| eventdat6 | `ani` | Gdy `> 0`: nowe `ani`, aktywuj animację (resetuje `animax=0, aniactive=1`) |

### Mechanika działania

**1. Zmiana silnika wahadłowego X (pełny reset):**
```c
if (eventdat != -99)
{
    enemy.excc    = eventdat;      // stałe przyspieszenie
    enemy.exccw   = abs(eventdat); // aktualna wartość wahadła
    enemy.exccwmax = abs(eventdat); // maksimum wahadła
    enemy.exccadd = (eventdat > 0) ? 1 : -1; // kierunek zmiany
}
```

**2. Zmiana silnika wahadłowego Y (bez resetu):**
```c
if (eventdat2 != -99)
{
    enemy.eycc = eventdat2;  // tylko zmienia stałe przyspieszenie
    // stan wahadła (eyccw, eyccwmax, eyccadd) pozostaje bez zmian
}
```

**3. Filtrowanie wrogów:**
```c
for (temp = 0; temp < 100; temp++)
{
    if (eventdat4 == 0 || enemy[temp].linknum == eventdat4)
    {
        // zastosuj zmiany
    }
}
```

### Wpływ na ruch

Silnik wahadłowy (`excc`, `eycc`) dodaje stałe przyspieszenie do prędkości w każdej klatce:

```c
// W każdej klatce:
enemy.exccw += enemy.exccadd;
if (abs(enemy.exccw) > enemy.exccwmax)
    enemy.exccadd = -enemy.exccadd;

enemy.exc += enemy.exccw;  // dodaj wahadło do prędkości X
enemy.eyc += enemy.eycc;  // dodaj stałe przyspieszenie Y
```

Wartości typowe:
- `excc = 0`: brak wahadła X
- `excc = 1`: wolne wahadło poziome
- `excc = 3`: szybkie wahadło poziome
- `eycc = 0`: brak przyspieszenia Y
- `eycc = -1`: stały dryf w górę

### Animacja (eventdat5, eventdat6)

**Gdy `eventdat6 > 0`:**
```c
enemy.animin = eventdat5;  // nowa klatka startowa
enemy.ani = eventdat6;     // nowa ostatnia klatka
enemy.animax = 0;          // reset limitu
enemy.aniactive = 1;       // aktywuj animację
```

**Gdy `eventdat6 == 0` i `eventdat5 > 0`:**
```c
enemy.enemycycle = eventdat5;  // ustaw klatkę animacji
```

### Typowe zastosowania

**1. Wahadło poziome dla formacji:**
```json
{
  "event_type": 20,
  "new_excc": 1,
  "new_eycc": 0,
  "link_num": 2
}
```
Wrogowie z `link_num=2` będą się poruszać wahadłowo w poziomie.

**2. Stały dryf w górę:**
```json
{
  "event_type": 20,
  "new_excc": 0,
  "new_eycc": -1,
  "link_num": 5
}
```
Wrogowie z `link_num=5` będą stale dryfować w górę.

**3. Reset wahadła:**
```json
{
  "event_type": 20,
  "new_excc": 0,
  "new_eycc": 0,
  "link_num": 10
}
```
Zatrzymuje wahadło dla wrogów z `link_num=10` (pełny reset stanu).

### Ograniczenia

- **Reset tylko dla X:** Zmiana `excc` resetuje stan wahadła, zmiana `eycc` nie
- **Wartość -99:** Oznacza "nie zmieniaj" - pozwala modyfikować tylko jedną oś
- **Linknum 0:** Dotyczy wszystkich wrogów (nie tylko grupy)

---

### Event 27 — Global AccelRev

Zmienia limity prędkości wahadła oraz filtr koloru.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `exrev` | Nowy limit X; `-99` = nie zmieniaj |
| eventdat2 | `eyrev` | Nowy limit Y; `-99` = nie zmieniaj |
| eventdat3 | selector/filtr | Gdy `1–16`: ustaw `filter` (kolor); gdy `80–89`: selektor grupy; `0` = ignoruj |
| eventdat4 | `linknum` | Filtr grupy (lub `0` = wszyscy) |

### Mechanika działania

**1. Zmiana limitów prędkości:**
```c
if (eventdat != -99)
    enemy.exrev = eventdat;  // limit X

if (eventdat2 != -99)
    enemy.eyrev = eventdat2; // limit Y
```

**2. Filtrowanie koloru (gdy eventdat3 = 1–16):**
```c
if (eventdat3 >= 1 && eventdat3 <= 16)
    enemy.filter = eventdat3;  // filtr koloru
```

**3. Selektor grupy (gdy eventdat3 = 80–89):**
```c
// Działa jak eventdat4, ale z tablicy newPL
if (eventdat3 >= 80 && eventdat3 <= 89)
    // używa newPL[eventdat3-80] jako linknum
```

**4. Filtrowanie wrogów:**
```c
for (temp = 0; temp < 100; temp++)
{
    if (eventdat4 == 0 || enemy[temp].linknum == eventdat4)
    {
        // zastosuj zmiany
    }
}
```

### Wpływ na ruch

Limity prędkości (`exrev`, `eyrev`) ograniczają maksymalną prędkość wrogów:

```c
// W każdej klatce:
enemy.exc += enemy.xmove + enemy.exccw;  // prędkość X
enemy.eyc += enemy.ymove + enemy.eyccw;  // prędkość Y

// Ograniczenie prędkości
if (enemy.exc > enemy.exrev)
    enemy.exc = enemy.exrev;
if (enemy.exc < -enemy.exrev)
    enemy.exc = -enemy.exrev;
```

Wartości typowe:
- `exrev = 0`: wróg nie porusza się w poziomie
- `exrev = 8`: limit prędkości X na ±8
- `exrev = 20`: szybki wróg (limit ±20)
- `eyrev = 0`: wróg nie porusza się w pionie
- `eyrev = 10`: limit prędkości Y na ±10

### Filtr koloru

Filtr koloru (`filter`) zmienia kolor wroga:
- Wartości 1–16: różne filtry kolorów
- Wartość 0: brak filtra
- Używane do oznaczenia grupy wrogów lub zmiany wyglądu

### Typowe zastosowania

**1. Limit prędkości dla formacji:**
```json
{
  "event_type": 27,
  "new_exrev": 8,
  "new_eyrev": 0,
  "link_num": 2
}
```
Wrogowie z `link_num=2` będą mieć ograniczoną prędkość X na ±8.

**2. Zatrzymanie wrogów w pionie:**
```json
{
  "event_type": 27,
  "new_exrev": 0,
  "new_eyrev": 10,
  "link_num": 5
}
```
Wrogowie z `link_num=5` nie będą się poruszać w poziomie, tylko w pionie.

**3. Zmiana koloru grupy:**
```json
{
  "event_type": 27,
  "filter": 5,
  "link_num": 10
}
```
Wrogowie z `link_num=10` będą mieć filtr koloru 5.

**4. Połączenie z Event 20 (wahadło + limit):**
```json
// Event 20: ustaw wahadło
{
  "event_type": 20,
  "new_excc": 1,
  "link_num": 2
}

// Event 27: ustaw limit prędkości
{
  "event_type": 27,
  "new_exrev": 8,
  "link_num": 2
}
```
Wrogowie z `link_num=2` będą się poruszać wahadłowo, ale nie przekroczą prędkości ±8.

### Ograniczenia

- **Wartość -99:** Oznacza "nie zmieniaj" - pozwala modyfikować tylko jedną oś
- **Linknum 0:** Dotyczy wszystkich wrogów (nie tylko grupy)
- **Filtr vs selektor:** `eventdat3` ma dwa znaczenia (kolor lub selektor grupy) zależnie od wartości
- **Brak resetu:** Zmiana limitów nie resetuje stanu wahadła

---

### Event 31 — Fire Override

Nadpisuje parametry strzelania grupy.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `freq[0]` | Nowa częstotliwość dla broni dół |
| eventdat2 | `freq[1]` | Nowa częstotliwość dla broni prawo |
| eventdat3 | `freq[2]` | Nowa częstotliwość dla broni lewo |
| eventdat4 | `linknum` | Filtr grupy; `99` = wszyscy |
| eventdat5 | `launchfreq` | Nowa częstotliwość launch (jeśli wróg ma `launchtype > 0`) |

Po zmianie wszystkie `eshotwait` są resetowane do 1 (natychmiastowy strzał).

---

### Event 74 — Bounce Params

Ustawia granice odbicia dla grupy.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `xmaxbounce` | Prawa granica X; `-99` = nie zmieniaj |
| eventdat2 | `ymaxbounce` | Dolna granica Y; `-99` = nie zmieniaj |
| eventdat4 | `linknum`    | Filtr grupy; `0` = wszyscy |
| eventdat5 | `xminbounce` | Lewa granica X; `-99` = nie zmieniaj |
| eventdat6 | `yminbounce` | Górna granica Y; `-99` = nie zmieniaj |

> Domyślne granice przy spawnie to `±10000` (praktycznie nieosiągalne).

---

### Event 33 — Enemy From Enemy

Ustawia "hook" który aktywuje się przy śmierci wroga z danej grupy. **Nie spawnował wroga natychmiast** - tylko modyfikuje pole `enemydie`.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `enemydie` | ID wroga do spawnowania przy śmierci |
| eventdat4 | `linknum`  | Filtr grupy (wszyscy wrogowie z tym linknum otrzymają enemydie) |

### Mechanika działania

**1. Gdy event się odpala:**
```c
for (temp = 0; temp < 100; temp++)
{
    if (enemy[temp].linknum == eventdat4)
        enemy[temp].enemydie = eventdat;  // ustaw hook
}
```
Event przegląda wszystkich wrogów z `linknum == eventdat4` i ustawia ich pole `enemydie` na `eventdat`.

**2. Gdy wróg z ustawionym `enemydie > 0` umiera:**
```c
if ((enemy[temp2].enemydie > 0) && ...)
{
    tempW = enemy[temp2].enemydie;  // ID nowego wroga
    int enemy_offset = temp2 - (temp2 % 25);  // slot zmarłego wroga
    if (enemyDat[tempW].value > 30000)
        enemy_offset = 0;  // power-upy zawsze do slotu 0

    b = JE_newEnemy(enemy_offset, tempW, 0);  // spawn nowego wroga
    if (b != 0)
    {
        enemy[b-1].ex = enemy[temp2].ex;  // pozycja X zmarłego
        enemy[b-1].ey = enemy[temp2].ey;  // pozycja Y zmarłego
    }
}
```

### Właściwości nowego wroga

- **Pozycja:** Taka sama jak pozycja zmarłego wroga (`ex`, `ey`)
- **Slot:** Ten sam slot co zmarły wróg (chyba że to power-up z `value > 30000`)
- **linknum:** Zawsze `0` (nie przekazywany od rodzica!)
- **enemydie:** Pochodzi z danych wroga (`enemyDat[enemy_id].eenemydie`), nie z eventu

### Specjalne przypadki

**Power-upy (enemy_id z `value > 30000`):**
- Zawsze spawnowane do slotu 0 (Sky)
- Oznaczone jako `scoreitem = true`

**Enemy ID 533 (w trybie non-superTyrian):**
- Jeśli gracz ma 11 żyć lub losowo (15% szansy), zamieniany na losowy special weapon (ID 829-834)

**Enemy ID 534:**
- W trybie SuperArcade zamieniany na 827
- W trybie SuperTyrian zamieniany na 828 + losowy special

**Event 45 (arcade-only):**
- Podobny do Event 33, ale działa tylko w trybie 2-graczy lub onePlayerAction

### Typowe zastosowania

**1. Boss który rozsypuje się na mniejsze wrogie:**
```
# Spawn bossa z linknum = 10
eventtype = 15, link_num = 10, enemy_id = 200

# Ustaw hook - przy śmierci bossa spawn enemy_id = 201
eventtype = 33, eventdat = 201, eventdat4 = 10
```

**2. Wróg który wypuszcza power-up:**
```
# Wróg z linknum = 5
eventtype = 15, link_num = 5, enemy_id = 100

# Przy śmierci spawn power-up (enemy_id z value > 30000)
eventtype = 33, eventdat = 533, eventdat4 = 5
```

**3. Łańcuchowa transformacja:**
```
# Wróg A (linknum = 1) → przy śmierci spawn B
eventtype = 33, eventdat = 200, eventdat4 = 1

# Wróg B ma w danych enemydie = 201 → przy śmierci spawn C
# (to jest w danych wroga, nie w evencie)
```

### Ograniczenia

- **linknum nie jest przekazywany** - nowy wróg zawsze ma `linknum = 0`
- **Pozycja jest kopiowana** - nowy wróg pojawia się dokładnie tam gdzie zmarł rodzic
- **Slot jest dziedziczony** - chyba że to power-up (zawsze slot 0)
- **enemydie nie jest kumulowany** - Event 33 nadpisuje istniejącą wartość

---

### Event 60 — Assign Special Enemy

Oznacza wrogów z danej grupy jako „specjalnych", ustawiając im hook który przy śmierci wpisuje wartość do globalnej tablicy flag. **Nie powoduje żadnego natychmiastowego efektu** — modyfikuje jedynie pola `special`, `flagnum` i `setto` żyjących wrogów.

| Pole | Zmienna wroga | Działanie |
|------|---------------|-----------|
| `eventdat`  | `flagnum` | Numer globalnej flagi do ustawienia przy śmierci (1-based) |
| `eventdat2` | `setto`   | Wartość wpisywana do flagi: `1` → `true`, inne → `false` |
| `eventdat4` | filtr `linknum` | Numer grupy wrogów do oznaczenia |

### Mechanika działania

**1. Gdy event się odpala:**
```c
for (temp = 0; temp < 100; temp++)
{
    if (enemy[temp].linknum == eventRec[eventLoc-1].eventdat4)
    {
        enemy[temp].special = true;
        enemy[temp].flagnum = eventRec[eventLoc-1].eventdat;
        enemy[temp].setto   = (eventRec[eventLoc-1].eventdat2 == 1);
    }
}
```
Event przegląda wszystkich 100 slotów wrogów i dla każdego z `linknum == eventdat4` ustawia flagę `special = true` oraz zapamiętuje numer flagi i docelową wartość.

**2. Gdy oznaczony wróg umiera:**
```c
if (enemy[temp2].special)
{
    globalFlags[enemy[temp2].flagnum - 1] = enemy[temp2].setto;
}
```
Przy destrukcji wroga (wewnątrz pętli obsługi kolizji/śmierci) silnik sprawdza flagę `special`. Jeśli jest ustawiona, wpisuje `setto` do `globalFlags[flagnum - 1]`.

### Pola wroga — szczegóły

| Pole | Typ | Znaczenie |
|------|-----|-----------|
| `special` | `bool` | Czy wróg ma aktywny hook na flagę globalną |
| `flagnum` | `int` | Indeks (1-based) w tablicy `globalFlags` |
| `setto`   | `bool` | Wartość wpisywana do flagi (`true`/`false`) |

> **`flagnum` jest 1-based** — kod używa `globalFlags[flagnum - 1]`, więc wartość `1` odpowiada `globalFlags[0]`.

### Relacja z globalFlags i eventem 61

Event 60 jest naturalnym partnerem eventu 61, który odczytuje te same flagi:

```c
// Event 61 — jeśli flaga ma daną wartość, przeskocz eventy
if (globalFlags[eventdat - 1] == eventdat2)
    eventLoc += eventdat3;
```

Typowy wzorzec: event 60 ustawia flagę przy śmierci bossa → event 61 wykrywa to i pomija dalsze eventy (np. pomija kolejną falę wrogów lub wyzwala scenę).

### Typowe zastosowania

**1. Boss który po śmierci odblokowuje postęp:**
```
# Spawn bossa z linknum = 5
eventtype = 15, linknum = 5, enemy_id = 300

# Przy śmierci bossa ustaw globalFlags[0] = true
eventtype = 60, eventdat = 1, eventdat2 = 1, eventdat4 = 5

# Jeśli flaga 1 == true, pomiń 3 kolejne eventy
eventtype = 61, eventdat = 1, eventdat2 = 1, eventdat3 = 3
```

**2. Oznaczenie wielu wrogów naraz:**
```
# Wrogowie z linknum = 10 — każdy przy śmierci ustawi flagę 2 na false
eventtype = 60, eventdat = 2, eventdat2 = 0, eventdat4 = 10
```

### Ograniczenia

- **Filtr tylko po `linknum`** — nie można ograniczyć do pojedynczego wroga inaczej niż przez unikalny `linknum`
- **Brak filtra `linknum == 0`** — wrogowie z `linknum = 0` (domyślnym) nie są pomijani, dlatego event 60 z `eventdat4 = 0` oznaczy wszystkich wrogów z `linknum = 0`
- **Nadpisywanie** — kolejne wywołania eventu 60 na tej samej grupie nadpiszą wcześniejsze wartości `flagnum` i `setto`
- **Pętla 100 slotów** — event zawsze sprawdza dokładnie sloty `0`–`99` (stała `100`), niezależnie od aktualnie żyjących wrogów

---

### Tabela pozostałych eventów globalnych

| Type | Pole(a) | Efekt |
|------|---------|-------|
| 25 | `eventdat`=HP, `eventdat4`=group | Ustaw `armorleft` grupy (0=wszyscy) |
| 33 | `eventdat`=enemy_id, `eventdat4`=group | Przy śmierci wroga z grupy utwórz wroga `enemy_id` |
| 39 | `eventdat`=stary linknum, `eventdat2`=nowy | Przenieś wrogów między grupami |
| 47 | `eventdat`=HP, `eventdat4`=group | Jak 25, bez trybu galaga |
| 55 | `eventdat`=xaccel, `eventdat2`=yaccel, `eventdat4`=group | Zmień parametr losowego przyspieszenia |
| 60 | `eventdat`=flagnum (1-based), `eventdat2`=wartość (1=true), `eventdat4`=linknum | Oznacz grupę wrogów jako specjalną — przy śmierci każdego wpisują wartość do `globalFlags[flagnum-1]` |

---

## 5. Eventy Środowiskowe i Sterujące

### Event 2 — Ustaw prędkość scrollingu

| Pole | Zmienna | Opis |
|------|---------|------|
| eventdat  | `backMove`  | Scrolling tła 1 (używany dla Ground) |
| eventdat2 | `backMove2` | Scrolling tła 2 (używany dla Sky) |
| eventdat3 | `backMove3` | Scrolling tła 3 (używany dla Top) |

`explodeMove` ustawiany na `backMove2` jeśli `> 0`, inaczej na `backMove`.

### Event 5 — Załaduj banki sprite'ów

| Pole | Bank |
|------|------|
| eventdat  | Bank 0 |
| eventdat2 | Bank 1 |
| eventdat3 | Bank 2 |
| eventdat4 | Bank 3 |

Wartość `0` = zwolnij dany bank. Banki odpowiadają plikom `.shp` (np. wartość `8` → `shapes8.dat`).

### Event 12 — 4×4 Ground Enemy

Tworzy 4 wrogów rozmieszczonych w kwadracie (2 kolumny × 2 wiersze, offset 24px × 28px):

| Pole | Znaczenie |
|------|-----------|
| eventdat  | Bazowy ID wroga (kolejne to `+1`, `+2`, `+3`) |
| eventdat2 | Pozycja X (jak standardowy spawn) |
| eventdat6 | Wybór slotu: `0`/`1`=slot 25, `2`=slot 0, `3`=slot 50, `4`=slot 75 |

> `eventdat6` jest używane **przed** wywołaniem `JE_createNewEventEnemy`, a następnie zerowane (nie trafia do `fixedmovey`).

### Mechanika działania

**1. Wybór slotu:**
```c
switch (eventdat6) {
    case 0:
    case 1:
        temp = 25;  // Ground slot
        break;
    case 2:
        temp = 0;   // Sky slot
        break;
    case 3:
        temp = 50;  // Top slot
        break;
    case 4:
        temp = 75;  // Ground 2 slot
        break;
}
eventdat6 = 0;  // zerowane przed spawnem
```

**2. Spawn 4 wrogów w siatce 2×2:**
```c
// Wróg 0: pozycja bazowa
JE_createNewEventEnemy(0, temp, 0);

// Wróg 1: pozycja bazowa + 24px X
JE_createNewEventEnemy(1, temp, 0);
if (b > 0)
    enemy[b-1].ex += 24;

// Wróg 2: pozycja bazowa - 28px Y
JE_createNewEventEnemy(2, temp, 0);
if (b > 0)
    enemy[b-1].ey -= 28;

// Wróg 3: pozycja bazowa + 24px X, -28px Y
JE_createNewEventEnemy(3, temp, 0);
if (b > 0)
{
    enemy[b-1].ex += 24;
    enemy[b-1].ey -= 28;
}
```

**3. ID wrogów:**
- Wróg 0: `eventdat` (bazowe ID)
- Wróg 1: `eventdat + 1`
- Wróg 2: `eventdat + 2`
- Wróg 3: `eventdat + 3`

Parametr `uniqueShapeTableI` w `JE_createNewEventEnemy` (0, 1, 2, 3) jest używany do obliczenia ID wroga.

### Układ wrogów

```
Wróg 2 (eventdat+2)    Wróg 3 (eventdat+3)
     (0, -28)                (+24, -28)
     
Wróg 0 (eventdat)     Wróg 1 (eventdat+1)
     (0, 0)                  (+24, 0)
```

Wszystkie 4 wrogowie są w tym samym slotie i mają tę samą pozycję startową Y (zależną od scrollingu).

### Pozycja X

Pozycja X jest obliczana jak dla standardowego spawnu (zależna od `eventdat2` i slotu), a następnie korygowana offsetami:
- Wróg 0: bez korekty
- Wróg 1: +24px
- Wróg 2: bez korekty
- Wróg 3: +24px

### Pozycja Y

Pozycja Y jest taka sama dla wszystkich 4 wrogów (zależna od scrollingu slotu), a następnie korygowana:
- Wróg 0: bez korekty
- Wróg 1: bez korekty
- Wróg 2: -28px
- Wróg 3: -28px

### Inne pola

Wszystkie 4 wrogowie otrzymują te same wartości z eventu:
- `y_vel` (eventdat3)
- `y_offset` (eventdat5)
- `link_num` (eventdat4)
- `fixed_move_y` (eventdat6 po zerowaniu = 0)

Pole `eventdat6` jest zerowane przed spawnem, więc `fixed_move_y` jest zawsze 0 dla wszystkich 4 wrogów.

### Przykład

```json
{
  "event_type": 12,
  "enemy_id": 440,
  "raw_x": 80,
  "slot_selector": 3,
  "enemy_ids": [440, 441, 442, 443]
}
```

Tworzy 4 wrogów w slotu 50 (Top):
- Wróg 440: pozycja (base_x, base_y)
- Wróg 441: pozycja (base_x + 24, base_y)
- Wróg 442: pozycja (base_x, base_y - 28)
- Wróg 443: pozycja (base_x + 24, base_y - 28)

### Event 13 — Dezaktywuj Random-Spawn
### Event 14 — Aktywuj Random-Spawn

Te eventy kontrolują system losowego spawnu wrogów, który jest niezależny od eventów spawnu w pliku `.lvl`.

| Event | Zmienna | Działanie |
|-------|---------|-----------|
| 13 | `enemiesActive = false` | Wyłącza losowy spawn wrogów |
| 14 | `enemiesActive = true` | Włącza losowy spawn wrogów |

### Mechanika losowego spawnu

Losowy spawn jest sprawdzany w każdej klatce w `JE_drawEnemy`:

```c
/* New Enemy */
if (enemiesActive && mt_rand() % 100 > levelEnemyFrequency)
```

**Parametry losowego spawnu:**
- `enemiesActive` — czy losowy spawn jest włączony (Event 13/14)
- `levelEnemyFrequency` — częstotliwość spawnu (typ `JE_word` / `uint16_t`; 0 = zawsze, 99 = rzadko, domyślnie 96)
- `levelEnemy[40]` — tablica ID wrogów do losowego spawnu (ładowana z pliku `.lvl`)
- `levelEnemyMax` — liczba wrogów w tablicy (maksimum 40, ładowana z pliku `.lvl`)

Tablica `levelEnemy` jest ładowana z nagłówka pliku `.lvl` podczas ładowania poziomu:

```c
fread_u16_die(&levelEnemyMax, 1, level_f);        // liczba wrogów
fread_u16_die(levelEnemy, levelEnemyMax, level_f); // tablica ID wrogów
```

**Event 37** ustawia `levelEnemyFrequency`:

```c
case 37:
    levelEnemyFrequency = eventRec[eventLoc-1].eventdat;
    break;
```

> ⚠️ **Uwaga:** `levelEnemyFrequency` jest typu `JE_word` (`uint16_t`), natomiast `eventdat` jest `Sint16`. Przypisanie ujemnej wartości `eventdat` da w efekcie bardzo dużą liczbę bez znaku, co sprawi, że warunek `mt_rand() % 100 > levelEnemyFrequency` będzie zawsze fałszywy — spawn zostanie praktycznie wyłączony.

### Domyślne wartości

Przy ładowaniu poziomu (`JE_main`):
Spawn następuje gdy losowa liczba z zakresu 0–99 jest większa niż levelEnemyFrequency. Przy domyślnej wartości 96 (tylko 97, 98 lub 99 spełniają warunek).
```c
enemiesActive = true;          // domyślnie włączony
levelEnemyFrequency = 96;     // domyślna częstotliwość
```
Pozycja startowa pochodzi z pól startx / starty w danych wroga, z opcjonalnym losowym rozrzutem:  

jeśli startxc != 0, pozycja X jest losowana w zakresie startx ± startxc
enemy->ex = enemyDat[eDatI].startx + (mt_rand() % (startxc * 2)) - startxc + 1;  

jeśli startxc == 0, pozycja jest po prostu stała
enemy->ex = enemyDat[eDatI].startx + 1;  

To samo dla Y.  

Prędkość pochodzi z pól xmove / ymove w danych wroga:
cenemy->exc = enemyDat[eDatI].xmove;
enemy->eyc = enemyDat[eDatI].ymove;  

Czyli wróg pojawia się dokładnie tam i porusza dokładnie tak, jak ma zapisane w swojej definicji — ani o piksel inaczej. Projektant poziomu nie ma tu żadnej kontroli nad pozycją ani ruchem poza tym, jakich wrogów wpisze do tablicy levelEnemy.

### Grupy slotów wrogów

`JE_newEnemy(0, tempW, 0)` spawnuje wroga do pierwszego wolnego slotu w grupie **Ground (indeksy 0–24)**. Dla porównania:

| Grupa | Indeksy slotów | Wywołanie |
|-------|---------------|-----------|
| Ground | 0–24 | `JE_newEnemy(0, ...)` |
| Sky | 25–49 | `JE_newEnemy(25, ...)` / event 15 |
| Top | 50–74 | `JE_newEnemy(50, ...)` |

Losowy spawn zawsze trafia do grupy **Ground**, nie Sky.

### Typowe zastosowania

**1. Wyłączenie losowego spawnu podczas bossa:**
```
eventtype = 13  // dezaktywuj losowy spawn przed bossem
```

**2. Włączenie losowego spawnu po bossie:**
```
eventtype = 14  // aktywuj losowy spawn po bossie
```

**3. Zwiększenie częstotliwości spawnu:**
```
eventtype = 37
eventdat = 50  // levelEnemyFrequency = 50 (częstszy spawn)
```

**4. Maksymalna częstotliwość spawnu (spawn w każdej klatce):**
```
eventtype = 37
eventdat = 0   // levelEnemyFrequency = 0 (zawsze spawnuje)
```

### Różnice od eventów spawnu

| Cecha | Eventy spawnu (6, 7, 10, 15, etc.) | Losowy spawn |
|-------|--------------------------------------|--------------|
| Czas | Zdefiniowany w pliku `.lvl` (`eventtime`) | Losowy w każdej klatce |
| Pozycja | Zdefiniowana w evencie | Losowa (pierwszy wolny slot w grupie Ground) |
| ID wroga | Zdefiniowane w evencie | Losowe z tablicy `levelEnemy` |
| Kontrola | Precyzyjna przez eventy | Ogólna przez `levelEnemyFrequency` |
| Dźwięk | Zależy od wroga | Specjalny przypadek dla ID 2 (`S_WEAPON_7`) |
---

### Event 46 — Zmiana trudności

| Pole | Zmienna | Opis |
|------|---------|------|
| eventdat  | `difficultyLevel` | Delta trudności (może być ujemna) |
| eventdat2 | flaga | `0` = zmień zawsze; `≠0` = zmień tylko w trybie 2-graczy lub arcade |
| eventdat3 | `damageRate` | Nowa wartość; `0` = bez zmiany |

---

## 6. Hierarchia Ruchu w Każdej Klatce

W funkcji `JE_drawEnemy`, pozycja Y każdego wroga jest aktualizowana w następującej **stałej kolejności**:

```c
// 1. Ruch stały (niezależny od fizyki i scrollingu)
enemy.ey += enemy.fixedmovey;

// 2. Ruch fizyczny (prędkość z przyspieszeniami)
enemy.ey += enemy.eyc;

// 3. Ruch środowiska (scrolling tła)
enemy.ey += tempBackMove;
```

**`tempBackMove`** odpowiada prędkości scrollingu właściwego dla slotu wroga.

Analogicznie dla osi X:
```c
// Ruch fizyczny X (brak fixed/środowiska dla X)
enemy.ex += enemy.exc;
```

Oś X nie ma odpowiednika `fixedmovey` ani korekty `backMove` — porusza się wyłącznie przez `exc`.

### Aktualizacja prędkości `eyc` w każdej klatce

```
Jeśli eycc != 0:
  --eyccw
  Gdy eyccw == 0:
    eyc += eyccadd
    eyccw = eyccwmax   (reset odliczania)
    Jeśli eyc == eyrev:
      eycc    = -eycc
      eyrev   = -eyrev
      eyccadd = -eyccadd   ← odwrócenie wahadła
```

### Odbicia od granic

```c
if (enemy.ex <= xminbounce || enemy.ex >= xmaxbounce)
    enemy.exc = -enemy.exc;

if (enemy.ey <= yminbounce || enemy.ey >= ymaxbounce)
    enemy.eyc = -enemy.eyc;
```

Sprawdzane **po** obliczeniu nowej pozycji, ale przed usunięciem poza ekranem.

### Usunięcie poza ekranem

```c
if (enemy.ex < -80 || enemy.ex > 340)   → enemy usunięty
if (enemy.ey < -112 || enemy.ey > 190)  → enemy usunięty
```

---

## 7. Mechanika `fixedmovey` — Stały Ruch Niezależny

Pole `fixedmovey` to stały ruch pionowy, który jest **dodawany w każdej klatce** niezależnie od:
- Prędkości fizycznej (`eyc`)
- Przyspieszenia wahadłowego (`eycc`)
- Scrollingu tła (`tempBackMove`)

### Różnica między ruchem fizycznym a stałym

| Typ ruchu | Wartość | Zależności | Modyfikowalność |
|-----------|---------|------------|----------------|
| `eyc` (fizyczny) | Zmienia się co klatkę przez `eycc` | Wahadło, przyspieszenie | Event 19 (Global Move) |
| `fixedmovey` (stały) | Stała wartość | Brak zależności | Event 19, spawn (eventdat6) |
| `tempBackMove` (środowisko) | Zależy od slotu | Scrolling tła | Event 2 |

### Wzór końcowy na pozycję Y

```c
ey_nowe = ey_stare + fixedmovey + eyc + tempBackMove
```

**Kolejność dodawania jest istotna:**
1. `fixedmovey` — najpierw stały dryf
2. `eyc` — potem ruch fizyczny
3. `tempBackMove` — na końcu scrolling tła

### Zastosowania `fixedmovey`

**1. Wróg poruszają się tylko z tłem (stacjonarny względem świata):**
```
ymove = 0
fixedmovey = 0
eyc = 0
→ Wróg porusza się tylko z prędkością scrollingu tła
```

**2. Szybki atak z dołu (niezależny od fizyki):**
```
ymove = 2
fixedmovey = -3
eyc = 2
→ Efektywny ruch w górę: 2 (fizyczny) - 3 (stały) + scrolling
```

**3. Powolny dryf w dół (nawet gdy wróg ma zerową prędkość):**
```
ymove = 0
fixedmovey = 1
eyc = 0
→ Wróg zawsze przesuwa się o 1px/klatkę w dół + scrolling
```

### Modyfikacja przez eventy

**Event 19 (Global Move):**
| Wartość eventdat6 | Efekt |
|-------------------|-------|
| `0` | Nie zmieniaj `fixedmovey` |
| `-99` | Zresetuj `fixedmovey` do 0 |
| Inna wartość | Ustaw nową wartość `fixedmovey` |

**Spawn (eventdat6):**
```
fixedmovey = eventdat6  // ustawione przy spawnie
```

### Interakcja z wahadłem

`fixedmovey` jest **niezależny** od mechaniki wahadła (`eycc`, `eyrev`). Nawet gdy wahadło odwraca prędkość `eyc`, `fixedmovey` pozostaje stały.

**Przykład:**
```
eyc = 5 → 10 → 5 → 0 → -5 (oscylacja przez wahadło)
fixedmovey = 1 (stały)
→ Efektywny ruch: 6 → 11 → 6 → 1 → -4
```

Wahadło wpływa tylko na `eyc`, `fixedmovey` jest zawsze dodawany.

### Wartości typowe

| Wartość | Zastosowanie |
|---------|--------------|
| `0` | Brak stałego ruchu (tylko fizyka + scrolling) |
| `1` | Powolny dryf w dół |
| `-1` | Powolny dryf w górę |
| `-3` do `-5` | Szybki atak z dołu ekranu |
| `2` do `5` | Szybki zjazd w dół |

---

## 8. System `linknum` — Grupowanie Wrogów

Pole `linknum` służy do grupowania wrogów dla koordynowanego zachowania przez eventy globalne. Wrogowie z tym samym `linknum` tworzą "formację" która może być modyfikowana jednocześnie.

### Przypisanie linknum

**Przy spawnie (eventdat4):**
```c
enemy.linknum = eventdat4;  // ustawione w JE_createNewEventEnemy
```

**Wartość domyślna:**
```c
enemy->linknum = 0;  // ustawione w JE_makeEnemy (przed spawnem)
```

**Event 39 (Linknum Change):**
```c
// Przenosi wrogów z jednej grupy do drugiej
for (temp = 0; temp < 100; temp++)
{
    if (enemy[temp].linknum == eventdat)  // stary linknum
        enemy[temp].linknum = eventdat2;  // nowy linknum
}
```

### Filtracja przez linknum w eventach globalnych

Większość eventów globalnych (19, 20, 24, 25, 27, 31, 33, 47, 55, 60, 74) używa `linknum` do wyboru grupy wrogów:

```c
if (eventdat4 == 0 || enemy[temp].linknum == eventdat4)
{
    // zastosuj zmianę do tego wroga
}
```

**Wartości specjalne eventdat4:**
| Wartość | Znaczenie |
|---------|-----------|
| `0` | Dotyczy wszystkich wrogów (brak filtru) |
| `1-255` | Dotyczy tylko wrogów z tym linknum |
| `99` (tylko event 31) | Wszyscy wrogowie (synonim 0) |

### Specjalne zachowania związane z linknum

**1. Przekazywanie linknum przy launch (spawn z wroga):**
```c
// W JE_drawEnemy, gdy wróg launchuje innego wroga
if (enemy[i].launchspecial == 1 && enemy[i].linknum < 100)
{
    e->linknum = enemy[i].linknum;  // przekazanie linknum
}
```

**2. Enemydie (wróg przy śmierci tworzy innego wroga):**
```c
// W JE_drawEnemy, przy śmierci wroga
if ((enemy[temp2].enemydie > 0) && ...)
{
    // spawn nowego wroga z enemydie
    // nowy wróg dostaje ten sam linknum co rodzic?
    // NIE - linknum jest ustawiany na 0 w JE_makeEnemy
}
```

**3. Linknum a damage (kontynualne obrażenia):**
```c
// W JE_drawEnemy, przy obrażeniach
temp = enemy[b].linknum;
if (temp == 0)
    temp = 255;  // linknum 0 jest traktowane jako 255 dla damage

// Wrogowie z tym samym linknum otrzymują damage razem
if (enemy[e].linknum == temp && ...)
{
    // zastosuj damage
}
```

**4. Linknum a boss bar:**
```c
// W JE_drawEnemy
temp = enemy[b].linknum;
if (temp == 0)
    temp = 255;

for (unsigned int i = 0; i < COUNTOF(boss_bar); i++)
    if (temp == boss_bar[i].link_num)
        boss_bar[i].color = 6;  // aktualizacja koloru boss bar
```

### Typowe wzorce użycia linknum

**1. Formacja wrogów z synchronicznym ruchem:**
```
# Spawn 3 wrogów z tym samym linknum
eventtype = 15, link_num = 5, enemy_id = 100
eventtype = 15, link_num = 5, enemy_id = 100
eventtype = 15, link_num = 5, enemy_id = 100

# Zastosuj wahadło do całej grupy
eventtype = 20, eventdat = 3, eventdat4 = 5
```

**2. Boss z wieloma częściami:**
```
# Główny wróg
eventtype = 15, link_num = 10, enemy_id = 200

# Części bossa (przekazywane przez launch)
# Mają ten sam linknum = 10
# Damage rozprzestrzenia się na wszystkie części
```

**3. Dynamiczna zmiana grupy:**
```
# Wróg startuje w grupie 5
eventtype = 15, link_num = 5, enemy_id = 100

# Po pewnym czasie przenosi się do grupy 6
eventtype = 39, eventdat = 5, eventdat2 = 6

# Teraz eventy dla grupy 6 go dotyczą
```

### Ograniczenia

- **Wartość 0 jest specjalna** - oznacza "brak grupy" ale jest traktowana jako 255 w niektórych kontekstach (damage, boss bar)
- **Wartości > 255 nie są używane** - linknum to uint8 (0-255)
- **Przekazywanie linknum nie jest automatyczne** - tylko launchspecial=1 przekazuje linknum, enemydie nie
- **Eventy globalne z eventdat4=0 dotyczą WSZYSTKICH wrogów** - nie tylko tych z linknum=0

---

## 9. Ograniczenia Odbicia — Bounce Params

Wrogowie mogą być ograniczeni w ruchu przez granice odbicia. Gdy wróg osiągnie granicę, jego prędkość jest odwracana (odbicie).

### Struktura granic

Każdy wróg ma 4 granice odbicia:
```c
enemy.xminbounce  // lewa granica X
enemy.xmaxbounce  // prawa granica X
enemy.yminbounce  // górna granica Y
enemy.ymaxbounce  // dolna granica Y
```

### Wartości domyślne

Przy spawnie w `JE_makeEnemy`:
```c
enemy->xminbounce = -10000;
enemy->xmaxbounce = 10000;
enemy->yminbounce = -10000;
enemy->ymaxbounce = 10000;
```

Wartości ±10000 są praktycznie nieosiągalne (ekran ma szerokość ~320px i wysokość ~200px), więc **domyślnie wrogowie nie odbijają się od krawędzi**.

### Mechanika odbicia

Sprawdzanie odbywa się **po** obliczeniu nowej pozycji, ale przed usunięciem poza ekranem:

```c
// Odbicie X
if (enemy.ex <= xminbounce || enemy.ex >= xmaxbounce)
    enemy.exc = -enemy.exc;  // odwróć prędkość X

// Odbicie Y
if (enemy.ey <= yminbounce || enemy.ey >= ymaxbounce)
    enemy.eyc = -enemy.eyc;  // odwróć prędkość Y
```

**Ważne:** Odbicie odwraca **tylko prędkość** (`exc`/`eyc`), nie pozycję. Wróg może chwilowo przekroczyć granicę przed odbiciem.

### Event 74 — Bounce Params

Ustawia granice odbicia dla grupy wrogów:

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `xmaxbounce` | Prawa granica X; `-99` = nie zmieniaj |
| eventdat2 | `ymaxbounce` | Dolna granica Y; `-99` = nie zmieniaj |
| eventdat4 | `linknum`    | Filtr grupy; `0` = wszyscy |
| eventdat5 | `xminbounce` | Lewa granica X; `-99` = nie zmieniaj |
| eventdat6 | `yminbounce` | Górna granica Y; `-99` = nie zmieniaj |

### Przykłady użycia

**1. Wróg odbijający się od krawędzi ekranu:**
```
eventtype = 74
eventdat  = 320   // xmaxbounce (prawa krawędź)
eventdat2 = 190   // ymaxbounce (dolna krawędź)
eventdat5 = 0     // xminbounce (lewa krawędź)
eventdat6 = -112  // yminbounce (górna krawędź)
eventdat4 = 0     // wszyscy wrogowie
```

**2. Wróg ograniczony do centralnej części ekranu:**
```
eventtype = 74
eventdat  = 240   // prawa granica (środek + 80)
eventdat2 = 150   // dolna granica (środek + 50)
eventdat5 = 80    // lewa granica (środek - 80)
eventdat6 = 50    // górna granica (środek - 50)
eventdat4 = 5     // tylko grupa 5
```

**3. Tylko odbicie od dolnej krawędzi:**
```
eventtype = 74
eventdat  = -99   // nie zmieniaj xmaxbounce
eventdat2 = 190   // ymaxbounce = 190
eventdat5 = -99   // nie zmieniaj xminbounce
eventdat6 = -99   // nie zmieniaj yminbounce
eventdat4 = 0
```

### Interakcja z innymi mechanikami ruchu

**Odbicie a wahadło:**
- Wahadło (`eycc`) kontynuuje działanie po odbiciu
- Prędkość po odbiciu może być odwrócona przez wahadło w następnej klatce

**Odbicie a fixedmovey:**
- `fixedmovey` jest dodawany **po** sprawdzeniu odbicia
- Wróg może stale "dryfować" w jedną stronę mimo odbicia

**Odbicie a scrolling:**
- Scrolling (`tempBackMove`) nie wpływa na granice odbicia
- Granice są absolutne, nie względne do scrollingu

### Usunięcie poza ekranem

Nawet z ustawionymi granicami odbicia, wrogowie są usuwani gdy:
```c
if (enemy.ex < -80 || enemy.ex > 340)   → usunięty
if (enemy.ey < -112 || enemy.ey > 190)  → usunięty
```

Granice odbicia mogą być **szersze** niż granice usunięcia, ale nie powinny być węższe - inaczej wróg może "utknąć" między granicą odbicia a granicą usunięcia.

### Typowe wartości granic

| Granica | Wartość | Zastosowanie |
|---------|---------|--------------|
| `xminbounce` | `0` | Lewa krawędź ekranu |
| `xmaxbounce` | `320` | Prawa krawędź ekranu |
| `yminbounce` | `-112` | Górna krawędza ekranu |
| `ymaxbounce` | `190` | Dolna krawędź ekranu |
| `±10000` | Domyślne | Brak odbicia (praktycznie) |

---

## 10. Sloty i Prędkości Scrollingu

Silnik gry dzieli wrogów na 4 sloty po 25 wrogów każdy. Każdy slot używa innej prędkości scrollingu tła, co wpływa na ruch względny wrogów.

### Struktura slotów

| Slot | Zakres | enemyOffset | Typ wrogów | Zmienna scrollingu | Domyślna wartość |
|------|--------|-------------|------------|-------------------|-----------------|
| 0    | 0-24   | 0           | Sky (powietrzni) | `backMove2` | 2 |
| 1    | 25-49  | 25          | Ground (naziemni) | `backMove` | 1 |
| 2    | 50-74  | 50          | Top (tło 3) | `backMove3` | 3 |
| 3    | 75-99  | 75          | Ground 2 (naziemni) | `backMove` | 1 |

### Zmienne scrollingu

```c
JE_word backMove;   // scrolling dla Ground (slot 1, 3)
JE_word backMove2;  // scrolling dla Sky (slot 0)
JE_word backMove3;  // scrolling dla Top (slot 2)
```

Te zmienne są globalne i mogą być modyfikowane przez Event 2.

### Wpływ scrollingu na ruch wrogów

W każdej klatce, do pozycji Y każdego wroga jest dodawana prędkość scrollingu właściwa dla jego slotu:

```c
// W JE_drawEnemy
switch (enemyOffset) {
    case 0:       // Sky
        tempBackMove = backMove2;
        break;
    case 25:      // Ground
    case 75:      // Ground 2
        tempBackMove = backMove;
        break;
    case 50:      // Top
        tempBackMove = backMove3;
        break;
}

enemy.ey += tempBackMove;  // dodane po fixedmovey i eyc
```

### Ruch względny vs absolutny

**Ruch absolutny (współrzędne świata):**
- Pozycja `ex`, `ey` jest absolutna
- Wrogowie z różnymi slotami poruszają się z różną prędkością względną do ekranu
- Ale w przestrzeni świata mogą mieć tę samą prędkość

**Przykład:**
```
Wróg A (Sky, backMove2=2):
  eyc = 0, fixedmovey = 0
  Ruch względny: 2px/klatkę (tylko scrolling)

Wróg B (Ground, backMove=1):
  eyc = 0, fixedmovey = 0  
  Ruch względny: 1px/klatkę (tylko scrolling)
```

Obaj mają zerową prędkość fizyczną, ale wróg A porusza się 2x szybciej względem ekranu.

### Spawn a scrolling

Przy spawnie od góry (typy 6, 7, 10, 15), pozycja Y jest korygowana o prędkość scrollingu:

```c
enemy.ey = -28;
enemy.ey -= backMove;  // lub backMove2/backMove3 zależnie od slotu
```

To sprawia, że wróg "wchodzi" z górnej krawędzi ekranu płynnie, z uwzględnieniem ruchu tła.

### Event 2 — Ustaw prędkość scrollingu

Modyfikuje globalne zmienne scrollingu:

| Pole | Zmienna | Opis |
|------|---------|------|
| eventdat  | `backMove`  | Scrolling tła 1 (Ground slots 1, 3) |
| eventdat2 | `backMove2` | Scrolling tła 2 (Sky slot 0) |
| eventdat3 | `backMove3` | Scrolling tła 3 (Top slot 2) |

**Przykład:**
```
# Zatrzymaj scrolling tła 1 (wrogowie naziemni stoją w miejscu)
eventtype = 2
eventdat = 0
eventdat2 = 2  // Sky nadal się porusza
eventdat3 = 3  // Top nadal się porusza
```

### Event 30 — Wariant bez explodeMove

Podobny do Event 2, ale nie modyfikuje `explodeMove`:

```c
// Event 2:
if (backMove2 > 0)
    explodeMove = backMove2;
else
    explodeMove = backMove;

// Event 30:
// tylko ustawia backMove, backMove2, backMove3
// nie dotyka explodeMove
```

### Różnice w zachowaniu slotów

**Slot 0 (Sky):**
- Najwolniejszy domyślny scrolling (backMove2=2)
- Używany dla wrogów powietrznych na tle 1
- Spawn od góry: `ey = -28 - backMove2`

**Slot 1, 3 (Ground):**
- Średni scrolling (backMove=1)
- Używany dla wrogów naziemnych
- Spawn od góry: `ey = -28 - backMove`
- Pozycja X jest przesunięta o -12 względem Sky

**Slot 2 (Top):**
- Najszybszy domyślny scrolling (backMove3=3)
- Używany dla wrogów na tle 3 (dalsze plany)
- Spawn od góry: `ey = -28 - backMove3`
- Pozycja X zależy od `background3x1` i `background3x1b`

### Praktyczne zastosowania

**1. Parallax effect (efekt paralaksy):**
```
backMove = 1   // tło 1 - najwolniejsze
backMove2 = 2  // tło 2 - średnie
backMove3 = 3  // tło 3 - najszybsze
→ Wrogowie na dalszych planach poruszają się szybciej
```

**2. Zatrzymanie wrogów naziemnych:**
```
eventtype = 2
eventdat = 0   // Ground się zatrzymuje
eventdat2 = 2  // Sky nadal się porusza
eventdat3 = 3  // Top nadal się porusza
→ Tylko wrogowie naziemni stoją w miejscu
```

**3. Przyspieszenie scrollingu:**
```
eventtype = 2
eventdat = 3   // Ground 3x szybciej
eventdat2 = 6  // Sky 3x szybciej
eventdat3 = 9  // Top 3x szybciej
→ Wszystkie wrogowie przyspieszają
```

### Wartości typowe

| Zmienna | Wartość | Zastosowanie |
|---------|---------|--------------|
| `backMove` | `0` | Zatrzymanie tła 1 |
| `backMove` | `1` | Domyślna wartość |
| `backMove` | `2-5` | Przyspieszony scrolling |
| `backMove2` | `0` | Zatrzymanie tła 2 |
| `backMove2` | `2` | Domyślna wartość |
| `backMove2` | `4-10` | Szybki scrolling |
| `backMove3` | `0` | Zatrzymanie tła 3 |
| `backMove3` | `3` | Domyślna wartość |
| `backMove3` | `6-15` | Bardzo szybki scrolling |

---

## 11. Wartości Specjalne Pól

| Pole eventu | Wartość specjalna | Znaczenie |
|-------------|-------------------|-----------|
| `eventdat2` (`x`) | `-99` | Nie modyfikuj pozycji X — użyj `startx` z danych wroga |
| `eventdat3` (`y_vel`) | `0` | Nie modyfikuj prędkości Y (bezpieczne „brak efektu") |
| `eventdat6` w event 19 | `0` | Nie zmieniaj `fixedmovey` |
| `eventdat6` w event 19 | `-99` | Zresetuj `fixedmovey` do 0 |
| `eventdat` / `eventdat2` w event 19, 20, 27 | `-99` | Nie zmieniaj danej zmiennej |
| `eventdat4` (`link_num`) | `0` | Brak grupy (domyślnie przy inicjalizacji) |
| `eventdat4` w event 31 | `99` | Dotyczy wszystkich wrogów |
| `eventdat4` w event 20, 25, 74 | `0` | Dotyczy wszystkich wrogów |

---

## 8. Przykłady Konfiguracji

### Wróg naziemny stacjonarny (porusza się tylko z tłem)

**WAŻNE:** Eventy spawnu (6, 7, 10, 15, etc.) nie nadpisują prędkości wroga - wróg zachowuje swoje `xmove` i `ymove` z danych wroga (`enemyDat`).

Aby wróg był naprawdę stacjonarny (tylko z tłem), trzeba:

**Opcja 1: Wybrać wroga z zerową prędkością w danych**
```
# Wybierz enemy_id wroga, który ma xmove=0 i ymove=0 w enemyDat
eventtype  = 6   (Ground)
eventdat   = X    (ID wroga z xmove=0, ymove=0)
eventdat2  = 160  (pozycja X)
eventdat4  = 0    (linknum)
```

**Opcja 2: Nadpisać prędkość po spawnie**
```
# Spawn wroga
eventtype  = 6   (Ground)
eventdat   = X    (ID wroga)
eventdat2  = 160  (pozycja X)
eventdat4  = 5    (linknum)

# Nadpisz prędkość dla grupy
eventtype  = 19  (Global Move)
eventdat   = 0    (exc = 0)
eventdat2  = 0    (eyc = 0)
eventdat4  = 5    (linknum tej samej grupy)
```

Wróg będzie się poruszał tylko z tłem (scrolling `backMove`), ponieważ jego fizyczna prędkość (`exc`, `eyc`) jest 0.

### Szybki atak z dołu ekranu

**WAŻNE:** Parametry `y_vel`, `y_offset`, `fixed_move_y` w JSON nie są używane przez eventy spawnu - to tylko pola z parsera. Rzeczywiste parametry to `eventdat` (ID wroga), `eventdat2` (X), `eventdat4` (linknum), `eventdat5` (Y offset dla Event 17).

```
eventtype  = 17  (Ground Bottom)
eventdat   = X    (ID wroga z ymove < 0 w danych)
eventdat2  = 80   (pozycja X)
eventdat5  = 0    (Y offset, startuje z ey=190)
```

Wróg będzie leciał w górę zgodnie z jego `ymove` z danych wroga. Aby dodać dodatkowy stały dryf, użyj Event 19 po spawnie:

```
eventtype  = 19  (Global Move)
eventdat   = 0    (nie zmieniaj X)
eventdat2  = 0    (nie zmieniaj Y)
eventdat6  = -1   (fixedmovey = -1, stały dryf w górę)
eventdat4  = 0    (wszyscy wrogowie)
```

### Formacja wrogów z synchronicznym ruchem wahadłowym

```
# Spawn grupy (np. 3× event type 15):
link_num = 5   (ta sama grupa)

# Następnie event 20 (Global Accel):
eventdat  = 3   (excc = 3 → wahadło poziome)
eventdat2 = 0   (eycc bez zmian)
eventdat4 = 5   (dotyczy grupy 5)

# Następnie event 27 (Global AccelRev):
eventdat  = 20  (exrev = 20 → limit prędkości X)
eventdat4 = 5
```

### Wróg który przy śmierci wypuszcza power-up

```
# Spawn wroga z link_num = 10, event type 15
# Następnie event 33:
eventdat  = 533  (ID power-upa)
eventdat4 = 10   (grupa)
```

---

## 9. Symulacja Matematyczna — Oś Y

### Dane wejściowe

**Z pliku wroga (`.json`):**
- `ymove` (tup[8]) = `2` — bazowa prędkość pionowa
- `ycaccel` (tup[12]) = `1` — stałe przyspieszenie (`eycc`)
- `yrev` (tup[43]) = `10` — limit prędkości (`eyrev`)

**Z eventu (`.lvl`):**
- `eventtype` = `15` (Sky Enemy)
- `y_vel` (eventdat3) = `3`
- `fixed_move_y` (eventdat6) = `1`
- `y_offset` (eventdat5) = `0`
- `backMove2` = `2` (scrolling dla Sky)

---

### Klatka 0 — Inicjalizacja przy spawnie

```
# Pozycja Y:
ey = -28 - backMove2 + y_offset
ey = -28 - 2 + 0 = -30

# Prędkość Y:
eyc = ymove + y_vel
eyc = 2 + 3 = 5

# Silnik wahadłowy (z danych wroga, ycaccel=1):
eycc     = 1
eyccw    = abs(1) = 1
eyccwmax = 1
eyccadd  = +1
eyrev    = 10    ← (yrev=0 → eyrev=100 wg reguły xrev, ale tutaj używamy yrev=10 wprost)
```

---

### Klatka 1 — Pierwsza aktualizacja

**Krok A — Aktualizacja silnika wahadłowego:**
```
--eyccw → eyccw = 0

Gdy eyccw == 0:
  eyc += eyccadd  →  eyc = 5 + 1 = 6
  eyccw = eyccwmax = 1  (reset)

  Czy eyc == eyrev?  6 == 10 → NIE → brak odwrócenia
```

**Krok B — Obliczenie nowej pozycji:**
```
ey = ey_stare + fixedmovey + eyc + tempBackMove
ey = -30 + 1 + 6 + 2 = -21
```

---

### Klatka 2 — Druga aktualizacja

**Krok A:**
```
--eyccw → 0 → eyc += 1 → eyc = 7
eyccw = 1
Czy 7 == 10? NIE
```

**Krok B:**
```
ey = -21 + 1 + 7 + 2 = -11
```

---

### Klatka 4 — Osiągnięcie limitu prędkości

```
eyc = 5+1+1+1+1 = 9  (po klatce 4)
...
Klatka 5: eyc += 1 → eyc = 10 = eyrev → odwrócenie wahadła:
  eycc    = -1
  eyrev   = -10
  eyccadd = -1
```

Od tego momentu `eyc` zaczyna **maleć** (wróg stopniowo zwalnia), aż osiągnie `-10`, po czym ponownie się odwróci — powstaje efekt oscylacji.

---

### Tabela stanów

| Klatka | `eyc` | `ey` | Uwagi |
|--------|-------|------|-------|
| 0 (spawn) | 5 | -30 | Inicjalizacja |
| 1 | 6 | -21 | Pierwsze przyspieszenie |
| 2 | 7 | -11 | |
| 3 | 8 | 0   | Wróg wchodzi w ekran |
| 4 | 9 | 12  | |
| 5 | 10 | 25 | Limit → odwrócenie wahadła |
| 6 | 9 | 37  | Zaczyna zwalniać |

`fixed_move_y = 1` i `backMove2 = 2` są dodawane **w każdej klatce**, więc nawet gdy `eyc` spada do 0 lub ujemne, wróg nadal przesuwa się w dół o 3px/klatkę (1+2).