# Tyrian Core Game Mechanics Analysis

## State Variables

### Player State
```c
// Core Player Variables
Player player[2];                    // 0-1 players
uint power;                         // Current power (0-900)
uint lastPower;                     // Previous power for UI
uint powerAdd;                      // Power generation rate
JE_byte shieldWait;                 // Shield recharge cooldown (15 frames)
JE_byte shieldT;                    // Shield cost per recharge

// Individual Player Stats
player[0].shield                    // Current shield points
player[0].shield_max               // Maximum shield capacity  
player[0].armor                    // Current armor (HP)
player[0].x_velocity, y_velocity    // Movement velocity
player[0].is_alive                 // Life state
player[0].invulnerable_ticks        // Invincibility frames
player[0].exploding_ticks          // Death animation timer

// Weapon System
player[0].items.weapon[0].id       // Front weapon ID
player[0].items.weapon[0].power    // Front weapon power level (1-11)
player[0].items.weapon[1].id       // Rear weapon ID  
player[0].items.weapon[1].power    // Rear weapon power level
player[0].items.shield             // Shield type
player[0].items.generator          // Power generator type
```

### Bullet State
```c
PlayerShotDataType playerShotData[MAX_PWEAPON];
JE_byte shotAvail[MAX_PWEAPON];     // 0=available, 1-255=duration

// Per-Bullet Variables
shot->shotX, shotY                 // Current position
shot->shotXM, shotYM               // Current velocity  
shot->shotXC, shotYC               // Acceleration
shot->shotComplicated              // Complex movement flag
shot->shotDevX, shotDevY           // Sine wave deviation
shot->shotDirX, shotDirY           // Sine wave direction
shot->shotCirSizeX, shotCirSizeY   // Sine wave amplitude
shot->shotAni, shotAniMax          // Animation frame/max
shot->chainReaction                // Chain damage flag
shot->aimAtEnemy                   // Homing target
```

## Core Constants (Magic Numbers)

| System | Constant | Value | Purpose |
|--------|----------|-------|---------|
| Power | MAX_POWER | 900 | Maximum power capacity |
| Power | POWER_BAR_SCALE | 10 | Power ÷ 10 for UI display |
| Shield | SHIELD_WAIT_TIME | 15 | Frames between shield recharges |
| Shield | SHIELD_COST_MULTIPLIER | 20 | shieldT = shield.tpwr × 20 |
| Weapons | MAX_POWER_LEVEL | 11 | Maximum weapon power |
| Weapons | MAX_PWEAPON | 40 | Maximum simultaneous bullets |
| Movement | SCREEN_WIDTH | 140 | Bullet X boundary |
| Movement | SCREEN_HEIGHT | 170 | Bullet Y boundary |
| Movement | VELOCITY_LIMIT | 100 | Special velocity handling |

## The "Step-by-Step" Logic

### Power System (Per Frame)
```
Step 1: Recovery
    IF NOT (twoPlayerMode OR onePlayerAction):
        power += powerAdd
        IF power > 900: power = 900

Step 2: Shield Consumption  
    IF player[0].is_alive AND player[0].shield < player[0].shield_max AND power > shieldT:
        IF shieldWait == 0:
            power -= shieldT
            player[0].shield += 1
            shieldWait = 15
        ELSE:
            shieldWait -= 1

Step 3: Weapon Consumption
    WHEN firing weapon:
        IF power >= weaponPort[portNum].poweruse:
            power -= weaponPort[portNum].poweruse
            CREATE bullet
        ELSE:
            NO bullet created
```

### Bullet Movement (Per Frame)
```
FOR each active bullet:
    Step 1: Update Lifetime
        shotAvail[bullet_id] -= 1
        IF shotAvail[bullet_id] == 0: REMOVE bullet

    Step 2: Apply Acceleration  
        shot->shotXM += shot->shotXC
        shot->shotYM += shot->shotYC

    Step 3: Update Position
        IF shot->shotXM <= 100:
            shot->shotX += shot->shotXM
        IF shot->shotYM > 100:
            shot->shotY -= 120  // Screen wrap effect

    Step 4: Complex Movement (Sine Wave)
        IF shot->shotComplicated != 0:
            // X-axis oscillation
            shot->shotDevX += shot->shotDirX
            shot->shotX += shot->shotDevX
            IF abs(shot->shotDevX) == shot->shotCirSizeX:
                shot->shotDirX = -shot->shotDirX

            // Y-axis oscillation  
            shot->shotDevY += shot->shotDirY
            shot->shotY += shot->shotDevY
            IF abs(shot->shotDevY) == shot->shotCirSizeY:
                shot->shotDirY = -shot->shotDirY

    Step 5: Boundary Check
        IF bullet outside screen (0-140, 0-170):
            REMOVE bullet

    Step 6: Animation
        shot->shotAni += 1
        IF shot->shotAni == shot->shotAniMax:
            shot->shotAni = 0
```

### Player Movement (Per Frame)
```
Step 1: Apply Input
    velocity += input_vector * acceleration_rate

Step 2: Apply Friction  
    velocity *= friction_coefficient

Step 3: Update Position
    position += velocity

Step 4: Screen Boundaries
    CLAMP position to screen limits
```

## Core Formulas

### Power Generation
```
powerAdd = powerSys[player[0].items.generator].power
shieldT = shields[player[0].items.shield].tpwr * 20
```

### Shield Regeneration Rate
```
Shield Points per Second = (FrameRate / shieldWait) × (1 shield point)
Standard: (30 / 15) = 2 shield points/second
Power Cost per Shield = shieldT (typically 20-100 power units)
```

### Bullet Trajectory

#### Basic Linear
```
NewX = OldX + velocityX
NewY = OldY + velocityY
velocityX += accelerationX  
velocityY += accelerationY
```

#### Sine Wave Movement
```
deviationX += directionX
deviationY += directionY

IF abs(deviationX) == amplitudeX:
    directionX = -directionX
IF abs(deviationY) == amplitudeY:  
    directionY = -directionY

NewX = OldX + velocityX + deviationX
NewY = OldY + velocityY + deviationY
```

#### Homing/Aiming
```
IF weapon->aim > 5:  // Guided weapon
    Find closest enemy within range
    shot->aimAtEnemy = closest_enemy_id
    shot->aimDelay = 5
    shot->aimDelayMax = weapon->aim - 5
    
    // Homing correction applied each frame
    Adjust velocity toward target
```

### Chain Reaction Damage
```
IF weapon->attack[shotMultiPos[bay_i]-1] > 99 AND < 250:
    shot->chainReaction = weapon->attack[shotMultiPos[bay_i]-1] - 100
    shot->shotDmg = 1  // Minimal damage for chain effect
ELSE:
    shot->shotDmg = weapon->attack[shotMultiPos[bay_i]-1]
```

## Interaction Rules

### Hit Detection Flow
```
1. Collision Detected
   ├─ Bullet hits enemy OR enemy bullet hits player
   ├─ Calculate damage amount
   └─ Apply damage to target

2. Player Damage Calculation (JE_playerDamage)
   IF incoming_damage <= player.shield:
       player.shield -= incoming_damage
       CREATE shield hit effects
   ELSE:
       overflow_damage = incoming_damage - player.shield  
       player.shield = 0
       
       IF overflow_damage <= player.armor:
           player.armor -= overflow_damage
           CREATE hull hit effects
       ELSE:
           player.armor = 0
           player.is_alive = false
           START death sequence

3. Enemy Damage Calculation  
   enemy.armorleft -= bullet.damage
   IF enemy.armorleft <= 0:
       enemy.is_alive = false
       CREATE explosion
       AWARD points to player
       SPAWN power-ups (chance-based)

4. Knockback/Physics
   player.velocity += (bullet_velocity * damage) / 2
   // Pushes player back based on damage and bullet force
```

### Power-up Collection
```
1. Purple Ball Collection
   IF player.purple_balls_needed > 1:
       player.purple_balls_needed -= 1
   ELSE:
       power_up_weapon(player, FRONT_WEAPON or REAR_WEAPON)

2. Weapon Power-up
   IF weapon.power < 11:
       weapon.power += 1
       shotMultiPos[port] = 0  // Reset firing pattern
       player.cash += 1000     // Bonus points
```

### Special Weapon Mechanics
```
Special Duration = base_duration + (weapon.power * duration_multiplier)

Example - SuperNova (special type 6):
    flareDuration = 200 + 25 * weapon.power
    // Level 1: 225 frames, Level 11: 475 frames

Example - Zinglon (special type 11):
    flareDuration = 10 + 10 * weapon.power  
    astralDuration = 20 + 10 * weapon.power
    // Both scale with weapon power level
```

## Key Design Insights

### Resource Management Triangle
```
Power Generation → Shield Regeneration ← Weapon Firing
                                ↗ Player Movement
```
The player must balance between shields, weapons, and movement using limited power.

### Weapon Progression System
- Power levels 1-11 provide linear scaling
- Each level increases damage, pattern complexity, or special duration
- Purple balls provide the progression mechanism

### Risk-Reward Mechanics
- Higher power weapons consume more power
- Complex bullet patterns (sine waves) are harder to aim but cover more area
- Shield regeneration pauses during heavy weapon usage

### Frame-Based Precision
All calculations use frame-based timing (30 FPS), making the game highly deterministic and skill-based.
