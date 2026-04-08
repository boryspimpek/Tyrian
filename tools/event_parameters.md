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
7. [Wartości Specjalne Pól](#7-wartości-specjalne-pól)
8. [Przykłady Konfiguracji](#8-przykłady-konfiguracji)
9. [Symulacja Matematyczna — Oś Y](#9-symulacja-matematyczna--oś-y)

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

> **Uwaga na `fixedmovey`:** Warunek `eventdat6 == -99` zeruje `fixedmovey`, warunek `eventdat6 != 0` ustawia nową wartość. Wartość `0` w evencie pozostawia `fixedmovey` bez zmian.

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

Pełny reset stanu wahadła dla X (kod):
```c
enemy.excc    = eventdat;
enemy.exccw   = abs(eventdat);
enemy.exccwmax = abs(eventdat);
enemy.exccadd = (eventdat > 0) ? 1 : -1;
```

---

### Event 24 — Global Animate

Zmienia parametry animacji grupy.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `ani`      | Gdy `> 0`: nowy ostatni indeks klatki animacji |
| eventdat2 | `enemycycle` / `animin` | Gdy `> 0`: ustaw klatkę startową i `animin`; gdy `0`: `enemycycle=0` |
| eventdat3 | tryb       | `0`=zawsze aktywna, `1`=jednorazowa (`animax=ani`), `2`=tylko przy strzale |
| eventdat4 | `linknum`  | Filtr grupy |

---

### Event 27 — Global AccelRev

Zmienia limity prędkości wahadła oraz filtr koloru.

| Pole | Zmienna | Działanie |
|------|---------|-----------|
| eventdat  | `exrev` | Nowy limit X; `-99` = nie zmieniaj |
| eventdat2 | `eyrev` | Nowy limit Y; `-99` = nie zmieniaj |
| eventdat3 | selector/filtr | Gdy `1–16`: ustaw `filter` (kolor); gdy `80–89`: selektor grupy; `0` = ignoruj |
| eventdat4 | `linknum` | Filtr grupy (lub `0` = wszyscy) |

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

### Tabela pozostałych eventów globalnych

| Type | Pole(a) | Efekt |
|------|---------|-------|
| 25 | `eventdat`=HP, `eventdat4`=group | Ustaw `armorleft` grupy (0=wszyscy) |
| 33 | `eventdat`=enemy_id, `eventdat4`=group | Przy śmierci wroga z grupy utwórz wroga `enemy_id` |
| 39 | `eventdat`=stary linknum, `eventdat2`=nowy | Przenieś wrogów między grupami |
| 47 | `eventdat`=HP, `eventdat4`=group | Jak 25, bez trybu galaga |
| 55 | `eventdat`=xaccel, `eventdat2`=yaccel, `eventdat4`=group | Zmień parametr losowego przyspieszenia |
| 60 | `eventdat`=flagnum, `eventdat2`=wartość, `eventdat4`=group | Oznacz wroga jako specjalny (globalne flagi) |

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

## 7. Wartości Specjalne Pól

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

```
eventtype  = 6   (Ground)
enemy_id   = X
x          = 160  (środek ekranu)
y_vel      = 0    (brak własnej prędkości)
link_num   = 0
y_offset   = 0
fixed_move_y = 0  (brak stałego ruchu — tylko backMove)
```

### Szybki atak z dołu ekranu

```
eventtype   = 17  (Ground Bottom)
enemy_id    = X
x           = 80
y_vel       = -5  (leci w górę)
y_offset    = 0   (startuje z ey=190)
fixed_move_y = -1 (dodatkowy stały dryf w górę)
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