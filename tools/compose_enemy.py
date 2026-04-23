#!/usr/bin/env python3
import os
import json
import sys
import time
from functools import lru_cache
from PIL import Image

BASE_TILES_DIR = r"../tyrian21/extracted_tiles"
OUTPUT_PATH = r"C:\Users\borys\projekty\Galaxid\data\enemy_lvl17"

# Tutaj znajduje się lista przeciwnikow, maja przypisane różne parametry, 
# miedzy innymi "index" co odpowiada "enemy_id" w lvl1.json
JSON_FILE = r"C:\Users\borys\projekty\Galaxid\data\enemies.json"

# Tutaj znajduje sie struktura poziomow, sa tu zapisana lista shapebanks, ktorą musimy wyciągnąć 
# oraz są eventy w ktorych spawnują się wrogowie, potrzebujemy wyciągnąć wszystkich wrogów
LEVELS_FILE = r"C:\Users\borys\projekty\Galaxid\data\lvl17.json"  


def load_level_data(levels_file):
    """
    Wczytuje z pliku poziomu:
      - active_banks: lista shape_banków (z eventu load_enemy_shapes)
      - enemy_ids: zbiór wszystkich enemy_id występujących w levelu
        (suma wrogów ze spawn eventów oraz z level_enemies w headerze)
    """
    with open(levels_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Plik może zawierać wiele poziomów; bierzemy pierwszy klucz
    level_key = next(iter(data))
    lvl = data[level_key]

    # --- shape_banks ---
    active_banks = []
    for event in lvl.get("events", []):
        if event.get("event_name") == "load_enemy_shapes":
            active_banks = event.get("shape_banks", [])
            break  # zakładamy jeden taki event na poziom

    # --- enemy_ids ---
    # Źródło 1: eventy spawnujące wrogów (pole enemy_id)
    spawn_ids = set(
        event["enemy_id"]
        for event in lvl.get("events", [])
        if "enemy_id" in event
    )

    # Źródło 2: eventy 4x4 (pole enemy_ids z listą 4 wrogów składowych)
    multi_ids = set(
        eid
        for event in lvl.get("events", [])
        if "enemy_ids" in event
        for eid in event["enemy_ids"]
    )

    # Źródło 3: level_enemies z headera (dodatkowe sety, bossowie itp.)
    header_ids = set(lvl.get("header", {}).get("level_enemies", []))

    enemy_ids = spawn_ids | multi_ids | header_ids

    return active_banks, enemy_ids


TILE_W, TILE_H = 12, 14

LARGE_ENEMY_OFFSETS = [(-6, -7), (6, -7), (-6, 7), (6, 7)]
LARGE_ENEMY_TILE_OFFSETS = [0, 1, 19, 20]

MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y = 128, 128

# Tablica shapeFile z lvlmast.c (OpenTyrian), indeksowana od 1.
# shapebank wroga -> shapeFile[shapebank - 1] -> litera pliku newsh?.shp
SHAPE_FILE = [
    '2', '4', '7', '8', 'A', 'B', 'C', 'D', 'E', 'F',  #  1-10
    'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',  # 11-20
    'Q', 'R', 'S', 'T', 'U', '5', '#', 'V', '0', '@',  # 21-30
    '3', '^', '5', '9',                                  # 31-34
]

def get_real_bank_id(enemy_shapebank, active_banks=None):
    """
    Zwraca ID banku dla danego wroga.
    
    shapebank wroga to bezpośrednia wartość porównywana z listą aktywnych
    banków levelu (enemySpriteSheetIds w OpenTyrian). Nie jest to indeks slotu.
    
    Wyjątki hardcoded w silniku:
      21 = Coins&Gems (spriteSheet11)
      26 = Two-Player Stuff (spriteSheet10)
    Dla nich zwracamy shapebank bezpośrednio — folder musi istnieć.
    """
    # Wartości hardcoded w silniku — zawsze bezpośrednie
    if enemy_shapebank in (21, 26):
        return enemy_shapebank

    # Jeśli bank wroga jest na liście aktywnych banków levelu — użyj go
    if active_banks and enemy_shapebank in active_banks:
        return enemy_shapebank

    # Bank nieznaleziony w aktywnych bankach levelu
    # (wróg z globalnego banku lub inaczej załadowany)
    return enemy_shapebank

def shapebank_to_foldername(bank_id):
    """
    Mapuje ID banku na nazwę folderu .shp używając tablicy shapeFile
    z OpenTyrian (lvlmast.c).
    bank_id jest 1-based (shapeFile[bank_id - 1]).
    """
    if 1 <= bank_id <= len(SHAPE_FILE):
        letter = SHAPE_FILE[bank_id - 1].lower()
        return f"extracted_newsh{letter}.shp"
    else:
        return f"extracted_newsh{bank_id}.shp"  # fallback

def get_tiles_dir(real_bank_id):
    foldername = shapebank_to_foldername(real_bank_id)
    path = os.path.join(BASE_TILES_DIR, foldername)
    if os.path.exists(path) and os.path.isdir(path):
        return path
    return None

@lru_cache(maxsize=512)
def load_tile_cached(tiles_dir, tile_idx):
    tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
    if os.path.exists(tile_path):
        try:
            with Image.open(tile_path) as img:
                return img.convert("RGBA").copy()
        except Exception:
            return None
    return None

def to_s16(val):
    return val if val < 32768 else val - 65536

def render_frame_1x1(tile_idx, tiles_dir):
    img = load_tile_cached(tiles_dir, tile_idx)
    return img.copy() if img else None

def render_frame_2x2(start_tile, tiles_dir):
    # Canvas musi być wystarczająco duży dla wszystkich offsetów
    # max paste_x = TILE_W + 6 = 18, max paste_y = TILE_H + 7 = 21
    # kafelek 12x14, więc canvas musi być min 30x35
    canvas = Image.new('RGBA', (35, 40), (0, 0, 0, 0))
    found_any = False
    for tile_offset, (dx, dy) in zip(LARGE_ENEMY_TILE_OFFSETS, LARGE_ENEMY_OFFSETS):
        tile_idx = start_tile + tile_offset
        img = load_tile_cached(tiles_dir, tile_idx)
        if img:
            paste_x = TILE_W + dx
            paste_y = TILE_H + dy
            canvas.paste(img, (paste_x, paste_y), img)
            found_any = True
    if found_any:
        return canvas
    return None

def render_megashape(egraphic, tiles_dir):
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    curr_x, curr_y = MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y
    found_any = False
    for val in egraphic:
        if val == 0: continue
        if val == 999: break
        s_val = to_s16(val)
        if s_val < 0:
            if s_val == -1: break
            elif s_val == -2:
                curr_y += TILE_H
                curr_x = MEGASHAPE_CENTER_X
            elif s_val <= -10: curr_x += abs(s_val)
            else: curr_x += TILE_W
            continue
        tile_idx = val - 1
        img = load_tile_cached(tiles_dir, tile_idx)
        if img:
            canvas.paste(img, (curr_x, curr_y), img)
            curr_x += TILE_W
            found_any = True
    if found_any:
        bbox = canvas.getbbox()
        return canvas.crop(bbox) if bbox else canvas
    return None

def save_enemy_image(canvas, out_dir, filename):
    if canvas and canvas.getbbox():
        if canvas.mode == 'RGBA':
            bg = Image.new('RGB', canvas.size, (0, 0, 0))
            bg.paste(canvas, mask=canvas.split()[3])
            canvas = bg
        canvas.save(os.path.join(out_dir, filename), optimize=True)
        return True
    return False

def assemble_enemy(enemy_data, out_dir, active_banks=None):
    idx = enemy_data.get("index")
    egraphic = enemy_data.get("egraphic", [])
    enemy_slot = enemy_data.get("shapebank", 0)
    esize = enemy_data.get("esize", 0)
    ani = enemy_data.get("ani", 1)
    animate = enemy_data.get("animate", 0)
    dani = enemy_data.get("dani", 0)
    edgr = enemy_data.get("edgr", 0)

    # Mapowanie shapebank na fizyczny bank i folder
    real_bank_id = get_real_bank_id(enemy_slot, active_banks)
    tiles_dir = get_tiles_dir(real_bank_id)

    # --- DEBUG: rozwiązanie banku ---
    in_active = active_banks and enemy_slot in active_banks
    bank_source = "aktywny bank levelu" if in_active else "poza aktywną listą (global/hardcoded)"
    folder_name = shapebank_to_foldername(real_bank_id)
    print(f"[{idx:03d}] shapebank={enemy_slot} -> real_bank={real_bank_id} ({bank_source}), folder={folder_name} ({'OK' if tiles_dir else 'BRAK!'})")

    if not tiles_dir:
        print(f"  !!! POMINIĘTY: folder '{shapebank_to_foldername(real_bank_id)}' nie istnieje")
        return False

    is_megashape = any(to_s16(v) < 0 or v == 999 for v in egraphic[:5])
    starts_damaged = dani < 0

    # Logika wyboru klatek
    frames_to_render = list(range(min(ani, len(egraphic)))) if animate != 0 else [0]

    # --- DEBUG: tryb renderowania ---
    render_mode = "megashape" if is_megashape else ("2x2" if esize == 1 else "1x1")
    print(f"  tryb={render_mode}, animate={animate}, ani={ani}, klatki={frames_to_render}, egraphic[:5]={egraphic[:5]}")

    saved_count = 0

    if is_megashape:
        canvas = render_megashape(egraphic, tiles_dir)
        if canvas:
            fname = f"enemy_{idx:03d}_bank{real_bank_id}_mega.png"
            save_enemy_image(canvas, out_dir, fname)
            print(f"  -> zapisano: {fname}")
            saved_count += 1
        else:
            print(f"  !!! POMINIĘTY: render_megashape zwrócił None (pusty canvas)")
    elif esize == 1:
        for f_idx in frames_to_render:
            base_tile = egraphic[f_idx]
            if base_tile > 0 and base_tile != 999:
                canvas = render_frame_2x2(base_tile - 1, tiles_dir)
                if canvas:
                    fname = f"enemy_{idx:03d}_bank{real_bank_id}_f{f_idx:02d}.png"
                    save_enemy_image(canvas, out_dir, fname)
                    print(f"  -> zapisano: {fname} (tile={base_tile})")
                    saved_count += 1
                else:
                    print(f"  !!! klatka {f_idx}: render_frame_2x2 zwrócił None (tile={base_tile}, brak pliku block_{base_tile-1:04d}.bmp?)")
            else:
                print(f"  --- klatka {f_idx}: pominięta (egraphic={base_tile})")
    else:
        for f_idx in frames_to_render:
            val = egraphic[f_idx]
            if val > 0 and val != 999:
                img = render_frame_1x1(val - 1, tiles_dir)
                if img:
                    fname = f"enemy_{idx:03d}_bank{real_bank_id}_f{f_idx:02d}.png"
                    save_enemy_image(img, out_dir, fname)
                    print(f"  -> zapisano: {fname} (tile={val})")
                    saved_count += 1
                else:
                    print(f"  !!! klatka {f_idx}: render_frame_1x1 zwrócił None (tile={val}, brak pliku block_{val-1:04d}.bmp?)")
            else:
                print(f"  --- klatka {f_idx}: pominięta (egraphic={val})")

    if saved_count == 0:
        print(f"  !!! UWAGA: żadna grafika nie została zapisana dla wroga {idx}")

    return True

def main():
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)

    # Wczytaj shape_banks i listę wrogów dynamicznie z pliku poziomu
    active_banks, level_enemy_ids = load_level_data(LEVELS_FILE)
    print(f"Shape banks z {LEVELS_FILE}: {active_banks}")
    print(f"Wrogowie w levelu ({len(level_enemy_ids)} unikalnych): {sorted(level_enemy_ids)}")

    # Filtruj enemies.json do tych, którzy faktycznie występują w levelu
    level_enemies = [e for e in all_enemies if e.get("index") in level_enemy_ids]
    print(f"Znaleziono {len(level_enemies)} wpisów w enemies.json pasujących do levelu.")

    if len(sys.argv) < 2:
        print("Użycie: python compose_enemy.py --all")
        return

    command = sys.argv[1]
    if command == "--all":
        for enemy in level_enemies:
            assemble_enemy(enemy, OUTPUT_PATH, active_banks)
    else:
        target_idx = int(command)
        enemy = next((e for e in level_enemies if e.get("index") == target_idx), None)
        if enemy:
            assemble_enemy(enemy, OUTPUT_PATH, active_banks)
            print(f"Wyrenderowano wroga {target_idx} używając kontekstu banków {active_banks}")
        else:
            print(f"Wróg o indeksie {target_idx} nie występuje w {LEVELS_FILE}.")

if __name__ == "__main__":
    main()