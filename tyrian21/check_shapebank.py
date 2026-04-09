import os
import json
import sys

JSON_FILE = "enemy.json"
BASE_TILES_DIR = "."

def quick_analyze():
    # Wczytaj JSON
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)
    
    # Zbierz wszystkie shapebank
    shapebanks = set()
    for enemy in all_enemies:
        sb = enemy.get("shapebank")
        if sb is not None:
            shapebanks.add(sb)
    
    print("\n=== Analiza shapebank ===")
    print(f"Znalezione wartości: {sorted(shapebanks)}")
    print(f"\nLiczba unikalnych: {len(shapebanks)}")
    print("\n=== Sprawdzanie folderów ===")
    
    # Sprawdź jakie foldery istnieją
    print(f"\nFoldery w {BASE_TILES_DIR}:")
    try:
        all_items = os.listdir(BASE_TILES_DIR)
        folders = [item for item in all_items if os.path.isdir(os.path.join(BASE_TILES_DIR, item))]
        shp_folders = [f for f in folders if 'newsh' in f.lower() or 'extracted' in f.lower()]
        
        if shp_folders:
            print("Znalezione foldery z kafelkami:")
            for folder in sorted(shp_folders):
                print(f"  - {folder}")
        else:
            print("Nie znaleziono folderów z 'newsh' lub 'extracted'")
            print("Dostępne foldery:")
            for folder in folders[:20]:
                print(f"  - {folder}")
    except Exception as e:
        print(f"Błąd: {e}")
    
    # Sprawdź mapowanie dla każdego shapebank
    print("\n=== Mapowanie shapebank -> foldery ===")
    for sb in sorted(shapebanks):
        # Konwersja na nazwę pliku
        if 0 <= sb <= 9:
            expected = f"newsh{sb}"
        elif 10 <= sb <= 35:
            letter = chr(ord('a') + (sb - 10))
            expected = f"newsh{letter}"
        else:
            expected = f"newsh{sb}"
        
        # Szukaj folderu
        found = None
        possible_names = [
            expected,
            f"extracted_{expected}",
            f"{expected}.shp",
            f"extracted_{expected}.shp",
            f"newsh{sb}",
            f"extracted_newsh{sb}"
        ]
        
        for name in possible_names:
            path = os.path.join(BASE_TILES_DIR, name)
            if os.path.exists(path) and os.path.isdir(path):
                found = name
                break
        
        # Jeśli nie znaleziono jako folder, sprawdź jako plik
        if not found:
            for name in possible_names:
                path = os.path.join(BASE_TILES_DIR, name)
                if os.path.exists(path) and os.path.isfile(path):
                    found = f"{name} (plik)"
                    break
        
        if found:
            print(f"  {sb:2d} -> {expected:15s} ✓ {found}")
        else:
            print(f"  {sb:2d} -> {expected:15s} ✗ BRAK")

if __name__ == "__main__":
    quick_analyze()