# Logika spawnu przeciwników

## 1. Tryby Interpretacji Parametrów Eventów (eventdat)
Silnik gry Tyrian używa tzw. "przeciążania pól". Znaczenie `eventdat1-6` zmienia się całkowicie w zależności od wybranego `eventtype`.

### 1.1. Tryb SPAWN (Podstawowy)

**Typy:** 6 (Ground), 7 (Air), 10 (Left), 15 (Right), 17 (Bottom), 18 (Top)

Służy do tworzenia nowego przeciwnika na mapie.

| Pole | Nazwa w JSON | Funkcja | Opis |
| :--- | :--- | :--- | :--- |
| eventdat | enemy_id | ID Typu | Który przeciwnik z bazy danych ma się pojawić. |
| eventdat2 | x | Pozycja X | Miejsce spawnu w poziomie (0-320). |
| eventdat3 | y_vel | Dodatkowe Y | Prędkość dodawana do `ymove` wroga. |
| eventdat4 | link_num | Grupa | ID formacji (używane przez eventy globalne). |
| eventdat5 | y_offset | Offset Y | Korekta pozycji startowej góra/dół. |
| eventdat6 | fixed_move_y | Stały Ruch | Ruch jednostajny, ignorujący fizykę. |

---

### 1.2. Tryb GLOBAL MOVE (Zmiana Ruchu)

**Typ:** 19

Służy do nagłej zmiany zachowania wszystkich żyjących wrogów z konkretnej grupy (`link_num`).

| Pole | Funkcja | Opis |
| :--- | :--- | :--- |
| eventdat | Nowe X Speed | Nadpisuje aktualne `exc` (prędkość poziomą). |
| eventdat2 | Nowe Y Speed | Nadpisuje aktualne `eyc` (prędkość pionową). |
| eventdat4 | Target Group | Której grupy (`link_num`) dotyczy zmiana. |
| eventdat5 | Anim Cycle | Zmienia aktualną klatkę animacji wrogów w grupie. |
| eventdat6 | New Fixed Y | Nadpisuje wartość `fixed_move_y`. |

---

### 1.3. Tryb GLOBAL ACCEL (Zmiana Fizyki)

**Typy:** 20 (Przyspieszenie), 27 (Limity)

Pozwala zmienić parametry "silnika" wrogów w trakcie ich lotu.

| Pole | Funkcja w Typie 20 | Funkcja w Typie 27 |
| :--- | :--- | :--- |
| eventdat | Nowe xcaccel (X) | Nowe xrev (Limit X) |
| eventdat2 | Nowe ycaccel (Y) | Nowe yrev (Limit Y) |
| eventdat4 | Target Group | Target Group |

---

### 1.4. Tryb BOUNCE (Granice Ekranu)

**Typ:** 54

Definiuje linię, od której wrogowie mają się "odbijać" (jeśli ich fizyka na to pozwala).

| Pole | Funkcja | Opis |
| :--- | :--- | :--- |
| eventdat4 | Target Group | Której grupy dotyczy nowa granica. |
| eventdat6 | Y Min Bounce | Współrzędna Y, powyżej której wrogowie nie mogą polecieć. |

---

### 1.5. Podsumowanie dla programisty

Jeśli widzisz w kodzie `eventdat2`, najpierw sprawdź `eventtype`:

1. Jeśli type < 19 -> to jest `x` (Pozycja X).
2. Jeśli type == 19 -> to jest `y_vel` (Prędkość Y).
3. Jeśli type == 20 -> to jest `ycaccel` (Przyspieszenie Y).
4. Jeśli type == 27 -> to jest `yrev` (Limit Prędkości Y).

---

## 2. Mapowanie Definicji Przeciwnika (Enemy Data Mapping)

| Indeks (tup) | Pole JSON | Typ | Zmienna w C | Opis funkcjonalny |
|:---|:---|:---|:---|:---|
| tup[7] | xmove | int8 | exc | Startowa prędkość X. Bazowy wektor poziomy w momencie spawnu. |
| tup[8] | ymove | int8 | eyc | Startowa prędkość Y. Wartość bazowa, do której dodawane jest `y_vel` z eventu. |
| tup[9] | xaccel | int8 | exca | Losowe przyspieszenie poziome. Wartości -1, 1. |
| tup[10] | yaccel | int8 | eyca | Losowe przyspieszenie pionow. Wartości -1, 1. |
| tup[11] | xcaccel | int8 | excc | Przyspieszenie X. Wartość dodawana do prędkości `exc` w każdej klatce. |
| tup[12] | ycaccel | int8 | eycc | Przyspieszenie Y. Wartość dodawana do prędkości `eyc` w każdej klatce. |
| tup[42] | xrev | int8 | exrev | Limit prędkości X. Punkt, w którym następuje odwrócenie przyspieszenia `excc`. |
| tup[43] | yrev | int8 | eyrev | Limit prędkości Y. Punkt, w którym następuje odwrócenie przyspieszenia `eycc`. |
| tup[1:4] | tur | 3xByte | etur | ID Uzbrojenia. Definiuje pociski dla kierunków: dół, prawo, lewo. |
| tup[4:7] | freq | 3xByte | efreq | Szybkostrzelność. Czas (w klatkach) między kolejnymi strzałami. |
| tup[17] | armor | Byte | hp | Wytrzymałość (HP). Ilość obrażeń, jakie wróg przyjmie przed śmiercią. |
| tup[18] | esize | Byte | esize | Rozmiar. 0 = 1x1 kafelka, 1 = 2x2 kafelki (duży wróg). |

---

## 3. Mapowanie Techniczne: JSON vs Silnik Gry
Niektóre zmienne widoczne w kodzie (np. podczas debugowania) nie mają bezpośredniego odpowiednika w pliku JSON, ponieważ są wynikiem działania logiki gry:

- **`eyccadd` / `exccadd`**: Zmienne pomocnicze sterujące kierunkiem przyspieszenia. Jeśli prędkość (`eyc`) osiągnie limit (`eyrev`), silnik zmienia znak `eyccadd`, co powoduje, że wróg zaczyna hamować lub zawracać (efekt wahadła).
- **`fixedmovey`**: Wartość ta pochodzi wyłącznie z parametrów eventu poziomu (`eventdat6`) i odpowiada `fixed_move_y`.

## 4. Hierarchia Wykonywania Ruchu

W pętli głównej (JE_drawEnemy), silnik przetwarza ruch w następującej kolejności, sumując wektory na finalną pozycję ekranową `ey`:

1. Ruch Sztywny: `enemy.ey += fixedmovey` (ignoruje fizykę).
2. Ruch Fizyczny: `enemy.ey += eyc` (uwzględnia przyspieszenia i limity).
3. Ruch Środowiska: `enemy.ey += tempBackMove` (scrolling tła).

Ostateczna pozycja na ekranie to suma:
`Pozycja_Y = Pozycja_Y + fixed_move_y (stały) + eyc (fizyka) + backMove (tło)`.

---

## 5. Szczegółowy Opis Parametrów Eventów

### 5.1. `x` (eventdat2) - Pozycja Pozioma

**Typ:** int16 (signed short)  
**Zakres:** 0 - 320 (szerokość ekranu)

**Działanie w grze:**
Pozycja X w pliku `.lvl` to wartość bezwzględna, ale gra koryguje ją w zależności od mapy:

```c
// Dla zwykłych wrogów (enemyOffset = 0)
enemy.ex = eventdat2 - (mapX - 1) * 24;

// Dla wrogów naziemnych (enemyOffset = 25, 75)
enemy.ex = eventdat2 - (mapX - 1) * 24 - 12;

// Dla wrogów "top" (enemyOffset = 50)
if (background3x1)
    enemy.ex = eventdat2 - (mapX - 1) * 24 - 12;
else
    enemy.ex = eventdat2 - mapX3 * 24 - 24 * 2 + 6;
```

**Kluczowe informacje:**
- Wartość `eventdat2 = -99` ma specjalne znaczenie - gra nie modyfikuje pozycji X
- Przesunięcie zależy od typu spawnu (ground/top/sky)
- `mapX` pochodzi z nagłowka pliku `.lvl`

---

### 5.2. `y_vel` (eventdat3) - Prędkość Pionowa (z Fizyką)

**Typ:** int8 (signed char)  
**Nazwa w kodzie:** `eyc`

**Działanie:**
Prędkość pionowa podlegająca pełnej fizyce gry:

**Fizyka:**
- Przyspieszenia (`ycaccel`, `eyccadd`) modyfikują `eyc`
- Losowe przyspieszenia (`yaccel`) wpływają na `eyc`
- Odbicia od krawędzi (`yminbounce`, `ymaxbounce`) odwracają `eyc`

**Zastosowanie:**

- Lot wroga z własną prędkością
- Opadanie/spływanie wroga
- Startowa prędkość przy spawnie

---

### 5.3. `y_offset` (eventdat5) - Przesunięcie Y

**Typ:** int8 (signed char)

**Działanie w zależności od typu spawnu:**

| Typ Eventu | Działanie |
|------------|-----------|
| 6, 7, 10, 12, 15 (standardowe) | `enemy.ey += eventdat5` (dodaje do pozycji) |
| 17 (Ground Bottom) | `enemy.ey = 190 + eventdat5` (bazowa pozycja + offset) |
| 18 (Sky Bottom) | `enemy.ey = 190 + eventdat5` |
| 23 (Sky Bottom 2) | `enemy.ey = 180 + eventdat5` |
| 19 (Enemy Global Move) | Jeśli > 0: ustawia `enemycycle` (animację) |

**Zastosowanie:**

- Gęste ustawianie obiektów (bez kolizji ze sobą przy spawnie)
- Dokładne pozycjonowanie wrogów "od dołu" ekranu
- Event 19 używa tego pola do kontroli animacji

---

### 5.4. `link_num` (eventdat4) - ID Grupy/Formacji

**Typ:** uint8 (unsigned char)  
**Nazwa w kodzie:** `linknum`  
**Zakres:** 0-255

**Znaczenie wartości:**
- `0` - Brak grupy (domyślnie przy inicjalizacji)
- `1-99` - Standardowa grupa przeciwników
- `100+` - Specjalne grupy (kontynualne obrażenia)
- `255` - Specjalna grupa (wszystkie wrogowie bez grupy)

**Działanie:**

```c
// Przypisanie przy spawnie
enemy.linknum = eventRec[eventLoc-1].eventdat4;

// Inicjalizacja domyślna (JE_makeEnemy):
enemy->linknum = 0;
```

**Zastosowanie w eventach globalnych:**
Eventy globalne (typ 19-60) operują na grupach przez `link_num`:

| Event | Działanie na grupie |
|-------|---------------------|
| 19 (Global Move) | Modyfikuje prędkość grupy |
| 20 (Global Accel) | Zmienia przyspieszenie grupy |
| 24 (Global Animate) | Włącza animację dla grupy |
| 25 (Global Damage) | Zmienia HP grupy |
| 31 (Fire Override) | Zmienia częstotliwość strzelania |
| 39 (Linknum Change) | Zmienia ID grupy wrogów |
| 46, 47, 55, 57, 60 | Różne operacje na grupach |

**System dziedziczenia:**
Wrogowie wystrzeliwani przez innych (`launchtype`) dziedziczą `linknum`:

```c
if (enemy[i].launchspecial == 1 && enemy[i].linknum < 100) {
    e->linknum = enemy[i].linknum;  // Nowy wróg dostaje ten sam link_num
}
```

**Pasek bossa:**
`link_num` używany jest do przypisania paska HP bossa:

```c
for (i = 0; i < COUNTOF(boss_bar); i++)
    if (temp == boss_bar[i].link_num)
        boss_bar[i].color = 6;  // Aktualizacja koloru paska
```

---

### 5.5. `fixed_move_y` (eventdat6) - Stały Ruch Pionowy

**Typ:** int8 (signed char)  
**Nazwa w kodzie:** `fixedmovey`

**Kluczowa różnica od `y_vel`:**
Ten ruch jest **niezależny od fizyki** - jest dodawany "na sztywno" do pozycji Y.

**Działanie w głównej pętli:**

```c
// JE_drawEnemy():
enemy.ey += enemy.fixedmovey;  // Najpierw stały ruch
enemy.ex += enemy.exc;         // Potem fizyka X
enemy.ey += enemy.eyc;         // Potem fizyka Y (z przyspieszeniami, odbiciami)
```

**Zastosowanie:**
- Ruch wroga **synchronizowany ze scrollingiem tła** (backMove, backMove2, backMove3)
- Wrogowie "unosiący się" razem z tłem
- Nie podlega odbiciom od krawędzi ekranu
- Nie jest modyfikowany przez przyspieszenia

**Specjalna obsługa w eventach:**

```c
// Event 19 (Global Move) - może zresetować:
if (eventRec[eventLoc-1].eventdat6 == -99)
    enemy[i].fixedmovey = 0;

// Inne wartości nadpisują fixed_move_y
```

---

## 6. Wpływ Scrollingu Tła (backMove)

Wartości `backMove`, `backMove2`, `backMove3` kontrolują prędkość scrollingu tła i wpływają na pozycję wrogów:

| Zmienna | Wartość domyślna | Używana dla | Efekt na wroga |
|---------|-------------------|-------------|----------------|
| `backMove` | 1 | enemyOffset 25, 75 (Ground) | `enemy.ey -= backMove` przy spawnie |
| `backMove2` | 2 | enemyOffset 0 (Sky) | `enemy.ey -= backMove2` przy spawnie |
| `backMove3` | 3 | enemyOffset 50 (Top) | `enemy.ey -= backMove3` przy spawnie |

### 6.1. Zmienne Scrollingu i Ruch w Pętli

**W głównej pętli:**

```c
// Wszyscy wrogowie "unoszą się" wraz z tłem
tempBackMove = backMove (lub 0, lub backMove3 zależnie od grupy)
enemy[i].ey += tempBackMove;  // Dodawane na końcu ruchu
```

---

## 7. Eventy Globalne Modyfikujące Ruch 

| Event | Nazwa | Efekt na Y | Parametry |
|-------|-------|------------|-----------|
| 19 | Global Move | Nadpisuje `eyc` i `fixedmovey` | eventdat2 = nowy y_vel, eventdat6 = nowy fixed_move_y |
| 20 | Global Accel | Zmienia stałe przyspieszenie | eventdat2 = nowy ycaccel (→ eycc) |
| 27 | Global AccelRev | Zmienia limity prędkości | eventdat2 = nowy yrev (→ eyrev) |
| 54 | Bounce | Zmienia granice odbicia | eventdat6 = yminbounce |

---

## 8. Pozycja Y - Zależności od Typu Eventu

Pozycja startowa Y wroga jest inicjalizowana w zależności od typu eventu spawnu:

### 8.1. Standardowe Inicjalizacje Pozycji Y

| Event | enemyOffset | Bazowa pozycja Y | Formuła | Korekta przy spawnie |
|-------|-------------|------------------|---------|----------------------|
| 6 (Ground) | 25 | -28 | `ey = -28 + y_offset` | `ey -= backMove` |
| 7 (Top) | 50 | -28 | `ey = -28 + y_offset` | `ey -= backMove3` |
| 10 (Ground 2) | 75 | -28 | `ey = -28 + y_offset` | `ey -= backMove` |
| 15 (Sky) | 0 | -28 | `ey = -28 + y_offset` | `ey -= backMove2` |
| 12 (4x4 Ground) | 0/25/50/75 | -28 | zależne od eventdat6 | `ey -= backMove` |
| 17 (Ground Bottom) | 25 | 190 | `ey = 190 + y_offset` | brak |
| 18 (Sky Bottom) | 0 | 190 | `ey = 190 + y_offset` | brak |
| 23 (Sky Bottom 2) | 50 | 180 | `ey = 180 + y_offset` | brak |
| 32 (Special) | 50 | 190 | `ey = 190` (stałe) | brak |
| 56 (Ground2 Bottom) | 75 | 190 | `ey = 190` (stałe) | brak |

---

## 9. Mechanika Ruchu i Fizyka Osi Y

Dokumentacja wyjaśniająca sposób obliczania pozycji pionowej przeciwnika na podstawie fuzji danych z pliku wroga (`.json`) oraz parametrów zdarzenia (`.lvl`).

---

### 10.1. Wzór na Pozycję Pionową
W każdej klatce gry (JE_drawEnemy), ostateczna pozycja `Y` przeciwnika jest sumą czterech wektorów:

$$Y_{nowe} = Y_{stare} + fixed\_move\_y + eyc + backMove$$

**Składniki równania:**

- **`fixed_move_y` (Stały Ruch):** Wartość dodawana "na sztywno", niezależna od fizyki i odbić.
- **`eyc` (Prędkość Fizyczna):** Wektor podlegający przyspieszeniu, limitom i odbiciom od krawędzi.
- **`backMove` (Scrolling):** Prędkość przesuwania tła, która sprawia, że wrogowie "płyną" wraz z mapą.

---

### 10.2. Inicjalizacja Prędkości (Faza Spawnu)
Gdy przeciwnik pojawia się na mapie, silnik ustala jego początkową prędkość fizyczną `eyc`:

$$eyc = ymove + y\_vel$$

- **`ymove` (tup[8]):** Bazowa prędkość zdefiniowana w profilu wroga.
- **`y_vel` (eventdat3):** Modyfikator prędkości ze zdarzenia w pliku poziomu.
  - *Uwaga:* Wartość `y_vel = -99` w evencie oznacza zignorowanie modyfikatora i użycie tylko bazowego `ymove`.

---

### 10.3. System Przyspieszenia i Limitów
Jeśli przeciwnik posiada zdefiniowane przyspieszenie, jego prędkość `eyc` zmienia się dynamicznie w każdej klatce:

1. Aktualizacja prędkości: Do `eyc` dodawane jest stałe przyspieszenie `ycaccel` (tup[12]).
2. Kontrola limitu (`yrev`): Silnik sprawdza, czy `eyc` osiągnęło limit prędkości zdefiniowany w `yrev` (tup[43]).
3. Oscylacja: Po osiągnięciu limitu `yrev`, kierunek przyspieszenia zostaje odwrócony, co tworzy efekt wahadła lub płynnego hamowania i zawracania.

---

### 11. Przykłady Konfiguracji

#### Wróg Naziemny (Stacjonarny)

`fixed_move_y = 0` oraz `eyc = 0`. Wróg porusza się wyłącznie o wartość `backMove` tła.

#### Szybki Atak z Dołu

Event typu `17` (Bottom) z ujemnym `y_vel` (np. `-5`). Wróg wystrzeliwuje w górę ekranu, sumując swoją prędkość z prędkością tła.

#### Stały Dryf

Ustawienie `fixed_move_y` na wartość dodatnią przy `eyc = 0`. Wróg przesuwa się jednostajnie w dół, wyprzedzając scrolling tła bez względu na fizykę.

---

## 12. Format Unpack w Pythonie

```python
# Struktura 11 bajtów w little-endian
event = struct.unpack('<H B h h b b b B', event_data)

# Mapowanie:
eventtime    = event[0]  # H - uint16
eventtype    = event[1]  # B - uint8
eventdat     = event[2]  # h - int16 (enemy_id)
eventdat2    = event[3]  # h - int16 (x)
eventdat3    = event[4]  # b - int8  (y_vel)
eventdat5    = event[5]  # b - int8  (y_offset)
eventdat6    = event[6]  # b - int8  (fixed_move_y)
eventdat4    = event[7]  # B - uint8 (link_num)
```

---

## 13. Wartości Specjalne

| Pole | Wartość specjalna | Znaczenie |
|------|-------------------|-----------|
| `x` | `-99` | Nie modyfikuj pozycji X |
| `y_vel` | `-99` | Nie modyfikuj prędkości Y |
| `fixed_move_y` | `-99` | Zresetuj stały ruch do 0 |
| `link_num` | `0` | Brak grupy (domyślnie) |
| `link_num` | `255` | Wszystkie wrogowie bez grupy |
---  

# Symulacja Matematyczna Ruchu Przeciwnika (Oś Y)

Dokumentacja przedstawia proces obliczeniowy pozycji przeciwnika od momentu spawnu do pierwszej klatki aktualizacji, uwzględniając fizykę, akcelerację oraz scrolling.

## 1. Dane Wejściowe (Parametry)

### A. Dane z pliku przeciwnika (.json)
* **`ymove` (tup[8])**: `2` (Bazowa prędkość pionowa)
* **`ycaccel` (tup[12])**: `1` (Stałe przyspieszenie pionowe - `eycc`)
* **`yaccel` (tup[10])**: `1` (Kierunek losowego przyspieszenia - `eyca`)
* **`yrev` (tup[43])**: `10` (Limit prędkości pionowej - `eyrev`)

### B. Dane z parametrów zdarzenia (.lvl)
* **`eventtype`**: `15` (Sky Enemy - przeciwnik powietrzny)
* **`y_vel` (eventdat3)**: `3` (Modyfikator prędkości pionowej)
* **`fixed_move_y` (eventdat6)**: `1` (Stały ruch niezależny od fizyki)
* **`y_offset` (eventdat5)**: `0` (Przesunięcie startowe)

### C. Dane środowiskowe
* **`backMove2`**: `2` (Prędkość scrollingu dla jednostek typu Sky)


## 2. Klatka 0: Inicjalizacja (Spawn)

W momencie pojawienia się wroga na mapie, silnik wykonuje pierwsze przypisania wartości startowych.

**Wzór na prędkość startową ($eyc_{start}$):**  
eyc = ymove + y\_vel

**Podstawienie:**  
eyc = 2 + 3 = 5

**Wzór na pozycję startową ($ey_{start}$):**  
ey = -28 + y\_offset - backMove2

**Podstawienie:**  
ey = -28 + 0 - 2 = -30


## 3. Klatka 1: Pętla aktualizacji (Update)

W tej fazie silnik aktualizuje prędkość fizyczną, a następnie wyznacza nową pozycję na ekranie.

### Krok A: Aktualizacja prędkości fizycznej ($eyc$)
Silnik dodaje do aktualnej prędkości przyspieszenie stałe oraz (opcjonalnie) losowe szarpnięcie.

**Wzór:**  
eyc_{nowe} = eyc_{stare} + ycaccel + yaccel

**Podstawienie:**  
eyc_{nowe} = 5 + 1 + 1 = 7

### Krok B: Obliczenie nowej pozycji ($ey$)
Silnik sumuje wszystkie wektory ruchu zgodnie z hierarchią wykonywania.

**Wzór:**  
ey_{nowe} = ey_{stare} + fixed\_move\_y + eyc_{nowe} + tempBackMove

**Podstawienie:**  
ey_{nowe} = -30 + 1 + 7 + 2 = -20


## 4. Podsumowanie Stanu po 1 Klatce

| Parametr | Wartość | Opis |
| :--- | :--- | :--- |
| **$eyc$** | `7` | Aktualna prędkość fizyczna (dąży do `yrev` = 10) |
| **$ey$** | `-20` | Aktualna pozycja pionowa na ekranie |

**Logika dalszego ruchu:**
W kolejnych klatkach prędkość `eyc` będzie rosnąć o wartość `ycaccel`. Gdy osiągnie limit `10`, silnik odwróci znak przyspieszenia, co spowoduje hamowanie i ewentualny ruch w górę (fizycznie), przy jednoczesnym stałym spychaniu w dół przez `fixed_move_y` i `tempBackMove`.