# Dokumentacja mechaniki strzelania wroga (Enemy) – Tyrian

## Uwaga wstępna
Wrogowie w Tyrianie używają tej samej struktury broni co gracz, ale z uproszczoną logiką – pomijają wiele zaawansowanych mechanik (przyspieszenie, circlesize, trail, chain reaction, infinite shot, zamrożenie). Ten dokument opisuje pełną logikę strzelania przeciwników na podstawie kodu z tyrian2.c.

## 2. Struktura danych pocisku wroga
```c
// Z tyrian2.c – struktura pocisku wroga
typedef struct {
    JE_integer sx;           // pozycja X
    JE_integer sy;           // pozycja Y
    JE_integer sxm;          // prędkość X
    JE_integer sym;          // prędkość Y
    JE_byte sxc;             // przyspieszenie X (rzadko używane)
    JE_byte syc;             // przyspieszenie Y (rzadko używane)
    JE_byte tx;              // homing X (maksymalna korekta na klatkę)
    JE_byte ty;              // homing Y (maksymalna korekta na klatkę)
    JE_byte duration;        // czas życia (w klatkach)
    JE_byte sdmg;            // obrażenia
    JE_byte sgr;             // grafika pocisku
    JE_byte animate;         // aktualna klatka animacji
    JE_byte animax;          // maksymalna klatka animacji
} EnemyShot;
```

## 3. Inicjalizacja pocisku wroga
Kod z tyrian2.c (około linii 1700-1850):

```c
// Znajdź wolny slot na pocisk
for (b = 0; b < ENEMY_SHOT_MAX; b++) {
    if (enemyShotAvail[b] == 1)
        break;
}

// Inicjalizacja pocisku
enemyShot[b].sx = tempX + weapons[temp3].bx[tempPos] + tempMapXOfs;
enemyShot[b].sy = tempY + weapons[temp3].by[tempPos];
enemyShot[b].sdmg = weapons[temp3].attack[tempPos];
enemyShot[b].tx = weapons[temp3].tx;
enemyShot[b].ty = weapons[temp3].ty;
enemyShot[b].duration = weapons[temp3].del[tempPos];
enemyShot[b].animate = 0;
enemyShot[b].animax = weapons[temp3].weapani;

// Ustawienie prędkości (zależne od lufy – j=1,2,3)
switch (j) {
    case 1:  // lufa środkowa
        enemyShot[b].syc = weapons[temp3].acceleration;
        enemyShot[b].sxc = weapons[temp3].accelerationx;
        enemyShot[b].sxm = weapons[temp3].sx[tempPos];
        enemyShot[b].sym = weapons[temp3].sy[tempPos];
        break;
    case 3:  // lufa lewa
        enemyShot[b].sxc = -weapons[temp3].acceleration;
        enemyShot[b].syc = weapons[temp3].accelerationx;
        enemyShot[b].sxm = -weapons[temp3].sy[tempPos];
        enemyShot[b].sym = -weapons[temp3].sx[tempPos];
        break;
    case 2:  // lufa prawa
        enemyShot[b].sxc = weapons[temp3].acceleration;
        enemyShot[b].syc = -weapons[temp3].acceleration;
        enemyShot[b].sxm = weapons[temp3].sy[tempPos];
        enemyShot[b].sym = -weapons[temp3].sx[tempPos];
        break;
}

// Homing (celowanie w gracza)
if (weapons[temp3].aim > 0) {
    JE_byte aim = weapons[temp3].aim;
    
    // Modyfikacja celności w zależności od poziomu trudności
    if (difficultyLevel > DIFFICULTY_NORMAL)
        aim += difficultyLevel - 2;
    
    // Oblicz wektor do gracza
    JE_integer aimX = (targetX + 25) - tempX - tempMapXOfs - 4;
    JE_integer aimY = targetY - tempY;
    
    const JE_integer maxMagAim = MAX(abs(aimX), abs(aimY));
    enemyShot[b].sxm = roundf((float)aimX / maxMagAim * aim);
    enemyShot[b].sym = roundf((float)aimY / maxMagAim * aim);
}
```

## 4. Aktualizacja pocisku wroga (każda klatka)
Kod z tyrian2.c (około linii 3000-3100):

```c
for (int z = 0; z < ENEMY_SHOT_MAX; z++) {
    if (enemyShotAvail[z] == 0) {
        
        // KROK 1: Dodaj przyspieszenie do prędkości (rzadko używane)
        enemyShot[z].sxm += enemyShot[z].sxc;
        enemyShot[z].sym += enemyShot[z].syc;
        
        // KROK 2: Dodaj prędkość do pozycji
        enemyShot[z].sx += enemyShot[z].sxm;
        enemyShot[z].sy += enemyShot[z].sym;
        
        // KROK 3: Homing (tylko jeśli tx != 0 lub ty != 0)
        if (enemyShot[z].tx != 0) {
            if (enemyShot[z].sx > player[0].x) {
                if (enemyShot[z].sxm > -enemyShot[z].tx)
                    enemyShot[z].sxm--;
            } else {
                if (enemyShot[z].sxm < enemyShot[z].tx)
                    enemyShot[z].sxm++;
            }
        }
        
        if (enemyShot[z].ty != 0) {
            if (enemyShot[z].sy > player[0].y) {
                if (enemyShot[z].sym > -enemyShot[z].ty)
                    enemyShot[z].sym--;
            } else {
                if (enemyShot[z].sym < enemyShot[z].ty)
                    enemyShot[z].sym++;
            }
        }
        
        // KROK 4: Sprawdź czy pocisk żyje
        if (enemyShot[z].duration-- == 0 ||
            enemyShot[z].sy > 190 || enemyShot[z].sy <= -14 ||
            enemyShot[z].sx > 275 || enemyShot[z].sx <= 0) {
            enemyShotAvail[z] = true;
        }
        
        // KROK 5: Aktualizacja animacji
        if (enemyShot[z].animax != 0) {
            if (++enemyShot[z].animate >= enemyShot[z].animax)
                enemyShot[z].animate = 0;
        }
        
        // KROK 6: Renderowanie
        if (enemyShot[z].sgr >= 500)
            blit_sprite2(VGAScreen, enemyShot[z].sx, enemyShot[z].sy,
                        spriteSheet12, enemyShot[z].sgr + enemyShot[z].animate - 500);
        else
            blit_sprite2(VGAScreen, enemyShot[z].sx, enemyShot[z].sy,
                        spriteSheet8, enemyShot[z].sgr + enemyShot[z].animate);
    }
}
```

## 5. System szybkostrzelności wroga (freq)
Wrogowie mają 3 niezależne lufy, każda z własną częstotliwością strzałów:

```c
// Struktura wroga (tyrian2.c)
typedef struct {
    JE_byte freq[3];        // częstotliwość strzałów dla każdej lufy (w klatkach)
    JE_byte eshotwait[3];   // licznik oczekiwania dla każdej lufy
    JE_byte tur[3];         // typ broni dla każdej lufy (ID z weapons[])
    JE_byte eshotmultipos[3]; // pozycja w tablicy patterns dla danej lufy
    // ... reszta pól
} JE_SingleEnemyType;

// Logika strzelania (z JE_drawEnemy)
for (int j = 3; j > 0; j--) {
    if (enemy[i].freq[j-1]) {
        if (--enemy[i].eshotwait[j-1] == 0) {
            enemy[i].eshotwait[j-1] = enemy[i].freq[j-1];
            
            // Modyfikacja trudności – szybsze strzały na wyższych poziomach
            if (difficultyLevel > DIFFICULTY_NORMAL) {
                enemy[i].eshotwait[j-1] = (enemy[i].eshotwait[j-1] / 2) + 1;
                if (difficultyLevel > DIFFICULTY_MANIACAL)
                    enemy[i].eshotwait[j-1] = (enemy[i].eshotwait[j-1] / 2) + 1;
            }
            
            // Wystrzel pocisk z lufy j...
        }
    }
}
```

### Przykład użycia freq:

```c
// Wróg z trzema lufami strzelającymi w różnym tempie
freq[0] = 60;   // lufa 1: co 60 klatek (wolno)
freq[1] = 30;   // lufa 2: co 30 klatek (średnio)
freq[2] = 15;   // lufa 3: co 15 klatek (szybko)
```

## 6. Specjalne typy strzałów wroga (wartości tur)
W kodzie tyrian2.c zidentyfikowano specjalne wartości tur, które nie są zwykłymi pociskami:

| Wartość | Nazwa | Działanie |
|---------|-------|-----------|
| 251 | Suck-O-Magnet | Przyciąga statek gracza |
| 252 | Savara Boss DualMissile | Tworzy dwie eksplozje zamiast pocisków |
| 253 | Left ShortRange Magnet | Odpycha gracza w lewo (krótki zasięg) |
| 254 | Right ShortRange Magnet | Odpycha gracza w prawo (krótki zasięg) |
| 255 | Magneto RePulse | Odpycha gracza (długi zasięg) + filtr wizualny |

```c
// Przykład – Magneto RePulse (tyrian2.c)
case 255: /* Magneto RePulse!! */
    if (difficultyLevel != DIFFICULTY_EASY) {
        if (j == 3) {
            enemy[i].filter = 0x70;  // efekt wizualny na wrogu
        } else {
            const JE_integer repulsion = 4 - (abs(player[0].x - tempX) + 
                                               abs(player[0].y - tempY)) / 20;
            if (repulsion > 0)
                player[0].x_velocity += (player[0].x > tempX) ? repulsion : -repulsion;
        }
    }
    break;
```

## 7. Modyfikatory poziomu trudności dla wrogów

| Mechanika | Poziom trudności | Modyfikacja |
|-----------|------------------|-------------|
| Szybkostrzelność (freq) | Normalny | brak |
| | Hard, Impossible, Insanity | wait = (wait / 2) + 1 |
| | Maniacal, Zinglon, Nortaneous | wait = (wait / 2) + 1 (dwa razy) |
| Celność (aim) | Normalny | brak |
| | Hard+ | aim += difficultyLevel - 2 |
| Obrażenia od wroga | Brak skalingu | sdmg bez zmian |
| Wytrzymałość wroga (armor) | Patrz osobny dokument | Skaluje się z trudnością |

## 8. Pełna sekwencja aktualizacji (kolejność)

```text
KROK 1: Dodaj przyspieszenie do prędkości (sxc, syc)
   ↓
KROK 2: Dodaj prędkość do pozycji (sx += sxm, sy += sym)
   ↓
KROK 3: Homing – korekta prędkości w kierunku gracza (tx, ty)
   ↓
KROK 4: Sprawdź czy pocisk żyje (duration--, granice ekranu)
   ↓
KROK 5: Aktualizacja animacji (animate)
   ↓
KROK 6: Renderowanie
```

## Kluczowe wnioski
Wróg jest prostszy – brak wielu zaawansowanych mechanik gracza.

Homing (tx, ty) to unikalna cecha wrogów – gracz jej nie ma.

Trzy niezależne lufy (freq[3]) pozwalają na złożone wzory strzałów.

Poziom trudności wpływa na szybkostrzelność i celność wrogów.

Specjalne wartości tur (251-255) realizują unikalne efekty magnetyczne.