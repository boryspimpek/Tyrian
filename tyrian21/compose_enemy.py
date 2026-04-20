#!/usr/bin/env python3
import os
import json
import sys
import time
from functools import lru_cache
from PIL import Image

BASE_TILES_DIR = "."
OUTPUT_PATH = "extracted_enemy"
JSON_FILE = "enemies.json"
LEVELS_FILE = "levels.json"  # Załóżmy, że tu masz strukturę poziomów

TILE_W, TILE_H = 12, 14

LARGE_ENEMY_OFFSETS = [(-6, -7), (6, -7), (-6, 7), (6, 7)]
LARGE_ENEMY_TILE_OFFSETS = [0, 1, 19, 20]

MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y = 128, 128

def get_real_bank_id(enemy_slot, active_banks=None):
    """
    Tłumaczy slot wroga na fizyczny bank, zakładając że sloty 
    w enemies.json zaczynają się od 1.
    """
    if active_banks:
        # Jeśli wróg ma slot 1, bierzemy active_banks[0]
        # Jeśli wróg ma slot 2, bierzemy active_banks[1] itd.
        idx = enemy_slot - 1 
        if 0 <= idx < len(active_banks):
            return active_banks[idx]
    
    # Jeśli slotu nie ma w tablicy poziomu (np. slot 9), 
    # zwracamy go bezpośrednio (Global Bank)
    return enemy_slot
    
def shapebank_to_foldername(real_bank_id):
    """Mapuje fizyczny ID banku na nazwę folderu."""
    if 0 <= real_bank_id <= 9:
        return f"extracted_newsh{real_bank_id}.shp"
    elif 10 <= real_bank_id <= 35:
        # 10 -> a, 11 -> b, itd.
        letter = chr(ord('a') + (real_bank_id - 10))
        return f"extracted_newsh{letter}.shp"
    elif real_bank_id == 26: # Specyficzny przypadek dla Tyriana
        return "extracted_newsh~.shp"
    else:
        return f"extracted_newsh{real_bank_id}.shp"

def get_tiles_dir(real_bank_id):
    foldername = shapebank_to_foldername(real_bank_id)
    path = os.path.join(BASE_TILES_DIR, foldername)
    if os.path.exists(path) and os.path.isdir(path):
        return path
    # Próba bez prefiksu "extracted_"
    fallback = foldername.replace("extracted_", "")
    path = os.path.join(BASE_TILES_DIR, fallback)
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
    canvas = Image.new('RGBA', (TILE_W * 2, TILE_H * 2), (0, 0, 0, 0))
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
        bbox = canvas.getbbox()
        return canvas.crop(bbox) if bbox else canvas
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

    # KLUCZOWA ZMIANA: Mapowanie slotu na fizyczny bank
    real_bank_id = get_real_bank_id(enemy_slot, active_banks)
    tiles_dir = get_tiles_dir(real_bank_id)

    if not tiles_dir:
        print(f"! BŁĄD: Brak folderu dla real_bank_id={real_bank_id} (slot {enemy_slot}, wróg {idx})")
        return False

    is_megashape = any(to_s16(v) < 0 or v == 999 for v in egraphic[:5])
    starts_damaged = dani < 0

    # Logika wyboru klatek
    frames_to_render = list(range(min(ani, len(egraphic)))) if animate != 0 else [0]

    if is_megashape:
        canvas = render_megashape(egraphic, tiles_dir)
        if canvas: save_enemy_image(canvas, out_dir, f"enemy_{idx:03d}_bank{real_bank_id}_mega.png")
    elif esize == 1:
        for f_idx in frames_to_render:
            base_tile = egraphic[f_idx]
            if base_tile > 0 and base_tile != 999:
                canvas = render_frame_2x2(base_tile - 1, tiles_dir)
                if canvas: save_enemy_image(canvas, out_dir, f"enemy_{idx:03d}_bank{real_bank_id}_f{f_idx:02d}.png")
    else:
        for f_idx in frames_to_render:
            val = egraphic[f_idx]
            if val > 0 and val != 999:
                img = render_frame_1x1(val - 1, tiles_dir)
                if img: save_enemy_image(img, out_dir, f"enemy_{idx:03d}_bank{real_bank_id}_f{f_idx:02d}.png")

    return True

def main():
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)

    # Przykładowa lista banków z lvl17.json:
    # W prawdziwym systemie powinienem to wczytywać dynamicznie dla każdego poziomu.
    active_banks_context = [1, 2, 9, 4] 

    if len(sys.argv) < 2:
        print("Użycie: python script.py <indeks>|--all")
        return

    command = sys.argv[1]
    if command == "--all":
        for enemy in all_enemies:
            assemble_enemy(enemy, OUTPUT_PATH, active_banks_context)
    else:
        target_idx = int(command)
        enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
        if enemy:
            assemble_enemy(enemy, OUTPUT_PATH, active_banks_context)
            print(f"Wyrenderowano wroga {target_idx} używając kontekstu banków {active_banks_context}")

if __name__ == "__main__":
    main()