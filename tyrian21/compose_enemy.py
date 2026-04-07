import os
import json
import sys
from PIL import Image

# --- KONFIGURACJA ---
BASE_TILES_DIR = "."  
OUTPUT_PATH = "assembled_enemies"
JSON_FILE = "enemies.json" 

TILE_W, TILE_H = 12, 14
# ROW_OFFSET to odległość w arkuszu między kafelkiem górnym a dolnym (często 19-20)
ROW_OFFSET = 19 

def get_tiles_path(shapebank):
    return os.path.join(BASE_TILES_DIR, f"extracted_newsh{shapebank}.shp")

def to_s16(val):
    """Konwertuje unsigned 16-bit na signed 16-bit (np. 65535 -> -1)."""
    return val if val < 32768 else val - 65536

def render_complex(idx, egraphic, tiles_dir, out_dir):
    """Logika dla dużych obiektów składanych z instrukcji (MegaShapes)."""
    print(f"-> Wróg {idx}: Tryb Złożony (MegaShape)...")
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0)) # Duży bufor
    
    curr_x, curr_y = 128, 128 # Start od środka
    found_any = False

    # W trybie złożonym egraphic jest listą instrukcji:
    # Małe liczby ujemne to przesunięcia, duże dodatnie to ID kafelka
    for val in egraphic:
        if val == 0: continue
        
        s_val = to_s16(val)
        
        if s_val == -1: # Częsty znacznik końca w Tyrianie
            break
        
        if s_val < 0:
            # Przykład: mała liczba ujemna może przesuwać kursor rysowania
            # Dostosuj wg obserwacji (np. -13 to może być nowa linia)
            curr_y += TILE_H
            curr_x = 128 
            continue

        tile_idx = val - 1
        tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
        
        if os.path.exists(tile_path):
            with Image.open(tile_path).convert("RGBA") as img:
                canvas.paste(img, (curr_x, curr_y), img)
                curr_x += TILE_W
                found_any = True

    if found_any:
        # Kadrowanie do zawartości
        bbox = canvas.getbbox()
        if bbox:
            canvas = canvas.crop(bbox)
        canvas.save(os.path.join(out_dir, f"enemy_{idx:03d}_complex.png"))

def assemble_enemy(enemy_data, out_dir):
    idx = enemy_data.get("index")
    egraphic = enemy_data.get("egraphic", [])
    bank = enemy_data.get("shapebank")
    esize = enemy_data.get("esize", 0)
    ani = enemy_data.get("ani", 1)
    
    if not egraphic: return

    tiles_dir = get_tiles_path(bank)
    if not os.path.exists(tiles_dir):
        print(f"BŁĄD: Brak folderu {tiles_dir}")
        return

    # DECYZJA O TRYBIE
    # Sprawdzamy czy w pierwszych kilku wartościach są flagi ujemne (np. 65535)
    is_complex = any(to_s16(v) < 0 for v in egraphic[:5])

    if is_complex:
        render_complex(idx, egraphic, tiles_dir, out_dir)
        
    elif esize == 0 or esize == 1:
        # TRYB 2x2 (Standardowy statek)
        print(f"-> Wróg {idx} (Bank {bank}): Tryb 2x2 (Animacja)...")
        # W Tyrianie 'ani' mówi ile klatek wziąć z egraphic
        for f_idx in range(min(ani, len(egraphic))):
            base_tile = egraphic[f_idx]
            if base_tile <= 0: continue
            
            start_tile = base_tile - 1
            canvas = Image.new('RGBA', (TILE_W * 2, TILE_H * 2), (0, 0, 0, 0))
            
            # Kafelki w Tyrianie 2x2 są często ułożone: 
            # [T] [T+1]
            # [T+Row] [T+Row+1]
            offsets = [(0, 0, 0), (1, TILE_W, 0), (ROW_OFFSET, 0, TILE_H), (ROW_OFFSET + 1, TILE_W, TILE_H)]
            
            for off, dx, dy in offsets:
                tile_path = os.path.join(tiles_dir, f"block_{start_tile + off:04d}.bmp")
                if os.path.exists(tile_path):
                    with Image.open(tile_path).convert("RGBA") as img:
                        canvas.paste(img, (dx, dy), img)
            
            canvas.save(os.path.join(out_dir, f"enemy_{idx:03d}_f{f_idx:02d}.png"))

    else:
        # TRYB 1x1 (Pociski / Małe obiekty)
        print(f"-> Wróg {idx} (Bank {bank}): Tryb 1x1...")
        for f_idx in range(min(ani, len(egraphic))):
            val = egraphic[f_idx]
            if val <= 0: continue
            
            tile_path = os.path.join(tiles_dir, f"block_{val-1:04d}.bmp")
            if os.path.exists(tile_path):
                with Image.open(tile_path).convert("RGBA") as img:
                    img.save(os.path.join(out_dir, f"enemy_{idx:03d}_f{f_idx:02d}.png"))

def main():
    if not os.path.exists(OUTPUT_PATH): os.makedirs(OUTPUT_PATH)
    if not os.path.exists(JSON_FILE): return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)

    if len(sys.argv) > 1:
        target_idx = int(sys.argv[1])
        enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
        if enemy: assemble_enemy(enemy, OUTPUT_PATH)
    else:
        print("Użycie: python skrypt.py <indeks_wroga>")

if __name__ == "__main__":
    main()