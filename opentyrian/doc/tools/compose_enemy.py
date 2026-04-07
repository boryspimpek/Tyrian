import os
from PIL import Image

# --- KONFIGURACJA ---
TILES_PATH = "extracted_newsh1.shp" 
OUTPUT_PATH = "assembled_enemies"
TILE_W, TILE_H = 12, 14
ROW_OFFSET = 19  # Odległość w pamięci do kafelka poniżej

def assemble_enemy(enemy_data, tiles_dir, out_dir):
    idx = enemy_data.get("index")
    egraphic = enemy_data.get("egraphic", [])
    bank = enemy_data.get("shapebank")
    
    if bank != 1 or not egraphic:
        return

    # Jeśli nie ma wielkich liczb (65523+), to jest to wróg animowany klatka po klatce
    is_animation = not any(v > 32768 for v in egraphic)

    if is_animation:
        print(f"-> Przetwarzanie wroga {idx} (Tryb Animacji 2x2)...")
        frame_count = 0
        for base_tile in egraphic:
            if base_tile <= 0: continue
            
            # KOREKTA: Przesuwamy o -1, bo JSON wskazuje na prawy-górny lub środek
            start_tile = base_tile - 1
            
            canvas = Image.new('RGBA', (24, 28), (0, 0, 0, 0))
            # Siatka 2x2 oparta na przesunięciu 19
            offsets = [
                (0, 0, 0),               # Góra-Lewo
                (1, 12, 0),              # Góra-Prawo
                (ROW_OFFSET, 0, 14),     # Dół-Lewo
                (ROW_OFFSET + 1, 12, 14) # Dół-Prawo
            ]
            
            found = False
            for off, dx, dy in offsets:
                tile_path = os.path.join(tiles_dir, f"block_{start_tile + off:04d}.bmp")
                if os.path.exists(tile_path):
                    with Image.open(tile_path) as img:
                        canvas.paste(img.convert("RGBA"), (dx, dy))
                        found = True
            
            if found:
                out_fn = os.path.join(out_dir, f"enemy_{idx:03d}_frame_{frame_count:02d}.png")
                canvas.save(out_fn)
                frame_count += 1
    
    else:
        print(f"-> Przetwarzanie wroga {idx} (Tryb Złożony)...")
        # Tworzymy większe płótno dla dużych statków
        canvas = Image.new('RGBA', (300, 300), (0, 0, 0, 0))
        curr_x, curr_y = 0, 0
        found_any = False
        
        for val in egraphic:
            if val == 0: continue
            if val == 27: break
            
            if val > 32768: # Np. 65523 -> Nowa linia (powrót o 13 kafelków)
                curr_x = 0
                curr_y += TILE_H
            else:
                # Tutaj też stosujemy korektę -1, jeśli statki złożone są rozcięte
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
                out_fn = os.path.join(out_dir, f"enemy_{idx:03d}_full.png")
                canvas.crop(bbox).save(out_fn)

def main():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Tutaj możesz wkleić całą listę JSON lub wczytać z pliku
    # Przykład dla Twoich dwóch typów wrogów:
    enemies_json = [
        {
            "index": 156, "shapebank": 1, 
            "egraphic": [77, 79, 81, 83, 85, 87, 89, 91, 93, 115, 117, 119, 0, 0, 0, 0, 0, 0, 0, 0]
        },
    ]

    # Jeśli masz plik, użyj:
    # with open('enemies.json', 'r') as f:
    #     enemies_json = json.load(f)

    for enemy in enemies_json:
        assemble_enemy(enemy, TILES_PATH, OUTPUT_PATH)
    
    print("\nZakończono! Sprawdź folder 'assembled_enemies'.")

if __name__ == "__main__":
    main()