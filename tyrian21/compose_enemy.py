#!/usr/bin/env python3
import os
import json
import sys
import time
from functools import lru_cache
from PIL import Image

BASE_TILES_DIR = "."
OUTPUT_PATH = "enemy_lvl1"
JSON_FILE = "enemies.json"

TILE_W, TILE_H = 12, 14

LARGE_ENEMY_OFFSETS = [(-6, -7), (6, -7), (-6, 7), (6, 7)]
LARGE_ENEMY_TILE_OFFSETS = [0, 1, 19, 20]

MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y = 128, 128

def shapebank_to_foldername(shapebank):
    if 0 <= shapebank <= 9:
        return f"extracted_newsh{shapebank}.shp"
    elif 10 <= shapebank <= 25:
        letter = chr(ord('a') + (shapebank - 10))
        return f"extracted_newsh{letter}.shp"
    elif shapebank == 26:
        return "extracted_newsh~.shp"
    else:
        return f"extracted_newsh{shapebank}.shp"

def get_tiles_dir(shapebank):
    foldername = shapebank_to_foldername(shapebank)
    path = os.path.join(BASE_TILES_DIR, foldername)
    if os.path.exists(path) and os.path.isdir(path):
        return path
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
        except Exception as e:
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
        if bbox:
            canvas = canvas.crop(bbox)
        return canvas
    return None

def render_megashape(egraphic, tiles_dir):
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    curr_x, curr_y = MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y
    found_any = False
    
    for val in egraphic:
        if val == 0:
            continue
        if val == 999:
            break
        
        s_val = to_s16(val)
        
        if s_val < 0:
            if s_val == -1:
                break
            elif s_val == -2:
                curr_y += TILE_H
                curr_x = MEGASHAPE_CENTER_X
            elif s_val <= -10:
                curr_x += abs(s_val)
            else:
                curr_x += TILE_W
            continue
        
        tile_idx = val - 1
        img = load_tile_cached(tiles_dir, tile_idx)
        
        if img:
            canvas.paste(img, (curr_x, curr_y), img)
            curr_x += TILE_W
            found_any = True
    
    if found_any:
        bbox = canvas.getbbox()
        if bbox:
            canvas = canvas.crop(bbox)
        return canvas
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

def assemble_enemy(enemy_data, out_dir):
    idx = enemy_data.get("index")
    egraphic = enemy_data.get("egraphic", [])
    shapebank = enemy_data.get("shapebank")
    esize = enemy_data.get("esize", 0)
    ani = enemy_data.get("ani", 1)
    animate = enemy_data.get("animate", 0)
    dani = enemy_data.get("dani", 0)
    edgr = enemy_data.get("edgr", 0)
    
    if not egraphic:
        print(f"! Pomijam wroga {idx}: brak danych egraphic")
        return False
    
    tiles_dir = get_tiles_dir(shapebank)
    if not tiles_dir:
        print(f"! BŁĄD: Nie można znaleźć kafelków dla shapebank={shapebank} (wróg {idx})")
        return False
    
    is_megashape = False
    for v in egraphic[:10]:
        if v == 999 or to_s16(v) < 0:
            is_megashape = True
            break
    
    starts_damaged = dani < 0
    
    if is_megashape:
        canvas = render_megashape(egraphic, tiles_dir)
        if canvas:
            save_enemy_image(canvas, out_dir, f"enemy_{idx:03d}_megashape.png")
        
        if edgr > 0 and edgr != 999:
            canvas_damaged = render_megashape([edgr], tiles_dir)
            if canvas_damaged:
                save_enemy_image(canvas_damaged, out_dir, f"enemy_{idx:03d}_megashape_damaged.png")
        return True
    
    if animate == 0 or animate == 2:
        frames_to_render = [0]
    else:
        frames_to_render = list(range(min(ani, len(egraphic))))
    
    if esize == 1:
        for f_idx in frames_to_render:
            if f_idx >= len(egraphic):
                continue
            base_tile = egraphic[f_idx]
            if base_tile <= 0 or base_tile == 999:
                continue
            start_tile = base_tile - 1
            canvas = render_frame_2x2(start_tile, tiles_dir)
            if canvas:
                suffix = "_damaged" if starts_damaged else ""
                save_enemy_image(canvas, out_dir, f"enemy_{idx:03d}_f{f_idx:02d}{suffix}.png")
    
    elif esize == 0:
        for f_idx in frames_to_render:
            if f_idx >= len(egraphic):
                continue
            val = egraphic[f_idx]
            if val <= 0 or val == 999:
                continue
            tile_idx = val - 1
            img = render_frame_1x1(tile_idx, tiles_dir)
            if img:
                suffix = "_damaged" if starts_damaged else ""
                save_enemy_image(img, out_dir, f"enemy_{idx:03d}_f{f_idx:02d}{suffix}.png")
    
    else:
        print(f"  ! Nieznana wartość esize={esize} dla wroga {idx}")
        return False
    
    if edgr > 0 and edgr != 999 and not starts_damaged:
        if esize == 1:
            start_tile = edgr - 1
            canvas = render_frame_2x2(start_tile, tiles_dir)
            if canvas:
                save_enemy_image(canvas, out_dir, f"enemy_{idx:03d}_damaged.png")
        elif esize == 0:
            img = render_frame_1x1(edgr - 1, tiles_dir)
            if img:
                save_enemy_image(img, out_dir, f"enemy_{idx:03d}_damaged.png")
    
    return True

def main():
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    if not os.path.exists(JSON_FILE):
        print(f"Błąd: Nie znaleziono pliku {JSON_FILE}")
        return
    
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)
    
    if len(sys.argv) < 2:
        print("Użycie: python compose_enemy.py <indeks>|--all")
        return
    
    command = sys.argv[1]
    
    if command == "--all":
        print(f"Renderowanie {len(all_enemies)} wrogów -> {OUTPUT_PATH}")
        start_time = time.time()
        success = fail = 0
        
        for i, enemy in enumerate(all_enemies, 1):
            try:
                if assemble_enemy(enemy, OUTPUT_PATH):
                    success += 1
                else:
                    fail += 1
                if i % 50 == 0:
                    print(f"  {i}/{len(all_enemies)}")
            except Exception as e:
                print(f"  Błąd {enemy.get('index')}: {e}")
                fail += 1
        
        elapsed = time.time() - start_time
        print(f"Zakończono: {success} sukces, {fail} błędy, {elapsed:.1f}s, {len([f for f in os.listdir(OUTPUT_PATH) if f.endswith('.png')])} plików")
    else:
        try:
            target_idx = int(command)
            enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
            if enemy and assemble_enemy(enemy, OUTPUT_PATH):
                print(f"✅ Wróg {target_idx} wyrenderowany")
            else:
                print(f"❌ Błąd renderowania wroga {target_idx}")
        except ValueError:
            print("Nieznana komenda")

if __name__ == "__main__":
    main()