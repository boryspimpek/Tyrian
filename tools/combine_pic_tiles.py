#!/usr/bin/env python3
"""
Skrypt do składania 4 kafelków w jeden duży obrazek.
Kafelki są brane z folderu data/enemy_lvl17 i zapisywane do data/big_enemy.
"""

from PIL import Image
import os

# === KONFIGURACJA ===
# Tutaj wpisz nazwy 4 kafelków w kolejności:
# [0] -> offset (0, 26)   - lewy dolny
# [1] -> offset (23, 26)  - prawy dolny
# [2] -> offset (0, 0)    - lewy górny
# [3] -> offset (23, 0)   - prawy górny
TILE_NAMES = [
    "enemy_008_bank1_f00.png",  # offset (0, 26)
    "enemy_009_bank1_f00.png",  # offset (23, 26)
    "enemy_013_bank1_f00.png",  # offset (0, 0)
    "enemy_014_bank1_f00.png",  # offset (23, 0)
]

# Nazwa wyjściowego pliku
OUTPUT_NAME = "enemy_8_9_13_14.png"

# Offsety dla każdego kafelka (lewy górny narożnik)
OFFSETS = [
    (0, 26),   # lewy dolny
    (24, 26),  # prawy dolny
    (0, 0),    # lewy górny
    (24, 0),   # prawy górny
]

# Wymiary pojedynczego kafelka
TILE_WIDTH = 24
TILE_HEIGHT = 28

# === ŚCIEŻKI ===
SCRIPT_DIR = r"C:\Users\borys\projekty\Tyrian\tools"
PROJECT_ROOT = r"C:\Users\borys\projekty\Tyrian"
SOURCE_DIR = r"C:\Users\borys\projekty\Galaxid\data\enemy_lvl17"
OUTPUT_DIR = r"C:\Users\borys\projekty\Tyrian\big_enemy"

def combine_tiles():
    """Składa 4 kafelki w jeden obrazek."""
    
    # Oblicz wymiary wynikowego obrazka
    result_width = 2 * TILE_WIDTH + 8
    result_height = 2 * TILE_HEIGHT + 5
    
    # Utwórz nowy obrazek z przezroczystym tłem (RGBA)
    result_image = Image.new("RGBA", (result_width, result_height), (0, 0, 0, 0))
    
    print(f"Łączenie kafelków w obrazek {result_width}x{result_height}...")
    
    for i, tile_name in enumerate(TILE_NAMES):
        if i >= 4:
            break
            
        source_path = os.path.join(SOURCE_DIR, tile_name)
        
        if not os.path.exists(source_path):
            print(f"BŁĄD: Nie znaleziono pliku: {source_path}")
            return
        
        # Wczytaj kafelek
        tile = Image.open(source_path).convert("RGBA")
        
        # Sprawdź wymiary
        if tile.size != (TILE_WIDTH, TILE_HEIGHT):
            print(f"OSTRZEŻENIE: Kafelek {tile_name} ma wymiary {tile.size}, oczekiwano {(TILE_WIDTH, TILE_HEIGHT)}")
        
        # Pobierz offset
        offset_x, offset_y = OFFSETS[i]
        
        # Wklej kafelek na wynikowy obrazek
        result_image.paste(tile, (offset_x, offset_y), tile)
        
        print(f"  [{i}] {tile_name} -> offset ({offset_x}, {offset_y})")
    
    # Zapisz wynik
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_NAME)
    
    # Upewnij się że folder wyjściowy istnieje
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    result_image.save(output_path)
    print(f"\nZapisano: {output_path}")

if __name__ == "__main__":
    combine_tiles()
