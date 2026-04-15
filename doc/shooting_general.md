# System Strzelania w Tyrian

Dokumentacja systemu strzelania, struktur broni i mechanik pocisków w grze Tyrian.

---

## 1. Struktura sposobu strzelania (Firing Mode / Weapon Pattern)

Ten fragment odpowiada za to, jak pociski są wystrzeliwane w danej chwili.

- **`drain`** – Zużycie energii (mocy) przy każdym strzale. W strukturze broni przeciwników często wynosi 0 ponieważ wrogowie tego nie używają. To pole istnieje, ale NIE JEST UŻYWANE. Zamiast tego player powinien użyć `power_use` z struktury broni w weapon_port.json.
- **`shotRepeat`** – Opóźnienie między kolejnymi seriami strzałów (częstotliwość). Jest ignorowane przez wrogów. Wrogowie używają `freq[]` zamiast tego.
- **`multi`** – Liczba pocisków wystrzeliwanych jednocześnie w jednej serii. Kod wykonuje pętlę `for (int tempCount = weapons[temp3].multi; tempCount > 0; tempCount--)`, aby stworzyć odpowiednią liczbę obiektów pocisków.
- **`weapAni`** – Maksymalna klatka animacji dla grafiki pocisku (używane do animowanych strzałów). W kodzie przypisywane do `enemyShot[b].animax`.
- **`max`** – Liczba zdefiniowanych punktów (wzorców) w tablicy patterns. Jeśli broń ma multi większe niż 1, gra przechodzi przez kolejne indeksy tej tablicy aż do wartości max.
- **`tx`, `ty`** – Tylko dla wrogów – parametry "homingu" (korekta trajektorii w locie). W tyrian2.c widać: if (enemyShot[z].tx != 0) – używane do śledzenia gracza..
- **`aim`** – Wartość celowania. Jeśli aim > 0, gra oblicza wektor w stronę gracza, zamiast korzystać ze stałych wartości sx/sy. Wyższa wartość oznacza szybszy pocisk nakierowany na cel.
- **`acceleration` / `accelerationx`** – Dodatkowe przyspieszenie pocisku w osiach Y i X po wystrzeleniu.
- **`sound`** – Identyfikator dźwięku odtwarzanego przy wystrzale.
- **`shipBlastFilter`** – Filtr graficzny nakładany na statek w momencie strzału (np. błysk lufy).
- **`circlesize`** – Określa rozmiar okręgu, po którym porusza się pocisk (tzw. "orbiting shot"). Jeśli >0, pocisk nie leci prosto, ale krąży wokół punktu startowego.
- **`trail`** – Definiuje efekt śladu (trail) pozostawianego przez pocisk. Wartość 98 powoduje eksplozję w miejscu poprzedniej klatki, inne wartości mogą wywoływać dym, iskry itp.

---

## 2. Podstruktura patterns (Wzorce pojedynczych pocisków)

Definiuje właściwości konkretnego pocisku w serii.

### Parametry podstawowe

- **`attack`** – Obrażenia zadawane przez ten konkretny pocisk.
  - Jeśli `attack` w zakresie 100-249 → oznacza to Chain Reaction (reakcję łańcuchową). Prawdziwe obrażenia to 1, a wartość `attack-100` to ID kolejnego pocisku, który zostanie wystrzelony po trafieniu.
  - Jeśli `attack >= 250` → pocisk zadaje obrażenia `attack-250` i ustawia flagę `infiniteShot` (może przenikać przez wrogów).
  - Jeśli `attack == 99` → specjalny efekt: nie zadaje obrażeń, ale zamraża wroga (`iced = 40`).

- **`del` (delay/duration)** – Czas życia pocisku lub opóźnienie przed jego zniknięciem.
  - Jeśli `del` w zakresie 100-120 → definiuje liczbę klatek animacji (`del-100+1`).
  - Jeśli `del == 99` lub `98` → pocisk reaguje na pozycję kursora myszy (celowanie ręczne).

- **`sx`, `sy`** – Początkowa prędkość (pęd) pocisku w osiach X i Y.
  - Jeśli `sx > 100` → pocisk "przykleja się" do ruchu gracza (względny układ współrzędnych).

- **`bx`, `by`** – Przesunięcie (offset) punktu startowego pocisku względem środka statku. Pozwala to na strzelanie np. z dwóch skrzydeł jednocześnie (bx ujemne dla lewego, dodatnie dla prawego).

- **`sg` (shot graphic)** – Identyfikator grafiki (sprite'a) używanego dla tego konkretnego pocisku.
  - Jeśli `sg >= 500` → grafika pobierana z arkusza `spriteSheet12`.
  - Jeśli `sg < 500` → grafika z `spriteSheet8`.

---

## 3. Struktura samej broni (Weapon Item)

To jest "opakowanie", które trzyma statystyki rynkowe i odnośniki do powyższych trybów.

- **`cost`** – Cena zakupu broni w sklepie.
- **`power_use`** – Bazowe zapotrzebowanie na moc generatora.
- **`item_graphic`** – Ikona broni wyświetlana w menu wyposażenia (hangarze).
- **`modes_count`** – Liczba dostępnych poziomów ulepszeń (Level 1, Level 2 itd.).
- **`firing_modes`** – Tablice zawierające indeksy (ID) struktur strzelania. Każdy kolejny poziom ulepszenia broni (Power Level) aktywuje kolejny zestaw indeksów z tablicy `mode_1`.

---

## 4. Logika celowania (Enemy AIM Logic)

### Podstawowa logika aim

- **`aim > 0`** – sprawdza, czy przeciwnik ma parametr aim (celowanie).

1. Wybierany jest cel (`targetX`, `targetY`).
2. Obliczana jest różnica pozycji celu i przeciwnika (`aimX`, `aimY`).
3. Normalizacja wektora – dzielenie przez `maxMagAim` (największa składowa).
4. Mnożenie przez `aim` – to daje prędkość pocisku w osiach X i Y w kierunku gracza.
5. Wynik zaokrąglany (`roundf`) i zapisywany jako `sxm`, `sym` (prędkość pocisku).

**Podsumowanie:** Logika aim to proste celowanie w gracza – pocisk leci w kierunku pozycji gracza z prędkością zależną od wartości aim (im wyższa, tym szybszy i celniejszy lot).

### Zaawansowana logika AIM (tyrian2.c, linie ~1850-1890)

```c
if (weapons[temp3].aim > 0)
{
    JE_byte aim = weapons[temp3].aim;
    if (difficultyLevel > DIFFICULTY_NORMAL)
        aim += difficultyLevel - 2;

    JE_word targetX = player[0].x;
    JE_word targetY = player[0].y;

    // Obsługa trybu dwóch graczy – wybór żywego celu
    if (twoPlayerMode) { /* ... */ }

    JE_integer aimX = (targetX + 25) - tempX - tempMapXOfs - 4;
    JE_integer aimY = targetY - tempY;

    const JE_integer maxMagAim = MAX(abs(aimX), abs(aimY));
    enemyShot[b].sxm = roundf((float)aimX / maxMagAim * aim);
    enemyShot[b].sym = roundf((float)aimY / maxMagAim * aim);
}
```

**Opis krok po kroku:**
1. Sprawdzenie `aim > 0`.
2. Modyfikacja celności w zależności od poziomu trudności (dodatkowe punkty).
3. Wybór celu – w trybie dwóch graczy losowy żywy gracz.
4. Obliczenie różnicy pozycji celu i wroga (`aimX`, `aimY`).
5. Normalizacja wektora – dzielenie przez `maxMagAim` (największa składowa, aby zachować kierunek).
6. Mnożenie przez `aim` – to daje prędkość pocisku w osiach X i Y w kierunku gracza.
7. Wynik zaokrąglany (`roundf`) i zapisywany jako `sxm`, `sym` (prędkość pocisku).

---

## 5. Specjalne typy strzałów i broni

W `tyrian2.c` zidentyfikowano szereg niestandardowych wartości `tur` (typ wystrzeliwanego pocisku):

- **252** – Savara Boss DualMissile – Wystrzeliwuje dwie eksplozje (`JE_setupExplosion`) symulujące pocisk.
- **251** – Suck-O-Magnet – Przyciąga statek gracza w stronę wroga (`player[0].x_velocity += ...`).
- **253 / 254** – Left/Right ShortRange Magnet – Odpycha lub przyciąga gracza, gdy znajduje się w krótkim zasięgu.
- **255** – Magneto RePulse!! – Odpycha gracza (lub zmienia filtr wizualny wroga na `0x70` – efekt "iskrzenia").

---

## 6. Specjalne przypadki generowania pocisków

W `tyrian2.c` (linie ~1950-2000) znajduje się kod odpowiedzialny za wystrzeliwanie pocisków przez wrogów z uwzględnieniem:

- **Pozycji startowej** – `sx`, `sy` + przesunięcia `bx`, `by`.
- **Efektów dźwiękowych** – losowy kanał dźwiękowy (z pominięciem kanału 3, który jest zarezerwowany).
- **Animacji** – jeśli `aniactive == 2` → reset animacji.
- **Trybu "Galaga"** – ograniczenie częstotliwości strzałów (`galagaShotFreq`).
- **Wielokrotnych pocisków** – pętla po `multi` i szukanie wolnego slotu w `enemyShotAvail`.

---

## 7. Chain Reaction (Reakcja Łańcuchowa)

Gdy `attack` pocisku znajduje się w przedziale 100-249, oznacza to, że po trafieniu w wroga zamiast normalnych obrażeń zostanie wystrzelony nowy pocisk o ID równym `attack-100`.

### Przykład z kodu (tyrian2.c, okolice linii 3300)

```c
if (chain > 0)
{
    shotMultiPos[SHOT_MISC] = 0;
    b = player_shot_create(0, SHOT_MISC, tempShotX, tempShotY, 
                           player[0].mouseX, player[0].mouseY, chain, playerNum);
    shotAvail[z] = 0;
}
```

**Zastosowanie:** Tworzenie "efektu kaskady" – np. pocisk rozpadający się na mniejsze, łańcuchowe wybuchy między wrogami.

---

## 8. Strzelanie okrężne (Orbiting / Circular Shots)

Parametr `circlesize` w strukturze broni jest używany do tworzenia pocisków krążących.

### Kod w shots.c (funkcja player_shot_move_and_draw)

```c
if (shot->shotComplicated != 0)
{
    shot->shotDevX += shot->shotDirX;
    shot->shotX += shot->shotDevX;
    if (abs(shot->shotDevX) == shot->shotCirSizeX)
        shot->shotDirX = -shot->shotDirX;

    shot->shotDevY += shot->shotDirY;
    shot->shotY += shot->shotDevY;
    if (abs(shot->shotDevY) == shot->shotCirSizeY)
        shot->shotDirY = -shot->shotDirY;
}
```

**Działanie:**
- Pocisk porusza się po okręgu/elipsie o promieniu `circlesize`.
- `circlesize > 19` kodowane jest jako `(Y*20 + X)`, gdzie X i Y to promienie elipsy.
---

## 9. Trail (Ślad pocisku) i efekty specjalne

Parametr `trail` w `shots.c`:

```c
if (shot->shotTrail != 255)
{
    if (shot->shotTrail == 98)
        JE_setupExplosion(shot->shotX - shot->shotXM, shot->shotY - shot->shotYM, 0, shot->shotTrail, false, false);
    else
        JE_setupExplosion(shot->shotX, shot->shotY, 0, shot->shotTrail, false, false);
}
```

- **`trail == 98`** – Eksplozja w poprzedniej pozycji pocisku (efekt "smugi ognia").
- **Inne wartości** – eksplozja w bieżącej pozycji (np. dym, iskry, małe wybuchy).
- **`trail == 255`** – brak śladu.

---

## 10. Filtry i efekty wizualne pocisków

- **`shipBlastFilter`** – nakładany na sprite statku (np. błysk podczas strzału). W `tyrian2.c` widoczne jest użycie `enemy[i].filter = 0x70` dla efektu "iskrzenia".

### Cieniowanie (shots.c)

```c
if (background2 && *out_shoty + shadowYDist < 190 && tmp_shotXM < 100)
    blit_sprite2_darken(VGAScreen, *out_shotx+1, *out_shoty + shadowYDist, spriteSheet12, sprite_frame - 500);
```

Rzucanie cienia pocisku na tło nr 2.

### Przezroczystość

W `player_shot_move_and_draw` dla `sprite_frame > 60000` używany jest `blit_sprite_blend` (efekt specjalny, np. laser).

---

## 11. Zestawienie charakterystyk broni: Player vs Enemy

### Legenda

- **✅ PLAYER** – pole jest używane przy wystrzeliwaniu pocisków przez gracza
- **👾 ENEMY** – pole jest używane przy wystrzeliwaniu pocisków przez przeciwników
- **⚠️ RÓŻNICE** – pole działa inaczej lub ma inne znaczenie w zależności od użycia

---

### 1. Podstawowe właściwości trybu strzelania (Firing Mode)

| Pole | ✅ PLAYER | 👾 ENEMY | Uwagi |
|------|--------|-------|-------|
| `drain` | ✅ | ❌ | Tylko dla gracza – koszt energii (mocy) generatora. Przeciwnicy nie mają limitu energii. |
| `shotRepeat` | ✅ | ❌ | Tylko dla gracza – opóźnienie między seriami. Przeciwnicy używają własnego systemu `freq[]` i `eshotwait[]`. Wyrazony w klatkach (ticks). |
| `multi` | ✅ | ✅ | Liczba pocisków w serii – działa identycznie dla obu stron. |
| `weapAni` | ✅ | ✅ | Animacja pocisku – działa tak samo. |
| `max` | ✅ | ✅ | Liczba wzorców w tablicy patterns. |
| `tx`, `ty` | ❌ | ✅ | Tylko dla wrogów – parametry "homingu" (korekta trajektorii w locie). W `tyrian2.c` widać: `if (enemyShot[z].tx != 0)` – używane do śledzenia gracza. |
| `aim` | ❌ | ✅ | Tylko dla wrogów – celowanie w gracza. Gracz zawsze celuje kursorem lub ma stały kierunek. |
| `acceleration` | ✅ | ✅ | Przyspieszenie w osi Y – działa podobnie. |
| `accelerationx` | ✅ | ✅ | Przyspieszenie w osi X – działa podobnie. |
| `sound` | ✅ | ✅ | Dźwięk wystrzału – obie strony go używają. |
| `shipBlastFilter` | ✅ | ❌ | Tylko dla gracza – efekt błysku na statku. Przeciwnicy mają własny system filtrów (`enemy[i].filter`). |
| `circlesize` | ✅ | ❓ | Prawdopodobnie tylko gracz – w kodzie wrogów nie widać użycia. |
| `trail` | ✅ | ❓ | Prawdopodobnie tylko gracz – w kodzie wrogów brak odpowiednika. |

---

### 2. Właściwości pojedynczego pocisku (Patterns)

| Pole | ✅ PLAYER | 👾 ENEMY | Uwagi |
|------|--------|-------|-------|
| `attack` | ✅ | ✅ | Obrażenia – działa tak samo. Uwaga: `attack >= 250` (infinite shot) i `attack` w zakresie 100-249 (chain reaction) są obsługiwane tylko dla gracza? W kodzie wrogów nie widać tych specjalnych przypadków. |
| `del` | ✅ | ✅ | Czas życia pocisku. U wrogów często 255 oznacza "nieskończony". |
| `sx`, `sy` | ✅ | ✅ | Prędkość początkowa. RÓŻNICA: Dla gracza `sx > 100` oznacza "względny ruch z graczem". Dla wrogów – nie. |
| `bx`, `by` | ✅ | ✅ | Offset pozycji startowej – działa podobnie. |
| `sg` | ✅ | ✅ | Grafika pocisku – działa tak samo. |

---

### 3. Specjalne wartości i ich interpretacja

#### Dla gracza (Player-specific)

| Wartość/Przypadek | Miejsce w kodzie | Znaczenie |
|-------------------|-----------------|-----------|
| `attack >= 250` | shots.c ~line 160 | `infiniteShot = true` – pocisk przenika przez wrogów |
| `attack w zakresie 100-249` | shots.c ~line 155 | Chain reaction – po trafieniu wystrzeliwuje nowy pocisk |
| `attack == 99` | tyrian2.c ~line 3250 | Efekt zamrożenia (`iced = 40`) |
| `sx > 100` | shots.c ~line 195 | Pocisk "przykleja się" do ruchu gracza |
| `del == 99 lub 98` | shots.c ~line 180-190 | Pocisk reaguje na pozycję myszy (celowanie ręczne) |
| `del w zakresie 100-120` | shots.c ~line 175 | Definiuje liczbę klatek animacji |
| `sg >= 500` | shots.c ~line 215 | Grafika z `spriteSheet12` |
| `sg < 500` | shots.c ~line 220 | Grafika z `spriteSheet8` |

#### Dla wroga (Enemy-specific)

| Wartość/Przypadek | Miejsce w kodzie | Znaczenie |
|-------------------|-----------------|-----------|
| `tur == 252` | tyrian2.c ~line 1750 | Savara Boss DualMissile – tworzy eksplozje zamiast pocisków |
| `tur == 251` | tyrian2.c ~line 1755 | Suck-O-Magnet – przyciąga gracza |
| `tur == 253/254` | tyrian2.c ~line 1760-1775 | Magnesy krótkiego zasięgu – odpychają/przyciągają |
| `tur == 255` | tyrian2.c ~line 1780 | Magneto RePulse – odpycha gracza |
| `tx > 0` | tyrian2.c ~line 1820 | Korekta trajektorii w locie (homing) |
| `ty > 0` | tyrian2.c ~line 1830 | Korekta trajektorii w locie (homing) |
| `aim > 0` | tyrian2.c ~line 1850 | Celowanie w gracza z modyfikacją trudności |

---

### 4. Różnice w inicjalizacji i przepływie

#### Player (shots.c – player_shot_create)

```c
// Sprawdzenie energii
if (power < weaponPort[portNum].poweruse)
    return MAX_PWEAPON;
power -= weaponPort[portNum].poweruse;

// Obsługa chain reaction
if (weapon->attack[...] > 99 && weapon->attack[...] < 250) {
    shot->chainReaction = weapon->attack[...] - 100;
    shot->shotDmg = 1;
}

// Obsługa nieskończonego pocisku
if (damage >= 250) {
    damage = damage - 250;
    infiniteShot = true;
}
```

#### Enemy (tyrian2.c – pętla strzelania)

```c
// Brak sprawdzania energii
// Bezpośrednie użycie weapons[temp3]
enemyShot[b].sx = tempX + weapons[temp3].bx[tempPos] + tempMapXOfs;
enemyShot[b].sdmg = weapons[temp3].attack[tempPos];

// Obsługa aim (tylko dla wrogów)
if (weapons[temp3].aim > 0) {
    // Oblicz wektor do gracza
    // Modyfikacja w zależności od difficultyLevel
}

// Obsługa specjalnych wartości tur (252-255)
switch (temp3) {
    case 252: /* Savara Boss DualMissile */
    case 251: /* Suck-O-Magnet */
    // ...
}
```

---

### 5. Podsumowanie tabelaryczne

| Kategoria | ✅ PLAYER | 👾 ENEMY |
|-----------|--------|-------|
| Zużycie energii | ✅ (drain) | ❌ |
| Opóźnienie między seriami | ✅ (shotRepeat) | ❌ (używa `freq[]`) |
| Celowanie (`aim`) | ❌ | ✅ |
| Homing w locie | ❌ | ✅ (`tx`, `ty`) |
| Efekty specjalne (magnet, repulse) | ❌ | ✅ (`tur` 251-255) |
| Chain reaction | ✅ | ❌ (brak w kodzie wroga) |
| Infinite shot (przenikanie) | ✅ | ❌ |
| Zamrożenie | ✅ (`attack == 99`) | ❌ |
| Reakcja na mysz | ✅ (`del == 99/98`) | ❌ |
| Przyklejenie do gracza | ✅ (`sx > 100`) | ❌ |
| Animacja | ✅ | ✅ |
| Dźwięk | ✅ | ✅ |
| Grafika (sprite) | ✅ | ✅ |
| Przyspieszenie | ✅ | ✅ |
| Offset pozycji | ✅ | ✅ |
| Czas życia | ✅ | ✅ |

---

### Wnioski

System broni jest w dużej mierze współdzielony – ta sama struktura `JE_WeaponType` jest używana zarówno dla gracza, jak i dla wrogów.

Główne różnice wynikają z kontekstu:

- **Gracz ma ograniczenia energetyczne** (`drain`)
- **Wrogowie mają zaawansowane celowanie** (`aim`, `tx`, `ty`)
- **Wrogowie mają specjalne efekty magnetyczne** (`tur` 251-255)
- **Gracz ma bardziej złożone mechaniki pocisków** (chain reaction, infinite shot, trailing)

## 12. tx i ty są używane TYLKO do homingu wrogów

Dowód z kodu (tyrian2.c, okolice linii ~1820-1840)
c
// Dla pocisków wroga
enemyShot[b].tx = weapons[temp3].tx;
enemyShot[b].ty = weapons[temp3].ty;


if (enemyShot[z].tx != 0)
{
    if (enemyShot[z].sx > player[0].x)
    {
        if (enemyShot[z].sxm > -enemyShot[z].tx)
            enemyShot[z].sxm--;
    }
    else
    {
        if (enemyShot[z].sxm < enemyShot[z].tx)
            enemyShot[z].sxm++;
    }
}

if (enemyShot[z].ty != 0)
{
    if (enemyShot[z].sy > player[0].y)
    {
        if (enemyShot[z].sym > -enemyShot[z].ty)
            enemyShot[z].sym--;
    }
    else
    {
        if (enemyShot[z].sym < enemyShot[z].ty)
            enemyShot[z].sym++;
    }
}
### 12.1. Co dokładnie robią tx i ty?
To jest "miękki homing" – pocisk łagodnie koryguje swoją trajektorię w kierunku gracza.

Mechanika krok po kroku:
tx i ty to maksymalna korekta prędkości na klatkę

W każdej klatce pocisk sprawdza, czy jest na lewo czy prawo od gracza

Jeśli jest na lewo (sx < player.x), zwiększa sxm (ale nie więcej niż tx)

Jeśli jest na prawo (sx > player.x), zmniejsza sxm (ale nie więcej niż tx)

Przykład:

tx = 2 (maksymalna korekta 2 piksele/klatkę)
sxm = 5 (pocisk leci w prawo z prędkością 5)
Gracz jest na lewo od pocisku

Klatka 1: sxm = 5 - 1 = 4  (zmniejszamy, bo pocisk ma zawrócić)
Klatka 2: sxm = 4 - 1 = 3
Klatka 3: sxm = 3 - 1 = 2
...
Aż sxm spadnie do 0, a potem zacznie rosnąć w przeciwnym kierunku

### 12.3. Co musisz wiedzieć do implementacji?
Dla wroga (ENEMY):
// Inicjalizacja pocisku wroga
enemyShot.tx = weapons[id].tx;
enemyShot.ty = weapons[id].ty;

// Aktualizacja co klatkę
if (enemyShot.tx != 0) {
    if (enemyShot.x > player.x) {
        if (enemyShot.vx > -enemyShot.tx)
            enemyShot.vx--;
    } else {
        if (enemyShot.vx < enemyShot.tx)
            enemyShot.vx++;
    }
}
// To samo dla ty i osi Y

### 12.4. Różnica między aim a tx/ty
Aspekt	        aim	                            tx / ty
Kiedy działa?	Tylko przy wystrzeleniu	        W każdej klatce (ciągły)
Co robi?	    Ustawia początkowy kierunek	    Korekta trajektorii w locie
Siła efektu	    Określa prędkość początkową	    Określa maks. korektę na klatkę
Typ	            "Twardy" homing (celny strzał)	"Miękki" homing (pocisk się zakręca)

Przykład użycia w oryginalnych danych:
aim = 10 – pocisk leci prosto na gracza od razu
tx = 2, ty = 1 – pocisk leci mniej więcej w stronę gracza, ale może go "przegapić"

---

## Dokumentacja pól attack i del w systemie strzelania Tyriana

### Uwaga wstępna
Pola attack i del znajdują się w strukturze patterns każdej broni. Ich interpretacja ZALEŻY od tego, kto strzela – gracz (player) lub wróg (enemy). Ten dokument opisuje oba przypadki.

### 1. Pole attack – Obrażenia i efekty specjalne

#### 1.1 Dla gracza (PLAYER) – pełna logika
W kodzie shots.c (funkcja player_shot_create) wartość attack jest interpretowana w następujący sposób:

```c
// Kod oryginalny (shots.c)
if (weapon->attack[shotMultiPos[bay_i]-1] > 99 && weapon->attack[shotMultiPos[bay_i]-1] < 250)
{
    // Chain Reaction
    shot->chainReaction = weapon->attack[shotMultiPos[bay_i]-1] - 100;
    shot->shotDmg = 1;
}
else if (damage == 99)
{
    // Zamrożenie
    damage = 0;
    doIced = 40;
    enemy[b].iced = 40;
}
else
{
    shot->shotDmg = weapon->attack[shotMultiPos[bay_i]-1];
    if (damage >= 250)
    {
        // Infinite Shot (penetracja)
        damage = damage - 250;
        infiniteShot = true;
    }
}
```

##### Tabela wartości dla gracza:

| Zakres/Wartość | Interpretacja | Obrażenia | Efekt dodatkowy |
|----------------|---------------|-----------|-----------------|
| 1-98 | Normalne obrażenia | = wartość | brak |
| 99 | Zamrożenie | 0 | Zatrzymanie wroga na 40 klatek |
| 100-249 | Chain reaction | 1 | Wystrzelenie nowej broni o ID = (wartość - 100) |
| 250-255 | Infinite shot | = (wartość - 250) | Penetracja (przechodzi przez wrogów) |

##### Przykłady użycia w oryginalnych danych Tyriana:

```c
// Przykład 1: Zwykły pocisk
attack = 10;   // Obrażenia 10, brak efektów specjalnych

// Przykład 2: Chain reaction (pocisk rozpadający się)
attack = 150;  // Obrażenia 1, po trafieniu wystrzeliwuje broń nr 50

// Przykład 3: Zamrażający pocisk
attack = 99;   // Brak obrażeń, zamrożenie wroga na 40 klatek

// Przykład 4: Przenikający laser
attack = 255;  // Obrażenia 5 (255-250), przenika przez wszystkich wrogów
```

#### 1.2 Dla wroga (ENEMY) – prosta logika
W kodzie tyrian2.c (pętla strzelania wroga) wartość attack jest używana bez żadnej interpretacji:

```c
// Kod oryginalny (tyrian2.c)
enemyShot[b].sdmg = weapons[temp3].attack[tempPos];
// Brak dodatkowych warunków!
```

##### Tabela wartości dla wroga:

| Zakres/Wartość | Interpretacja | Uwagi |
|----------------|---------------|-------|
| Dowolna liczba | Obrażenia = wartość | Bez chain reaction, bez infinite shot, bez zamrożenia |

##### Przykład:

```c
// Dla wroga WSZYSTKIE te wartości oznaczają TYLKO obrażenia:
attack = 10;   // Obrażenia 10
attack = 99;   // Obrażenia 99 (NIE zamrożenie!)
attack = 150;  // Obrażenia 150 (NIE chain reaction!)
attack = 255;  // Obrażenia 255 (NIE penetracja!)
```

### 2. Pole del – Czas życia i efekty specjalne

#### 2.1 Dla gracza (PLAYER) – pełna logika
W kodzie shots.c wartość del jest interpretowana w następujący sposób:

```c
// Kod oryginalny (shots.c)
JE_byte del = weapon->del[shotMultiPos[bay_i]-1];

if (del == 121)
{
    shot->shotTrail = 0;    // wyłącz efekt śladu
    del = 255;              // bardzo długi czas życia
}

if (del == 99 || del == 98)
{
    // Reakcja na pozycję myszy (oś X)
    tmp_by = PX - mouseX;
    if (tmp_by < -5) tmp_by = -5;
    else if (tmp_by > 5) tmp_by = 5;
    shot->shotXM += tmp_by;
}

if (del == 99 || del == 100)
{
    // Reakcja na pozycję myszy (oś Y)
    tmp_by = PY - mouseY;
    if (tmp_by < -4) tmp_by = -4;
    else if (tmp_by > 4) tmp_by = 4;
    shot->shotYM = tmp_by;
}

if (del > 100 && del < 120)
{
    // Określenie liczby klatek animacji
    shot->shotAniMax = (del - 100 + 1);
}

// Normalny przypadek – czas życia
shotAvail[shot_id] = del;
```

##### Tabela wartości dla gracza:

| Wartość | Interpretacja | Czas życia | Efekt dodatkowy |
|---------|---------------|------------|-----------------|
| 1-97 | Normalny czas życia | = wartość | brak |
| 98 | Reakcja na mysz (X) | 98 | Korekta prędkości X wg pozycji myszy |
| 99 | Reakcja na mysz (X+Y) | 99 | Korekta prędkości X i Y wg pozycji myszy |
| 100 | Reakcja na mysz (Y) | 100 | Korekta prędkości Y wg pozycji myszy |
| 101-119 | Animowany pocisk | = wartość | Liczba klatek animacji = (wartość - 100 + 1) |
| 120 | (zakres końcowy) | 120 | (jak wyżej) |
| 121 | Specjalny trail | 255 | Wyłącza efekt śladu (trail = 0) |
| 122-255 | Normalny czas życia | = wartość | brak |

##### Przykłady użycia w oryginalnych danych Tyriana:

```c
// Przykład 1: Zwykły pocisk żyjący 50 klatek
del = 50;

// Przykład 2: Pocisk kierowany myszką (np. w niektórych bonusowych broniach)
del = 99;    // Pełne sterowanie myszą

// Przykład 3: Pocisk z animacją 5 klatek
del = 105;   // shotAniMax = (105-100+1) = 6 klatek animacji

// Przykład 4: Długi czas życia bez trailu
del = 121;   // Czas życia 255 klatek, trail wyłączony
```

#### 2.2 Dla wroga (ENEMY) – prosta logika
W kodzie tyrian2.c wartość del jest używana bez żadnej interpretacji:

```c
// Kod oryginalny (tyrian2.c)
enemyShot[b].duration = weapons[temp3].del[tempPos];
// Brak dodatkowych warunków!
```

##### Tabela wartości dla wroga:

| Wartość | Interpretacja | Uwagi |
|---------|---------------|-------|
| Dowolna liczba | Czas życia = wartość | Bez reakcji na mysz, bez specjalnej animacji, bez specjalnego trailu |

##### Przykład:

```c
// Dla wroga WSZYSTKIE te wartości oznaczają TYLKO czas życia:
del = 50;    // Czas życia 50 klatek
del = 98;    // Czas życia 98 klatek (NIE reakcja na mysz!)
del = 105;   // Czas życia 105 klatek (NIE animacja!)
del = 121;   // Czas życia 121 klatek (NIE specjalny trail!)
```

### 3. Podsumowanie różnic między graczem a wrogiem

| Pole | Aspekt | Gracz (Player) | Wróg (Enemy) |
|------|--------|----------------|--------------|
| attack | Zakres 1-98 | Obrażenia = wartość | Obrażenia = wartość |
| | Wartość 99 | Zamrożenie (obrażenia 0) | Obrażenia 99 |
| | Zakres 100-249 | Chain reaction (obrażenia 1) | Obrażenia = wartość |
| | Zakres 250-255 | Infinite shot (obrażenia = wartość-250) | Obrażenia = wartość |
| del | Wartości 1-97 | Czas życia = wartość | Czas życia = wartość |
| | Wartości 98-100 | Reakcja na mysz (korekta trajektorii) | Czas życia = wartość |
| | Wartości 101-120 | Animacja (liczba klatek = wartość-100+1) | Czas życia = wartość |
| | Wartość 121 | Specjalny trail (czas życia 255) | Czas życia = 121 |
| | Wartości 122-255 | Czas życia = wartość | Czas życia = wartość |
