# Dokumentacja Pól Wroga (Enemy Fields)

Plik zawiera wyjaśnienie wszystkich pól struktury wroga używanych w `enemies_lvl1.json`.

---

## Podstawowe Parametry

### `ani` (tup[0])
- **Typ:** Byte
- **Opis:** Bazowy indeks animacji wroga
- **Wartości:** Różne w zależności od wroga

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
- **Uwaga:** Tylko 7 wrogów na 43 ma bronie

### `freq` (tup[4:7])
- **Typ:** Lista 3 bajtów [down, right, left]
- **Opis:** Częstotliwość strzelania (niższa wartość = szybsze strzelanie)
- **Zaobserwowane wartości:** 20 - 120
- **Przykłady:**
  - `[40, 41, 0]` - strzela w dół (40) i prawo (41) z różną częstotliwością
  - `[80, 81, 82]` - strzela we wszystkich kierunkach
  - `[0, 0, 0]` - brak strzelania

---

## Ruch i Prędkość

### `xmove` (tup[7])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Aktualna prędkość pozioma (X)
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Mapowanie:** `enemy->exc = enemyDat[eDatI].xmove`

### `ymove` (tup[8])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Aktualna prędkość pionowa (Y)
- **Zaobserwowane wartości:** 0 lub 2

### `xaccel` (tup[9])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Losowe przyspieszenie poziome
- **Wartości:** 1 lub -1 (w kodzie: `(xaccel > 0) ? 1 : -1`)
- **Działanie:** Określa kierunek losowego przyspieszenia

### `yaccel` (tup[10])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Losowe przyspieszenie pionowe
- **Wartości:** 1 lub -1

### `xcaccel` (tup[11])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Stałe przyspieszenie poziome
- **Zaobserwowane wartości:** 0 lub 125
- **Działanie:** Wartość dodawana do prędkości co klatkę
- **Mapowanie:** `enemy->excc = enemyDat[eDatI].xcaccel`

### `ycaccel` (tup[12])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Stałe przyspieszenie pionowe
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)

---

## Pozycja Startowa

### `startx` (tup[13])
- **Typ:** Short (16-bit)
- **Opis:** Bazowa pozycja startowa X
- **Zaobserwowane wartości:** 0 lub 130
- **Działanie:** Środkowa pozycja, wokół której wróg może się pojawić

### `starty` (tup[14])
- **Typ:** Short (16-bit)
- **Opis:** Bazowa pozycja startowa Y
- **Zaobserwowane wartości:** 0 lub -13

### `startxc` (tup[15])
- **Typ:** Byte
- **Opis:** Promień losowego odchylenia od pozycji X
- **Zaobserwowane wartości:** 0 lub 125
- **Działanie:** 
  - `0` - wróg pojawia się dokładnie w `startx`
  - `125` - wróg pojawia się w `startx + random(-125, +125)`
- **Formuła:** `startx + (random() % (startxc * 2)) - startxc + 1`

### `startyc` (tup[16])
- **Typ:** Byte
- **Opis:** Promień losowego odchylenia od pozycji Y
- **Zaobserwowane wartości:** 0
- **Działanie:** Analogiczne do `startxc`

---

## Statystyki

### `armor` (tup[17])
- **Typ:** Byte
- **Opis:** Punkty życia (HP) wroga
- **Zaobserwowane wartości:** 0 - 255
- **Uwaga:** Wartość 0 oznacza wroga, który ginie od jednego trafienia

### `esize` (tup[18])
- **Typ:** Byte
- **Opis:** Rozmiar wroga (flaga wielkości)
- **Zaobserwowane wartości:** 0 lub 1
- **Znaczenie:**
  - `0` - zwykły wróg (1x1 sprite)
  - `1` - duży wróg (2x2 sprite - składa się z 4 części)
- **Efekty:**
  - Duży wróg (`esize=1`) ma inną eksplozję (`JE_setupExplosionLarge`)
  - Duży wróg rysowany jest jako 4 części: górna-lewa, górna-prawa, dolna-lewa, dolna-prawa

---

## Grafika

### `egraphic` (tup[19:39])
- **Typ:** Lista 20 wartości 16-bitowych (unsigned short)
- **Opis:** ID sprite'ów dla 20 klatek animacji wroga
- **Rozmiar:** 40 bajtów (20 klatek × 2 bajty)
- **Uwaga:** To tutaj znajdują się numery kafelków, z których składa się obraz wroga

---

## Pozostałe Parametry

### `explosiontype` (tup[39])
- **Typ:** Byte
- **Opis:** Typ eksplozji przy zniszczeniu wroga
- **Zaobserwowane wartości:** 5, 6, 25, 26, 27, 28, 35

### `animate` (tup[40])
- **Typ:** Byte
- **Opis:** Tryb animacji wroga
- **Zaobserwowane wartości:** 0, 1, 2
- **Znaczenie:**
  - `0` - brak animacji
  - `1` - animacja zawsze aktywna
  - `2` - animacja tylko podczas strzelania

### `shapebank` (tup[41])
- **Typ:** Byte
- **Opis:** Bank sprite'ów (plik z grafiką)
- **Zaobserwowane wartości:** 8, 17, 20, 23
- **Opis:** Wskazuje, z którego pliku `.shp` pobierać grafikę

### `xrev` (tup[42])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Docelowa prędkość X (limit prędkości)
- **Zaobserwowane wartości:** 0 (wszystkie wrogi)
- **Działanie:**
  - `0` - domyślnie 100
  - `-99` - brak limitu (0)
  - inne - wartość limitu
- **Efekt:** Wróg przyspiesza do tej prędkości, potem zwalnia (wahadło)

### `yrev` (tup[43])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Docelowa prędkość Y (limit prędkości)
- **Zaobserwowane wartości:** 0 (wszystkie wrogi)

### `dgr` (tup[44])
- **Typ:** Word (16-bit)
- **Opis:** Typ/klasa wroga (enemy type ID)
- **Zaobserwowane wartości:** 2 - 207
- **Znaczenie:** Identyfikator typu wroga używany w systemie gry

### `dlevel` (tup[45])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Poziom trudności
- **Zaobserwowane wartości:** -1, 0, 10
- **Znaczenie:** Określa na jakim poziomie trudności wróg się pojawia

### `dani` (tup[46])
- **Typ:** Bajt ze znakiem (signed byte)
- **Opis:** Animacja przy otrzymaniu obrażeń
- **Zaobserwowane wartości:** 0 (wszystkie wrogi)
- **Znaczenie:**
  - `< 0` - wróg jest oznaczony jako `edamaged`
  - `0` - brak specjalnej animacji

### `elaunchfreq` (tup[47])
- **Typ:** Byte
- **Opis:** Częstotliwość wystrzeliwania nowych wrogów
- **Zaobserwowane wartości:** 0, 40, 60
- **Działanie:** Co ile klatek wróg wystrzeliwuje nowego wroga
- **Uwaga:** `0` oznacza brak wystrzeliwania

### `elaunchtype` (tup[48])
- **Typ:** Word (16-bit)
- **Opis:** Typ wroga do wystrzelenia
- **Zaobserwowane wartości:** 0, 463, 543, 544
- **Działanie:** ID wroga, który zostaje stworzony przez tego wroga

### `value` (tup[49])
- **Typ:** Word (16-bit)
- **Opis:** Punkty za zniszczenie wroga
- **Zaobserwowane wartości:** 0 - 10020
- **Znaczenie:** Ilość punktów dodawanych do wyniku gracza po zniszczeniu

### `enemydie` (tup[50])
- **Typ:** Byte
- **Opis:** ZACHOWANIE PRZY ŚMIERCI (flaga)
- **Zaobserwowane wartości:** 0 (wszystkie wrogi w level 1)
- **Znaczenie:** Określa specjalne zachowanie przy śmierci (np. czy znika od razu)

---

## Podsumowanie Relacji

### System Przyspieszenia:
```
xcaccel → excc (stałe przyspieszenie)
xrev → exrev (docelowa prędkość)

Loop:
1. exc += exccadd (przyspieszanie)
2. if exc == exrev → odwróć przyspieszenie
3. Wróg przyspiesza do xrev, potem zwalnia do -xrev
```

### System Pozycji Startowej:
```
startx + random(-startxc, +startxc) → pozycja X wroga
starty + random(-startyc, +startyc) → pozycja Y wroga
```

### System Strzelania:
```
tur[0] → broń w dół + freq[0] → częstotliwość
tur[1] → broń w prawo + freq[1] → częstotliwość  
tur[2] → broń w lewo + freq[2] → częstotliwość
```

---

## Format Binarny (struct_fmt)

```python
struct_fmt = "<B 3B 3B bbbbbb hh bb BB 20H B BB bb H b b B H h H"
```

Rozkład:
- `B` - ani (1 bajt)
- `3B` - tur[3] (3 bajty)
- `3B` - freq[3] (3 bajty)
- `bbbbbb` - xmove, ymove, xaccel, yaccel, xcaccel, ycaccel (6 bajtów)
- `hh` - startx, starty (4 bajty - 2×short)
- `bb` - startxc, startyc (2 bajty)
- `BB` - armor, esize (2 bajty)
- `20H` - egraphic[20] (40 bajtów - 20×unsigned short)
- `B` - explosiontype (1 bajt)
- `BB` - animate, shapebank (2 bajty)
- `bb` - xrev, yrev (2 bajty ze znakiem)
- `H` - dgr (2 bajty - unsigned short)
- `h` - dlevel (2 bajty - signed short)
- `b` - dani (1 bajt ze znakiem)
- `B` - elaunchfreq (1 bajt)
- `H` - elaunchtype (2 bajty)
- `h` - value (2 bajty ze znakiem)
- `H` - enemydie (2 bajty)

**Całkowity rozmiar:** 59 bajtów na wroga
