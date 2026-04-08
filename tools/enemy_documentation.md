# Dokumentacja Pól Wroga (Enemy Fields)

Plik zawiera wyjaśnienie wszystkich pól struktury enemies `enemies.json`.
Dokumentacja zweryfikowana na podstawie kodu źródłowego `tyrian2.c` (OpenTyrian).

---

## Podstawowe Parametry

### `ani` (tup[0])
- **Typ:** Byte
- **Opis:** Bazowy indeks animacji wroga — numer ostatniej klatki w cyklu animacji
- **Wartości:** Różne w zależności od wroga
- **Mapowanie:** `enemy->ani = enemyDat[eDatI].ani`
- **Uwaga:** Używany jako granica górna w pętli animacji (`enemycycle > ani → reset do animin`)

---

## System Strzelania

### `tur` (tup[1:4])
- **Typ:** Lista 3 bajtów [down, right, left]
- **Opis:** ID broni/turretów wroga w trzech kierunkach
- **Zaobserwowane wartości:**
  - `[0, 0, 0]` - brak broni (36 wrogów)
  - `[145, 146, 0]` - strzela w dół i w prawo
  - `[116, 116, 116]` - strzela we wszystkich kierunkach
  - `[24, 0, 0]`, `[59, 0, 0]`, `[144, 0, 0]`, `[154, 0, 0]`, `[115, 115, 115]` - inne konfiguracje
- **Wartości specjalne ID broni:**
  - `252` - Savara Boss DualMissile (specjalna eksplozja, nie pocisk)
  - `251` - Suck-O-Magnet (przyciąga gracza)
  - `253` - ShortRange Magnet prawo (odpycha gracza w prawo)
  - `254` - ShortRange Magnet lewo (odpycha gracza w lewo)
  - `255` - Magneto RePulse (odpychanie radialnie)
- **Uwaga:** Tylko 7 wrogów z pośród 43 (na level1) ma bronie. Na wyższych poziomach trudności czas ładowania (`eshotwait`) jest automatycznie dzielony przez 2 (hard) lub 4 (maniacal+)

### `freq` (tup[4:7])
- **Typ:** Lista 3 bajtów [down, right, left]
- **Opis:** Częstotliwość strzelania — liczba klatek między strzałami (niższa = szybsze)
- **Zaobserwowane wartości:** 20 - 120
- **Przykłady:**
  - `[40, 41, 0]` - strzela w dół (40) i prawo (41) z różną częstotliwością
  - `[80, 81, 82]` - strzela we wszystkich kierunkach
  - `[0, 0, 0]` - brak strzelania
- **Inicjalizacja `eshotwait`:** Przy spawnie: slot `252` → `eshotwait = 1`, inne niezerowe → `eshotwait = 20`, brak (`tur = 0`) → `eshotwait = 255`

---

## Ruch i Prędkość

### `xmove` (tup[7])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Startowa prędkość pozioma (X) przypisywana przy spawnie
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Mapowanie:** `enemy->exc = enemyDat[eDatI].xmove`

### `ymove` (tup[8])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Startowa prędkość pionowa (Y) przypisywana przy spawnie
- **Zaobserwowane wartości:** 0 lub 2
- **Mapowanie:** `enemy->eyc = enemyDat[eDatI].ymove`
- **Uwaga:** Do tej wartości może być dodany modyfikator `y_vel` z parametru eventu (`eventdat3`). Jeśli `eventdat3 == -99`, modyfikator jest ignorowany i używane jest tylko `ymove`.

### `xaccel` (tup[9])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Parametr losowego przyspieszenia poziomego, kodujący jednocześnie kierunek i próg aktywacji
- **Działanie w kodzie:**
  ```c
  // Warunek aktywacji losowego przyspieszenia:
  if (enemy[i].xaccel && enemy[i].xaccel - 89u > mt_rand() % 11)
  {
      // Wróg przyspiesza w kierunku gracza z limitem (xaccel - 89)
  }
  // Kierunek (exca) wyznaczany przy spawnie:
  enemy->exca = (enemy->xaccel > 0) ? 1 : -1;
  ```
- **Interpretacja wartości:**
  - `0` - brak losowego przyspieszenia
  - `90–100` - aktywne losowe przyspieszenie; limit prędkości = `xaccel - 89` (czyli 1–11)
  - Znak wartości (`+`/`-`) → `exca` = kierunek (`+1` lub `-1`)
- **Uwaga:** Wartości `1`/`-1` to zmienna wynikowa `exca`, nie samo pole `xaccel`. Pole w danych wroga przechowuje wartości 90–100 lub ich ujemne odpowiedniki.

### `yaccel` (tup[10])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Parametr losowego przyspieszenia pionowego — analogiczne do `xaccel`
- **Działanie:** Identyczne jak `xaccel`, ale na osi Y. `eyca = (yaccel > 0) ? 1 : -1`

### `xcaccel` (tup[11])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Stałe przyspieszenie poziome (silnik wahadłowy)
- **Zaobserwowane wartości:** 0 lub 125
- **Mapowanie:** `enemy->excc = enemyDat[eDatI].xcaccel`
- **Działanie:**
  - Przy spawnie: `exccw = abs(excc)`, `exccwmax = exccw`, `exccadd = (excc > 0) ? 1 : -1`
  - W każdej klatce: odlicza `exccw`; gdy osiągnie 0 → dodaje `exccadd` do `exc`, resetuje `exccw = exccwmax`
  - Gdy `exc == exrev` → odwraca znaki `excc`, `exrev`, `exccadd` (efekt wahadła)
  - **Okres wahadła zależy od wartości `xcaccel`** — im większy `xcaccel`, tym wolniejsze wahadło (dłuższe odliczanie)
- **Uwaga:** `xcaccel = 0` wyłącza silnik wahadłowy całkowicie

### `ycaccel` (tup[12])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Stałe przyspieszenie pionowe — analogiczne do `xcaccel`
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Mapowanie:** `enemy->eycc = enemyDat[eDatI].ycaccel`

---

## Pozycja Startowa

### `startx` (tup[13])
- **Typ:** Short (16-bit)
- **Opis:** Bazowa pozycja startowa X
- **Zaobserwowane wartości:** 0 lub 130
- **Działanie:** Środkowa pozycja, wokół której wróg może się pojawić (zależnie od `startxc`)
- **Uwaga:** Pozycja X przy spawnie jest dodatkowo korygowana przez parametr `x` z eventu (`eventdat2`)

### `starty` (tup[14])
- **Typ:** Short (16-bit)
- **Opis:** Bazowa pozycja startowa Y
- **Zaobserwowane wartości:** 0 lub -13

### `startxc` (tup[15])
- **Typ:** Byte
- **Opis:** Promień losowego odchylenia od pozycji X
- **Zaobserwowane wartości:** 0 lub 125
- **Formuła (z kodu):**
  ```c
  if (startxc != 0)
      enemy->ex = startx + (mt_rand() % (startxc * 2)) - startxc + 1;
  else
      enemy->ex = startx + 1;
  ```
  - `0` - wróg pojawia się dokładnie w `startx + 1`
  - `125` - wróg pojawia się w zakresie `[startx - 124, startx + 126]`

### `startyc` (tup[16])
- **Typ:** Byte
- **Opis:** Promień losowego odchylenia od pozycji Y
- **Zaobserwowane wartości:** 0
- **Działanie:** Analogiczne do `startxc`

---

## Statystyki

### `armor` (tup[17])
- **Typ:** Byte
- **Opis:** Wytrzymałość wroga (HP)
- **Zaobserwowane wartości:** 0 - 255
- **Interpretacja wartości:**
  - `0` — **SCORE ITEM** (kolektible, np. klejnot, powerup): wróg jest nieśmiertelny (`armorleft = 255`), znika gdy wyjdzie poza ekran. Jeśli `evalue != 0`, ustawiana jest flaga `scoreitem = true`.
  - `1–254` — normalny wróg; rzeczywiste HP są skalowane przez poziom trudności (patrz niżej)
  - `255` — specjalny wróg nieśmiertelny (boss itp.); wartość przekazywana bez skalowania
- **Skalowanie przez poziom trudności** (dla wartości 1–254):
  | Poziom trudności | Mnożnik HP |
  |---|---|
  | Wimp / -1 | ×0.5 + 1 |
  | Easy | ×0.75 + 1 |
  | Normal | ×1.0 (brak zmian) |
  | Hard | ×1.2 |
  | Impossible | ×1.5 |
  | Insanity | ×1.8 |
  | Suicide | ×2.0 |
  | Maniacal | ×3.0 |
  | Zinglon | ×4.0 |
  | Nortaneous / 10 | ×8.0 |
  
  Wynik jest obcinany do maksymalnie 254.

### `esize` (tup[18])
- **Typ:** Byte
- **Opis:** Rozmiar wroga (flaga wielkości)
- **Zaobserwowane wartości:** 0 lub 1
- **Znaczenie:**
  - `0` - zwykły wróg (1×1 sprite)
  - `1` - duży wróg (2×2 sprite — składa się z 4 części)
- **Efekty dla `esize=1`:**
  - Rysowany jako 4 części z przesunięciami: `(-6,-7)`, `(+6,-7)`, `(-6,+7)`, `(+6,+7)` względem centrum
  - Indeksy sprite'ów: `egr[cycle-1]+0`, `+1`, `+19`, `+20` (nie +0,+1,+2,+3!)
  - Inny typ eksplozji (`JE_setupExplosionLarge`)

---

## Grafika

### `egraphic` (tup[19:39])
- **Typ:** Lista 20 wartości 16-bitowych (unsigned short)
- **Opis:** ID sprite'ów dla 20 klatek animacji wroga
- **Rozmiar:** 40 bajtów (20 klatek × 2 bajty)
- **Uwaga:** Wartość `999` w klatce powoduje natychmiastowe usunięcie wroga z ekranu (`goto enemy_gone`)

---

## Pozostałe Parametry

### `explosiontype` (tup[39])
- **Typ:** Byte
- **Opis:** Pole dwuznaczne — koduje jednocześnie **typ podłoża** i **numer eksplozji**
- **Dekodowanie w kodzie:**
  ```c
  enemy->enemyground = (enemyDat[eDatI].explosiontype & 1) == 0;
  enemy->explonum    = enemyDat[eDatI].explosiontype >> 1;
  ```
  - **Bit 0 (LSB):** `0` → wróg powietrzny (`enemyground = true`), `1` → wróg naziemny (`enemyground = false`)
  - **Bity 1–7:** numer eksplozji (`explonum = explosiontype >> 1`)
- **Zaobserwowane wartości:** 5, 6, 25, 26, 27, 28, 35

### `animate` (tup[40])
- **Typ:** Byte
- **Opis:** Tryb animacji wroga
- **Zaobserwowane wartości:** 0, 1, 2
- **Znaczenie i inicjalizacja:**
  | Wartość | Tryb | `enemycycle` | `aniactive` | `animax` | `aniwhenfire` |
  |---|---|---|---|---|---|
  | `0` | Brak animacji | 1 | 0 | 0 | 0 |
  | `1` | Zawsze aktywna | 0 | 1 | 0 | 0 |
  | `2` | Tylko przy strzale | 1 | 2 | `ani` | 2 |

### `shapebank` (tup[41])
- **Typ:** Byte
- **Opis:** Bank sprite'ów (plik z grafiką)
- **Zaobserwowane wartości:** 8, 17, 20, 23
- **Opis:** Wskazuje, z którego pliku `.shp` pobierać grafikę
- **Wartości specjalne:**
  - `21` → `spriteSheet11` (Coins & Gems)
  - `26` → `spriteSheet10` (Two-Player Stuff)
  - Inne → wyszukiwane w tablicy `enemySpriteSheets[0..3]`

### `xrev` (tup[42])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Limit prędkości X — punkt zwrotny silnika wahadłowego `xcaccel`
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Konwersja przy spawnie:**
  ```c
  if (xrev == 0)   enemy->exrev = 100;
  if (xrev == -99) enemy->exrev = 0;    // brak limitu (wahadło wyłączone)
  else             enemy->exrev = xrev; // wartość dosłowna
  ```
- **Efekt:** Gdy `exc` osiągnie `exrev`, silnik odwraca znaki `excc`, `exrev` i `exccadd`, tworząc efekt wahadła

### `yrev` (tup[43])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Limit prędkości Y — analogiczne do `xrev`
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Konwersja:** Identyczna jak `xrev`, wynik trafia do `enemy->eyrev`

### `dgr` (tup[44])
- **Typ:** Word (16-bit, unsigned short)
- **Opis:** Typ/klasa wroga (enemy type ID) używany przez system zdarzeń i AI
- **Zaobserwowane wartości:** 2 - 207
- **Mapowanie:** `enemy->edgr = enemyDat[eDatI].dgr`

### `dlevel` (tup[45])
- **Typ:** Short (16-bit, signed)
- **Opis:** Poziom trudności, na którym wróg się pojawia
- **Zaobserwowane wartości:** -1, 0, 10
- **Mapowanie:** `enemy->edlevel = enemyDat[eDatI].dlevel`

### `dani` (tup[46])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Animacja przy otrzymaniu obrażeń / flaga zniszczenia
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Znaczenie:**
  - `< 0` → przy spawnie wróg jest od razu oznaczony jako `edamaged = true` (nieaktywny, nie strzela, nie jest rysowany normalnie)
  - `0` → brak specjalnej animacji
- **Mapowanie:** `enemy->edamaged = (enemyDat[eDatI].dani < 0)`, `enemy->edani = enemyDat[eDatI].dani`

### `elaunchfreq` (tup[47])
- **Typ:** Byte
- **Opis:** Częstotliwość wystrzeliwania nowych wrogów (w klatkach)
- **Zaobserwowane wartości:** 0, 40, 60
- **Działanie:** Co `elaunchfreq` klatek wróg tworzy nowego wroga typu `elaunchtype`
- **Uwaga:** `0` oznacza brak wystrzeliwania. Przy spawnie `launchwait = elaunchfreq` (pierwsze wystrzelenie po pełnym cyklu)

### `elaunchtype` (tup[48])
- **Typ:** Word (16-bit, unsigned short)
- **Opis:** Typ wroga do wystrzelenia + opcjonalne specjalne zachowanie przy launchu
- **Zaobserwowane wartości:** 0, 463, 543, 544
- **Dekodowanie w kodzie:**
  ```c
  enemy->launchtype    = elaunchtype % 1000;  // ID wroga do stworzenia
  enemy->launchspecial = elaunchtype / 1000;  // tryb specjalny
  ```
- **`launchspecial`:**
  - `0` — standardowe wystrzelenie
  - `1` — wróg wystrzeliwuje potomka tylko gdy jest w tej samej linii poziomej co gracz (`abs(ey - player.y) <= 5`)
- **Przykład:** `elaunchtype = 1463` → tworzy wroga #463, `launchspecial = 1`
- **Kierowanie wystrzelonym wrogiem:**
  - Jeśli `launchtype > 90` → losowe rozrzucenie (`± (launchtype-90)*2` pikseli w osi X)
  - Jeśli `launchtype <= 90` → wystrzelony wróg jest nakierowany na gracza z prędkością `launchtype`

### `value` (tup[49])
- **Typ:** Short (16-bit, signed — `h` w struct)
- **Opis:** Bazowe punkty za zniszczenie wroga
- **Zaobserwowane wartości:** 0 - 10020
- **Skalowanie przez poziom trudności** (dla wartości 2–9999):
  | Poziom | Mnożnik |
  |---|---|
  | Wimp / -1 | ×0.75 |
  | Easy / Normal | ×1.0 |
  | Hard | ×1.125 |
  | Impossible | ×1.5 |
  | Insanity | ×2.0 |
  | Suicide | ×2.5 |
  | Maniacal / Zinglon | ×4.0 |
  | Nortaneous / 10 | ×8.0 |
  
  Wynik jest obcinany do maksymalnie 10000.
- **Wartości specjalne:** `0` lub `1` → bez skalowania, `≥ 10000` → bez skalowania (przekazywane dosłownie)

### `enemydie` (tup[50])
- **Typ:** Byte (w struct: `H` — unsigned short, 2 bajty)
- **Opis:** Zachowanie przy śmierci wroga
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Mapowanie:** `enemy->enemydie = enemyDat[eDatI].eenemydie`
- **Uwaga:** Pole w formacie binarnym zajmuje 2 bajty (`H`), mimo że wartości mieszczą się w bajcie

---

## Pola Runtime (nie w danych wroga, obliczane przez silnik)

Poniższe zmienne nie mają bezpośredniego odpowiednika w JSON/danych wroga — są wyznaczane przez silnik przy spawnie lub w trakcie gry:

| Zmienna | Źródło | Opis |
|---|---|---|
| `exca` | `(xaccel > 0) ? 1 : -1` | Kierunek losowego przyspieszenia X |
| `eyca` | `(yaccel > 0) ? 1 : -1` | Kierunek losowego przyspieszenia Y |
| `exccadd` | `(excc > 0) ? 1 : -1` | Kierunek przyrostu prędkości w silniku wahadłowym X |
| `eyccadd` | `(eycc > 0) ? 1 : -1` | Kierunek przyrostu prędkości w silniku wahadłowym Y |
| `exccw` | `abs(excc)` | Odliczanie klatek do kolejnego przyrostu prędkości X |
| `eyccw` | `abs(eycc)` | Odliczanie klatek do kolejnego przyrostu prędkości Y |
| `exccwmax` | `abs(excc)` | Maksimum odliczania (stałe przez całą grę) |
| `eyccwmax` | `abs(eycc)` | Maksimum odliczania (stałe przez całą grę) |
| `fixedmovey` | `eventdat6` z eventu | Stały ruch Y niezależny od fizyki (inicjowany jako 0 przy spawnie) |
| `scoreitem` | `armor == 0 && evalue != 0` | Flaga: czy to kolektible (nie liczy się do ratio zniszczeń) |
| `enemyground` | `(explosiontype & 1) == 0` | Flaga: czy wróg jest powietrzny |
| `explonum` | `explosiontype >> 1` | Numer eksplozji |
| `launchspecial` | `elaunchtype / 1000` | Tryb specjalny launch |
| `launchtype` | `elaunchtype % 1000` | ID wystrzelwanego wroga |

---

## Podsumowanie Relacji

### System Przyspieszenia Wahadłowego (xcaccel/ycaccel):
```
Przy spawnie:
  excc    = xcaccel
  exccw   = abs(xcaccel)        ← odliczanie (zależy od xcaccel)
  exccwmax = abs(xcaccel)       ← maksimum odliczania (stałe)
  exccadd = (xcaccel > 0) ? 1 : -1

Każda klatka:
  1. --exccw
  2. Gdy exccw == 0:
     a. exc += exccadd
     b. exccw = exccwmax        ← reset odliczania
     c. Jeśli exc == exrev:
        excc    = -excc          ← odwróć kierunek
        exrev   = -exrev
        exccadd = -exccadd       ← efekt wahadła
```

### System Pozycji Startowej:
```
if (startxc != 0)
    ex = startx + (rand() % (startxc * 2)) - startxc + 1
else
    ex = startx + 1

Analogicznie dla Y z startyc.
```

### System Strzelania:
```
tur[0] → broń w dół   + freq[0] → częstotliwość
tur[1] → broń w prawo + freq[1] → częstotliwość
tur[2] → broń w lewo  + freq[2] → częstotliwość

Modyfikacja wg trudności:
  Hard:     eshotwait /= 2 + 1
  Maniacal+: eshotwait /= 4 + 1
```

### Armor i Score Items:
```
armor == 0  → score item (nieśmiertelny, znika poza ekranem)
armor == 255 → nieśmiertelny wróg (np. boss), brak skalowania
armor 1-254 → normalny wróg, HP skalowane przez trudność (max 254)
```

---

## Format Binarny (struct_fmt)

```python
struct_fmt = "<B 3B 3B bbbbbb hh bb BB 20H B BB bb H h b B H h H"
```

Rozkład:
- `B`    — ani (1 bajt)
- `3B`   — tur[3] (3 bajty)
- `3B`   — freq[3] (3 bajty)
- `bbbbbb` — xmove, ymove, xaccel, yaccel, xcaccel, ycaccel (6 bajtów)
- `hh`   — startx, starty (4 bajty — 2×signed short)
- `bb`   — startxc, startyc (2 bajty)
- `BB`   — armor, esize (2 bajty)
- `20H`  — egraphic[20] (40 bajtów — 20×unsigned short)
- `B`    — explosiontype (1 bajt)
- `BB`   — animate, shapebank (2 bajty)
- `bb`   — xrev, yrev (2 bajty ze znakiem)
- `H`    — dgr (2 bajty — unsigned short)
- `h`    — dlevel (2 bajty — signed short)
- `b`    — dani (1 bajt ze znakiem)
- `B`    — elaunchfreq (1 bajt)
- `H`    — elaunchtype (2 bajty — unsigned short)
- `h`    — value (2 bajty — signed short)
- `H`    — enemydie (2 bajty — unsigned short)

**Całkowity rozmiar:** 59 bajtów na wroga