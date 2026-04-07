import os
import json
import sys
from PIL import Image

# --- KONFIGURACJA ŚCIEŻEK ---
# Zakładamy, że foldery z kafelkami są w tym samym miejscu co skrypt
BASE_TILES_DIR = "."  # Miejsce, gdzie są foldery 'extracted_newshX.shp'
OUTPUT_PATH = "assembled_enemies"
JSON_FILE = "enemies.json"  # Nazwa Twojego pliku z danymi

TILE_W, TILE_H = 12, 14
ROW_OFFSET = 19 

def get_tiles_path(shapebank):
    """Zwraca ścieżkę do folderu na podstawie numeru banku."""
    folder_name = f"extracted_newsh{shapebank}.shp"
    return os.path.join(BASE_TILES_DIR, folder_name)

def assemble_enemy(enemy_data, out_dir):
    idx = enemy_data.get("index")
    egraphic = enemy_data.get("egraphic", [])
    bank = enemy_data.get("shapebank")
    
    if not egraphic:
        print(f"Brak danych graficznych dla wroga {idx}")
        return

    tiles_dir = get_tiles_path(bank)
    if not os.path.exists(tiles_dir):
        print(f"BŁĄD: Nie znaleziono folderu {tiles_dir} dla banku {bank}")
        return

    # Logika sprawdzania czy to animacja czy złożony
    is_animation = not any(v > 32768 for v in egraphic)

    if is_animation:
        print(f"-> Wróg {idx} (Bank {bank}): Generowanie klatek animacji...")
        frame_count = 0
        for base_tile in egraphic:
            if base_tile <= 0: continue
            start_tile = base_tile - 1
            canvas = Image.new('RGBA', (24, 28), (0, 0, 0, 0))
            offsets = [(0, 0, 0), (1, 12, 0), (ROW_OFFSET, 0, 14), (ROW_OFFSET + 1, 12, 14)]
            found = False
            for off, dx, dy in offsets:
                tile_path = os.path.join(tiles_dir, f"block_{start_tile + off:04d}.bmp")
                if os.path.exists(tile_path):
                    with Image.open(tile_path) as img:
                        canvas.paste(img.convert("RGBA"), (dx, dy))
                        found = True
            if found:
                canvas.save(os.path.join(out_dir, f"enemy_{idx:03d}_f{frame_count:02d}.png"))
                frame_count += 1
    else:
        print(f"-> Wróg {idx} (Bank {bank}): Generowanie pełnego statku...")
        canvas = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
        curr_x, curr_y = 0, 0
        found_any = False
        for val in egraphic:
            if val == 0: continue
            if val == 27: break
            if val > 32768:
                curr_x = 0
                curr_y += TILE_H
            else:
                tile_idx = val - 1 
                tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
                if os.path.exists(tile_path):
                    with Image.open(tile_path) as img:
                        canvas.paste(img.convert("RGBA"), (curr_x, curr_y))
                        found_any = True
                curr_x += TILE_W
        if found_any:
            bbox = canvas.getbbox()
            if bbox:
                canvas.crop(bbox).save(os.path.join(out_dir, f"enemy_{idx:03d}_full.png"))

def main():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Wczytywanie JSON
    if not os.path.exists(JSON_FILE):
        print(f"BŁĄD: Nie znaleziono pliku {JSON_FILE}")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)

    # Pobieranie indeksu z argumentu linii komend
    if len(sys.argv) > 1:
        target_idx = int(sys.argv[1])
        # Szukamy wroga o podanym indeksie
        enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
        if enemy:
            assemble_enemy(enemy, OUTPUT_PATH)
            print("Zakończono.")
        else:
            print(f"Nie znaleziono wroga o indeksie {target_idx}")
    else:
        print("Użycie: python skrypt.py <indeks_wroga>")
        print("Przykład: python skrypt.py 156")

if __name__ == "__main__":
    main()