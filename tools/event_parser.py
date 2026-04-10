#!/usr/bin/env python3
"""
Level Event Extractor for Tyrian
Extracts enemy spawn sequences and gameplay-relevant context events from .lvl binary files.

Usage:
    python event_parser.py                          # tyrian1.lvl, level 1
    python event_parser.py tyrian2.lvl              # tyrian2.lvl, level 1
    python event_parser.py tyrian1.lvl 3            # tyrian1.lvl, level 3
    python event_parser.py tyrian1.lvl --all        # wszystkie poziomy
"""

import struct
import json
import sys
import os

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_path(filename):
    """Zamienia ścieżkę na bezwzględną względem katalogu skryptu."""
    if not os.path.isabs(filename):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)
    return filename


# ---------------------------------------------------------------------------
# Event type catalogue
# Based on JE_eventSystem() in tyrian2.c
# ---------------------------------------------------------------------------

EVENT_TYPES = {
    1:  "starfield_speed",
    2:  "scroll_speed",            # backMove / backMove2 / backMove3
    3:  "scroll_speed_preset",     # preset: backMove=1 z opóźnieniami
    4:  "stop_background",
    5:  "load_enemy_shapes",       # ładuje banki sprite'ów (.shp)
    6:  "spawn_ground_enemy",      # slot 25
    7:  "spawn_top_enemy",         # slot 50
    8:  "disable_stars",
    9:  "enable_stars",
    10: "spawn_ground_enemy2",     # slot 75
    11: "end_level",
    12: "spawn_4x4_ground",        # 4 wrogie w kwadracie 2x2
    13: "disable_random_spawn",    # enemiesActive = false
    14: "enable_random_spawn",     # enemiesActive = true
    15: "spawn_sky_enemy",         # slot 0
    16: "show_text",
    17: "spawn_ground_bottom",     # slot 25, od dołu ekranu (ey=190)
    18: "spawn_sky_bottom",        # slot 0, od dołu ekranu (ey=190)
    19: "enemy_global_move",       # nadpisuje exc/eyc/fixedmovey grupy
    20: "enemy_global_accel",      # zmienia excc/eycc (silnik wahadłowy)
    21: "background3_over_enemy",  # background3over = 1
    22: "background3_under_enemy", # background3over = 0
    23: "spawn_sky_bottom2",       # slot 50 (Top), od dołu (ey=180)
    24: "enemy_global_animate",    # zmienia animację grupy
    25: "enemy_global_damage",     # ustawia armorleft grupy
    26: "small_enemy_adjust",      # przesuwa małe wrogie o (-10,-7)
    27: "enemy_global_accelrev",   # zmienia exrev/eyrev grupy
    28: "top_enemy_under_bg",
    29: "top_enemy_over_bg",
    30: "scroll_speed_alt",        # jak 2, bez efektu na explodeMove
    31: "enemy_fire_override",     # zmienia częstotliwość strzelania grupy
    32: "spawn_enemy_special",     # slot 50, ey=190 (stałe)
    33: "enemy_from_enemy",        # przy śmierci wroga tworzy nowego
    34: "music_fade_start",
    35: "play_song",
    36: "ready_to_end_level",
    37: "set_enemy_frequency",     # częstotliwość random-spawnu
    38: "goto_event_time",         # bezwarunkowy skok do czasu eventu
    39: "enemy_linknum_change",    # przenosi wrogów między grupami
    40: "enemy_continual_damage",
    41: "clear_enemies",           # usuwa wrogów ze slotów
    42: "background3_over2",
    43: "set_background2_over",
    44: "set_color_filter",
    45: "enemy_from_enemy_arcade",
    46: "change_difficulty",
    47: "enemy_armor_set",         # bezpośrednio ustawia armorleft
    48: "background2_opaque",
    49: "spawn_custom_ground",     # slot 25, inline grafika
    50: "spawn_custom_sky",        # slot 0, inline grafika
    51: "spawn_custom_top",        # slot 50, inline grafika
    52: "spawn_custom_ground2",    # slot 75, inline grafika
    53: "force_events",
    54: "jump_event",              # bezwarunkowy skok / return
    55: "enemy_accel_override",    # zmienia xaccel/yaccel grupy
    56: "spawn_ground2_bottom",    # slot 75, od dołu (ey=190)
    57: "super_enemy_254_jump",
    60: "assign_special_enemy",
    61: "jump_if_flag",
    62: "play_sound",
    63: "skip_if_not_2player",
    64: "set_smoothie",
    65: "set_background3x1",
    66: "skip_if_difficulty",
    67: "set_level_timer",
    68: "random_explosions",
    69: "player_invulnerable",
    70: "jump_if_no_enemy_group",
    71: "jump_if_map_position",
    72: "set_background3x1b",
    73: "sky_enemy_over_all",
    74: "enemy_bounce_params",     # ustawia granice odbicia grupy
    75: "select_random_enemy",
    76: "return_active",
    77: "set_map_position",
    78: "increase_galaga_shot_freq",
    79: "set_boss_bar",
    80: "skip_if_2player",
    81: "set_background2_wrap",
    82: "give_special_weapon",
}

# ---------------------------------------------------------------------------
# Event kategoryzacja
# ---------------------------------------------------------------------------

# Eventy tworzące wrogów — pełny schemat pól spawnu
SPAWN_EVENTS = {6, 7, 10, 12, 15, 17, 18, 23, 32, 49, 50, 51, 52, 56}

# Mapowanie: event_type -> (enemy_slot, from_bottom, fixed_screen_y)
# fixed_screen_y: None = oblicz z -28; liczba = stała wartość Y (ignoruje y_offset)
SPAWN_CONFIG = {
    6:  (25, False, None),   # Ground, od góry
    7:  (50, False, None),   # Top, od góry
    10: (75, False, None),   # Ground2, od góry
    12: (25, False, None),   # 4x4 Ground, od góry (slot zależy od eventdat6)
    15: (0,  False, None),   # Sky, od góry
    17: (25, True,  190),    # Ground, od dołu
    18: (0,  True,  190),    # Sky, od dołu
    23: (50, True,  180),    # Top, od dołu
    32: (50, True,  190),    # Special Top, ey=190 stałe (ignoruje y_offset)
    49: (25, False, None),   # Custom Ground
    50: (0,  False, None),   # Custom Sky
    51: (50, False, None),   # Custom Top
    52: (75, False, None),   # Custom Ground2
    56: (75, True,  190),    # Ground2, od dołu
}

# Eventy kontekstowe istotne dla spawnu — wyodrębniane osobno
CONTEXT_EVENTS = {
    2:  "scroll_speed",           # zmiana prędkości tła wpływa na pozycję Y wrogów przy spawnie
    3:  "scroll_speed_preset",
    5:  "load_enemy_shapes",      # wymagane do poprawnego załadowania sprite'ów wrogów
    13: "disable_random_spawn",
    14: "enable_random_spawn",
    19: "enemy_global_move",      # zmiana prędkości/ruchu żyjących wrogów
    20: "enemy_global_accel",     # zmiana silnika wahadłowego żyjących wrogów
    24: "enemy_global_animate",
    25: "enemy_global_damage",
    26: "small_enemy_adjust",     # wpływa na pozycję X/Y przy spawnie
    27: "enemy_global_accelrev",  # zmiana limitów prędkości
    30: "scroll_speed_alt",
    31: "enemy_fire_override",
    33: "enemy_from_enemy",       # tworzy wrogów przy śmierci innych
    37: "set_enemy_frequency",    # zmienia gęstość random-spawnu
    38: "goto_event_time",        # skok — zmienia sekwencję eventów
    39: "enemy_linknum_change",
    40: "enemy_continual_damage",
    41: "clear_enemies",
    46: "change_difficulty",      # wpływa na HP i punkty wrogów
    47: "enemy_armor_set",
    54: "jump_event",             # skok / return
    55: "enemy_accel_override",
    57: "super_enemy_254_jump",
    60: "assign_special_enemy",
    65: "set_background3x1",      # wpływa na obliczenie X dla slotu 50
    72: "set_background3x1b",     # wpływa na obliczenie X/Y dla slotu 50
    74: "enemy_bounce_params",
}

# ---------------------------------------------------------------------------
# Obliczenia pozycji
# ---------------------------------------------------------------------------

def compute_screen_x(raw_x, enemy_slot, map_x, map_x3,
                     background3x1=False, background3x1b=False):
    """
    Oblicza faktyczną pozycję X na ekranie zgodnie z JE_createNewEventEnemy.
    Zwraca None jeśli raw_x == -99 (pozycja pochodzi z danych wroga).
    """
    if raw_x == -99:
        return None

    if enemy_slot == 0:           # Sky
        return raw_x - (map_x - 1) * 24
    elif enemy_slot in (25, 75):  # Ground / Ground2
        return raw_x - (map_x - 1) * 24 - 12
    elif enemy_slot == 50:        # Top
        if background3x1:
            ex = raw_x - (map_x - 1) * 24 - 12
        else:
            ex = raw_x - map_x3 * 24 - 24 * 2 + 6
        if background3x1b:
            ex -= 6
        return ex
    return raw_x


def compute_screen_y_top(enemy_slot, back_move, back_move2, back_move3,
                         y_offset=0, background3x1b=False):
    """
    Oblicza startową pozycję Y dla spawnu od góry (typy 6,7,10,15,49-52).
    Nie uwzględnia smallEnemyAdjust (zależy od rozmiaru konkretnego wroga).
    """
    ey = -28
    if background3x1b and enemy_slot == 50:
        ey += 4   # wyjątek dla Top z background3x1b
    if enemy_slot == 0:
        ey -= back_move2
    elif enemy_slot in (25, 75):
        ey -= back_move
    elif enemy_slot == 50:
        ey -= back_move3
    return ey + y_offset


# ---------------------------------------------------------------------------
# Parsowanie pliku .lvl
# ---------------------------------------------------------------------------

def read_level_header(filename):
    """Wczytuje nagłówek pliku .lvl i zwraca listę offsetów poziomów."""
    with open(filename, 'rb') as f:
        lvl_num = struct.unpack('<H', f.read(2))[0]
        lvl_pos = list(struct.unpack(f'<{lvl_num}i', f.read(4 * lvl_num)))
        lvl_pos.append(f.tell())
    return lvl_num, lvl_pos


def read_level_events(filename, level_offset):
    """
    Wczytuje wszystkie eventy z konkretnego poziomu.
    Zwraca (lista eventów, słownik nagłówka poziomu).
    """
    with open(filename, 'rb') as f:
        f.seek(level_offset)

        map_file   = f.read(1).decode('ascii', errors='ignore')
        shape_file = f.read(1).decode('ascii', errors='ignore')
        map_x      = struct.unpack('<H', f.read(2))[0]
        map_x2     = struct.unpack('<H', f.read(2))[0]
        map_x3     = struct.unpack('<H', f.read(2))[0]

        # Pomiń tablicę levelEnemy (2 bajty na element)
        level_enemy_max = struct.unpack('<H', f.read(2))[0]
        level_enemies   = list(struct.unpack(f'<{level_enemy_max}H',
                                             f.read(level_enemy_max * 2)))
        try:
            max_event = struct.unpack('<H', f.read(2))[0]
        except struct.error:
            print(f"Warning: Could not read max_event at offset {level_offset}")
            return [], {}

        events = []
        for _ in range(max_event):
            raw = f.read(11)
            if len(raw) < 11:
                break
            # Format: eventtime(H) eventtype(B) dat(h) dat2(h) dat3(b) dat5(b) dat6(b) dat4(B)
            # Uwaga: kolejność w pliku to dat3, dat5, dat6, dat4 — nie dat3,dat4,dat5,dat6
            ev = struct.unpack('<H B h h b b b B', raw)
            events.append({
                'eventtime': ev[0],
                'eventtype': ev[1],
                'eventdat':  ev[2],
                'eventdat2': ev[3],
                'eventdat3': ev[4],
                'eventdat5': ev[5],
                'eventdat6': ev[6],
                'eventdat4': ev[7],
            })

    header = {
        'map_file':        map_file,
        'shape_file':      shape_file,
        'map_x':           map_x,
        'map_x2':          map_x2,
        'map_x3':          map_x3,
        'level_enemy_max': level_enemy_max,
        'level_enemies':   level_enemies,
        'max_event':       max_event,
    }
    return events, header


# ---------------------------------------------------------------------------
# Ekstrakcja eventów spawnu
# ---------------------------------------------------------------------------

def extract_spawn_event(event, header, back_move, back_move2, back_move3,
                        background3x1, background3x1b):
    """
    Przetwarza jeden event spawnu na ustrukturyzowany słownik.
    Oblicza screen_x i screen_y na podstawie aktualnego stanu scrollingu i tła.
    """
    etype = event['eventtype']
    cfg   = SPAWN_CONFIG[etype]
    enemy_slot, from_bottom, fixed_y = cfg

    raw_x    = event['eventdat2']
    y_offset = event['eventdat5']

    # Dla typu 12 (4x4) slot zależy od eventdat6 w oryginale — dokumentujemy jako-is
    # eventdat6 jest tam zerowane przed wywołaniem, więc fixed_move_y = 0
    is_4x4 = (etype == 12)

    # --- Pozycja X ---
    screen_x = compute_screen_x(
        raw_x, enemy_slot,
        header['map_x'], header['map_x3'],
        background3x1, background3x1b
    )

    # --- Pozycja Y ---
    if from_bottom:
        if fixed_y is not None and etype in (32, 56):
            # typ 32 i 56: y_offset ignorowane, stałe 190
            screen_y = fixed_y
        else:
            screen_y = fixed_y + y_offset   # 190+y_offset lub 180+y_offset
    else:
        screen_y = compute_screen_y_top(
            enemy_slot, back_move, back_move2, back_move3,
            y_offset, background3x1b
        )

    spawn = {
        'dist':          event['eventtime'],
        'event_type':    etype,
        'event_name':    EVENT_TYPES.get(etype, f"unknown_{etype}"),
        'enemy_slot':    enemy_slot,
        'from_bottom':   from_bottom,
        'enemy_id':      event['eventdat'],
        'raw_x':         raw_x,
        'screen_x':      screen_x,
        'screen_y':      screen_y,
        'y_vel':         event['eventdat3'],
        'y_offset':      y_offset,
        'link_num':      event['eventdat4'],
        'fixed_move_y':  0 if is_4x4 else event['eventdat6'],
        # Aktualny stan scrollingu w momencie spawnu (do symulacji)
        'back_move':     back_move,
        'back_move2':    back_move2,
        'back_move3':    back_move3,
    }

    if is_4x4:
        # Dla 4x4: eventdat6 przed zerowaniem = numer slotu (0-4)
        # faktyczny slot jest ustalany z eventdat6 — zapisujemy surową wartość
        spawn['slot_selector'] = event['eventdat6']
        spawn['enemy_ids'] = [
            event['eventdat'],
            event['eventdat'] + 1,
            event['eventdat'] + 2,
            event['eventdat'] + 3,
        ]

    return spawn


# ---------------------------------------------------------------------------
# Ekstrakcja eventów kontekstowych
# ---------------------------------------------------------------------------

def extract_context_event(event):
    """
    Przetwarza event kontekstowy (nie-spawn, ale istotny dla mechaniki spawnu).
    Zwraca ustrukturyzowany słownik z polami specyficznymi dla danego typu.
    """
    etype = event['eventtype']
    name  = EVENT_TYPES.get(etype, f"unknown_{etype}")

    ctx = {
        'dist':       event['eventtime'],
        'event_type': etype,
        'event_name': name,
    }

    # Dekodowanie pól specyficznych dla każdego typu
    if etype in (2, 30):
        ctx['back_move']  = event['eventdat']
        ctx['back_move2'] = event['eventdat2']
        ctx['back_move3'] = event['eventdat3']

    elif etype == 3:
        ctx['note'] = 'preset: backMove=1 z opóźnieniami (map1YDelayMax=3, map2YDelayMax=2)'

    elif etype == 5:
        ctx['shape_banks'] = [
            event['eventdat'],
            event['eventdat2'],
            event['eventdat3'],
            event['eventdat4'],
        ]

    elif etype in (13, 14):
        ctx['enemies_active'] = (etype == 14)

    elif etype == 19:
        ctx['new_exc']         = event['eventdat']   # -99 = bez zmian
        ctx['new_eyc']         = event['eventdat2']  # -99 = bez zmian
        ctx['scope_selector']  = event['eventdat3']  # 0=wg linknum, 1-3=slot, 99=wszyscy
        ctx['link_num']        = event['eventdat4']
        ctx['anim_cycle']      = event['eventdat5']  # >0 = ustaw enemycycle
        ctx['new_fixedmovey']  = event['eventdat6']  # 0=bez zmian, -99=resetuj do 0

    elif etype == 20:
        ctx['new_excc']       = event['eventdat']    # -99 = bez zmian
        ctx['new_eycc']       = event['eventdat2']   # -99 = bez zmian
        ctx['scope_selector'] = event['eventdat3']
        ctx['link_num']       = event['eventdat4']
        ctx['new_animin']     = event['eventdat5']   # gdy eventdat6>0
        ctx['new_ani']        = event['eventdat6']   # >0 = ustaw ani + aktywuj animację

    elif etype == 24:
        ctx['new_ani']    = event['eventdat']        # >0 = nowy ostatni indeks klatki
        ctx['new_cycle']  = event['eventdat2']       # >0 = nowy enemycycle i animin
        ctx['anim_mode']  = event['eventdat3']       # 0=zawsze, 1=jednorazowa, 2=przy strzale
        ctx['link_num']   = event['eventdat4']

    elif etype == 25:
        ctx['new_armor'] = event['eventdat']
        ctx['link_num']  = event['eventdat4']        # 0 = wszyscy

    elif etype == 26:
        ctx['small_enemy_adjust'] = bool(event['eventdat'])

    elif etype == 27:
        ctx['new_exrev'] = event['eventdat']         # -99 = bez zmian
        ctx['new_eyrev'] = event['eventdat2']        # -99 = bez zmian
        ctx['filter']    = event['eventdat3']        # 1-16 = filtr koloru; 80-89 = selektor
        ctx['link_num']  = event['eventdat4']        # 0 = wszyscy

    elif etype == 31:
        ctx['new_freq']    = [event['eventdat'], event['eventdat2'], event['eventdat3']]
        ctx['link_num']    = event['eventdat4']      # 99 = wszyscy
        ctx['new_launch_freq'] = event['eventdat5']

    elif etype == 33:
        ctx['spawn_on_death_id'] = event['eventdat']
        ctx['link_num']          = event['eventdat4']

    elif etype == 37:
        ctx['enemy_frequency'] = event['eventdat']  # wyższy = rzadszy spawn

    elif etype in (38, 54):
        ctx['jump_to'] = event['eventdat']          # 65535 = return

    elif etype == 39:
        ctx['old_linknum'] = event['eventdat']
        ctx['new_linknum'] = event['eventdat2']

    elif etype == 41:
        ctx['clear_scope'] = 'all' if event['eventdat'] == 0 else 'slot_0_24'

    elif etype == 46:
        ctx['difficulty_delta'] = event['eventdat']
        ctx['only_2player']     = bool(event['eventdat2'])
        ctx['new_damage_rate']  = event['eventdat3']  # 0 = bez zmian

    elif etype == 47:
        ctx['new_armor'] = event['eventdat']
        ctx['link_num']  = event['eventdat4']        # 0 = wszyscy

    elif etype == 55:
        ctx['new_xaccel'] = event['eventdat']        # -99 = bez zmian
        ctx['new_yaccel'] = event['eventdat2']       # -99 = bez zmian
        ctx['link_num']   = event['eventdat4']       # 0 = wszyscy

    elif etype in (65, 72):
        ctx['value'] = event['eventdat']

    elif etype == 74:
        ctx['new_xmaxbounce'] = event['eventdat']    # -99 = bez zmian
        ctx['new_ymaxbounce'] = event['eventdat2']   # -99 = bez zmian
        ctx['link_num']       = event['eventdat4']   # 0 = wszyscy
        ctx['new_xminbounce'] = event['eventdat5']   # -99 = bez zmian
        ctx['new_yminbounce'] = event['eventdat6']   # -99 = bez zmian

    else:
        # Dla pozostałych — zapisz surowe dane
        ctx['dat']  = event['eventdat']
        ctx['dat2'] = event['eventdat2']
        ctx['dat3'] = event['eventdat3']
        ctx['dat4'] = event['eventdat4']
        ctx['dat5'] = event['eventdat5']
        ctx['dat6'] = event['eventdat6']

    return ctx


# ---------------------------------------------------------------------------
# Główna funkcja przetwarzania eventów poziomu
# ---------------------------------------------------------------------------

def process_events(events, header):
    """
    Iteruje po wszystkich eventach poziomu chronologicznie, śledzi stan środowiska
    i zapisuje wszystko w jednej wspólnej osi czasu (timeline).
    """
    timeline = []

    # Stan scrollingu — wartości domyślne z JE_main()
    back_move  = 1
    back_move2 = 2
    back_move3 = 3
    background3x1  = False
    background3x1b = False

    for event in events:
        etype = event['eventtype']

        # --- Aktualizuj stan środowiska (zawsze przed przetworzeniem spawnu) ---
        if etype in (2, 30):
            back_move  = event['eventdat']
            back_move2 = event['eventdat2']
            back_move3 = event['eventdat3']
        elif etype == 3:
            back_move, back_move2, back_move3 = 1, 1, 1
        elif etype == 65:
            background3x1 = (event['eventdat'] == 0)
        elif etype == 72:
            background3x1b = bool(event['eventdat'])

        # --- Przetwarzanie i dodawanie do wspólnej listy ---
        if etype in SPAWN_EVENTS:
            data = extract_spawn_event(
                event, header,
                back_move, back_move2, back_move3,
                background3x1, background3x1b
            )
            data['category'] = 'spawn'  # Dodajemy kategorię dla rozróżnienia
            timeline.append(data)

        elif etype in CONTEXT_EVENTS:
            data = extract_context_event(event)
            data['category'] = 'context' # Dodajemy kategorię dla rozróżnienia
            timeline.append(data)

    return timeline

# ---------------------------------------------------------------------------
# Przetwarzanie pliku
# ---------------------------------------------------------------------------

def process_level_file(filename, level_num=None):
    """
    Przetwarza plik .lvl.
    level_num: 1-based numer poziomu, None = wszystkie poziomy.
    """
    filename = resolve_path(filename)

    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found")
        return None

    lvl_count, lvl_offsets = read_level_header(filename)
    print(f"Found {lvl_count} levels in '{filename}'")

    if level_num is not None:
        if not (1 <= level_num <= lvl_count):
            print(f"Error: Level {level_num} out of range (1–{lvl_count})")
            return None
        level_indices = [level_num - 1]
    else:
        level_indices = range(lvl_count)

    results = {}

    for i in level_indices:
        try:
            events, header = read_level_events(filename, lvl_offsets[i])
            # Teraz dostajemy jedną listę zamiast dwóch
            timeline = process_events(events, header)

            level_key = f"level_{i + 1}"
            results[level_key] = {
                'header':         header,
                'total_events':   len(events),
                'extracted_count': len(timeline),
                'events':         timeline, # Jedna wspólna lista w JSON
            }
            print(f"  Level {i + 1}: {len(events)} events processed into timeline.")
        except Exception as e:
            print(f"Error processing level {i + 1}: {e}")
            import traceback; traceback.print_exc()

    return results


# ---------------------------------------------------------------------------
# Punkt wejścia
# ---------------------------------------------------------------------------

def main():
    DEFAULT_FILE  = "tyrian1.lvl"
    DEFAULT_LEVEL = 1

    args = sys.argv[1:]

    if len(args) == 0:
        lvl_file  = DEFAULT_FILE
        level_num = DEFAULT_LEVEL
        print(f"No arguments — using defaults: '{DEFAULT_FILE}' level {DEFAULT_LEVEL}")

    elif len(args) == 1:
        if args[0] == '--all':
            lvl_file  = DEFAULT_FILE
            level_num = None
            print(f"Processing all levels in '{DEFAULT_FILE}'")
        else:
            lvl_file  = args[0]
            level_num = DEFAULT_LEVEL
            print(f"Processing '{lvl_file}' level {DEFAULT_LEVEL}")

    elif len(args) == 2:
        lvl_file = args[0]
        if args[1] == '--all':
            level_num = None
            print(f"Processing all levels in '{lvl_file}'")
        else:
            try:
                level_num = int(args[1])
                print(f"Processing '{lvl_file}' level {level_num}")
            except ValueError:
                print(f"Error: level number must be an integer, got '{args[1]}'")
                return

    else:
        print(__doc__)
        return

    results = process_level_file(lvl_file, level_num)

    if results:
        output_file = resolve_path("lvl1.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to '{output_file}'")


if __name__ == "__main__":
    main()