 # Dokumentacja mechaniki strzelania gracza (Tyrian)

## 1. Pełna sekwencja aktualizacji (właściwa kolejność)

### Krok 1: Zapisz stare wartości (potrzebne do trailu)
```c
int old_shotX = shot->shotX;
int old_shotY = shot->shotY;
```

### Krok 2: Przyspieszenie → prędkość
```c
shot->shotXM += shot->shotXC;    // przyspieszenie poziome
shot->shotYM += shot->shotYC;    // przyspieszenie pionowe
```

### Krok 3: Prędkość → pozycja
```c
shot->shotX += shot->shotXM;
shot->shotY += shot->shotYM;
```

### Krok 4: Ograniczenia (jeśli przekroczono 100)
```c
if (shot->shotXM > 100)
{
    shot->shotX -= 120;
    shot->shotX += player[...].delta_x_shot_move;
}

if (shot->shotYM > 100)
{
    shot->shotY -= 120;
    shot->shotY += player[...].delta_y_shot_move;
}
```

### Krok 5: Ruch okrężny (circlesize)
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

### Krok 6: Trail (ślad)
```c
if (shot->shotTrail != 255)
{
    if (shot->shotTrail == 98)
        JE_setupExplosion(old_shotX - shot->shotXM, old_shotY - shot->shotYM, ...);
    else
        JE_setupExplosion(shot->shotX, shot->shotY, ...);
}
```

---

## 2. Szczegółowe wyjaśnienie: Specjalne ograniczenie (prędkość > 100)

### Co oznacza wartość > 100?

W oryginalnym Tyrianie wartości prędkości (sx, sy) mają zakres 1-100 dla normalnych pocisków. Wartości > 100 są specjalną flagą:

| Wartość | Znaczenie |
|---------|-----------|
| 1-100   | Normalna prędkość |
| 101     | "Przyklejony" do gracza w obu osiach |
| 102+    | "Przyklejony" tylko w osi X |

### Jak to działa?

To NIE jest clamp ani limit prędkości! Prędkość `shotXM` pozostaje > 100, zmienia się tylko pozycja.

**Krok po kroku:**
1. `shotXM > 100` – wykryto specjalną flagę (pocisk ma "podążać" za graczem)
2. `shotX -= 120` – cofamy pocisk o 120 pikseli (kompensacja)
3. `shotX += player.delta_x_shot_move` – dodajemy zmianę pozycji gracza od ostatniej klatki

**Efekt końcowy:** Pocisk zachowuje swoją prędkość względem gracza, ale jego pozycja bezwzględna jest korygowana tak, aby "trzymać się" gracza.

### Dlaczego akurat 120?

Wartość arbitralna – wystarczająco duża, aby cofnąć pocisk poza ekran, a potem dodać ruch gracza.

- Normalny pocisk leci: `x += vx` (gdzie vx ≤ 100)
- Przyklejony pocisk: `x += vx - 120 + player.delta_x`

### Przykład liczbowy

Załóżmy:
- `shotXM = 101` (specjalna flaga)
- `player.delta_x_shot_move = 3` (gracz przesunął się w prawo o 3 piksele)
- Początkowa pozycja `shotX = 200`

**Klatka 1:**
```c
// Normalne dodanie prędkości (przed ifem)
shotX = 200 + 101 = 301  // poza ekranem!

// Jeśli shotXM > 100:
shotX = 301 - 120 = 181
shotX = 181 + 3 = 184
```

Efekt: Pocisk nie uciekł poza ekran, tylko "przeskoczył" z powrotem, dostosowując się do pozycji gracza.

### Kiedy to jest używane?

W oryginalnych danych Tyriana:
- Sidekick (towarzyszący statek) – wystrzeliwuje pociski z `sx = 101`
- Niektóre bronie specjalne – mają pociski podążające za graczem

### Implementacja

**Wzór matematyczny:**
```
jeśli v_x > 100:
    x = x + v_x - 120 + Δx_gracza
w przeciwnym razie:
    x = x + v_x
```

**Przykładowy kod (Python):**
```python
# Normalna aktualizacja
self.x += self.vx
self.y += self.vy

# Specjalna korekta dla "przyklejonych" pocisków
if self.vx > 100:
    self.x -= 120
    self.x += player.delta_x

if self.vy > 100:
    self.y -= 120
    self.y += player.delta_y
```

**Uwaga:** Dla osi Y wartość 101 oznacza to samo – przyklejenie w pionie. W oryginalnych danych częściej używa się `sx = 101` niż `sy = 101`.

---

## 3. Kluczowe pytania i odpowiedzi

**Pytanie 1:** Czy najpierw przyspieszenie czy pozycja?
**Odpowiedź:** Najpierw przyspieszenie → prędkość, potem prędkość → pozycja.

**Pytanie 2:** Czy circlesize jest dodawane przed czy po normalnym ruchu?
**Odpowiedź:** PO normalnym ruchu (przyspieszenie i prędkość są najpierw, potem dodawany jest efekt okrężny).

**Pytanie 3:** Czy circlesize używa starej czy nowej pozycji?
**Odpowiedź:** Używa NOWEJ pozycji (po dodaniu prędkości), a następnie dodaje odchylenie.

**Pytanie 4:** Kiedy zapisywana jest stara pozycja dla trailu?
**Odpowiedź:** PRZED jakimikolwiek zmianami (na samym początku).

---

## 4. Wzory matematyczne (do implementacji)

Dla każdej klatki t:
```
v_x[t] = v_x[t-1] + a_x
v_y[t] = v_y[t-1] + a_y

x[t] = x[t-1] + v_x[t]
y[t] = y[t-1] + v_y[t]

jeśli użyto circlesize:
    offset_x += dir_x
    x[t] += offset_x
    jeśli |offset_x| == radius_x: dir_x = -dir_x

    offset_y += dir_y
    y[t] += offset_y
    jeśli |offset_y| == radius_y: dir_y = -dir_y
```

**Gdzie:**
- `a_x, a_y` = acceleration (przyspieszenie, shotXC, shotYC)
- `v_x, v_y` = prędkość pocisku (shotXM, shotYM)
- `offset_x, offset_y` = odchylenie od środka orbity (shotDevX, shotDevY)
- `radius_x, radius_y` = promienie orbity (shotCirSizeX, shotCirSizeY)
- `dir_x, dir_y` = kierunek ruchu orbity (shotDirX, shotDirY)

---

## 5. Przykład liczbowy (dla zrozumienia)

Załóżmy prosty przypadek (bez circlesize):
- `v_x = 5, a_x = 1`
- Pozycja startowa: `x = 100`

**Klatka 1:**
```
v_x = 5 + 1 = 6
x = 100 + 6 = 106
```

**Klatka 2:**
```
v_x = 6 + 1 = 7
x = 106 + 7 = 113
```

**Gdyby ktoś zrobił odwrotnie (najpierw pozycja, potem przyspieszenie):**
```
x = 100 + 5 = 105   (błąd!)
v_x = 5 + 1 = 6
```

Różnica: 106 vs 105 – już w pierwszej klatce widać odchylenie!

---

## 6. Najważniejsze zasady do zapamiętania

| Zasada | Opis |
|--------|------|
| 1 | Stara pozycja musi być zapisana PRZED jakimikolwiek zmianami (dla trailu) |
| 2 | Przyspieszenie → prędkość → pozycja (w tej kolejności) |
| 3 | Circlesize jest dodawany PO normalnym ruchu |
| 4 | Ograniczenia (przekroczenie 100) są sprawdzane PO dodaniu prędkości |
| 5 | Trail używa starej pozycji tylko dla wartości 98 |

---

## 7. Czego nie można pomylić

**Błędne przekonanie #1:** "Najpierw aktualizuję pozycję, potem dodaję przyspieszenie"
- **POPRAWNIE:** Najpierw przyspieszenie → prędkość, potem prędkość → pozycja

**Błędne przekonanie #2:** "Circlesize jest niezależny od normalnego ruchu"
- **POPRAWNIE:** Circlesize DODAJE się do pozycji już zmienionej przez normalny ruch

**Błędne przekonanie #3:** "Trail używa aktualnej pozycji"
- **POPRAWNIE:** Trail = 98 używa starej pozycji (sprzed zmian), inne wartości używają nowej

---

## 8. Przepływ dla zwykłego strzału (brak specjalnych efektów)

- **KROK 1:** Zapisz starą pozycję (zawsze) → wykonany
- **KROK 2:** Przyspieszenie → prędkość (shotXC, shotYC = 0) → nic nie zmienia
- **KROK 3:** Prędkość → pozycja (wykonany)
- **KROK 4:** shotXM > 100? → NIE (zwykle 1-10) → pominięty
- **KROK 5:** shotComplicated != 0? → NIE (circlesize = 0) → pominięty
- **KROK 6:** shotTrail != 255? → TAK? (zależy od broni)

---

## 9. Uproszczony schemat decyzyjny (pseudokod)

```c
void update_player_shot(Shot* shot) {
    // ZAWSZE
    old_pos = shot->pos;

    // ZAWSZE
    shot->v += shot->a;
    shot->pos += shot->v;

    // TYLKO jeśli v > 100 (przyklejenie do gracza)
    if (shot->vx > 100) {
        shot->x -= 120;
        shot->x += player.delta_x;
    }
    if (shot->vy > 100) {
        shot->y -= 120;
        shot->y += player.delta_y;
    }

    // TYLKO jeśli circlesize > 0
    if (shot->circlesize > 0) {
        // logika okrężna...
    }

    // TYLKO jeśli trail != 255
    if (shot->trail != 255) {
        if (shot->trail == 98)
            explosion(old_pos - shot->v);
        else
            explosion(shot->pos);
    }
}
```

---

## Podsumowanie

- Kolejność jest święta: **przyspieszenie → prędkość → pozycja**
- Circlesize dodawany jest PO normalnym ruchu (modyfikuje już obliczoną pozycję)
- Stara pozycja zapisywana jest PRZED jakimikolwiek zmianami
- Wartość 98 w trail oznacza użycie starej pozycji (efekt smugi)
- Przekroczenie 100 w prędkości uruchamia specjalne ograniczenie (związane z przyklejeniem do gracza)