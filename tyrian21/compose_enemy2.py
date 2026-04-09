import os
import json
import sys
from PIL import Image

# --- KONFIGURACJA ---
BASE_TILES_DIR = "."  
OUTPUT_PATH = "assembled_enemies"
JSON_FILE = "enemy.json" 

TILE_W, TILE_H = 12, 14

# Offsets dla dużych wrogów (esize=1)
LARGE_ENEMY_OFFSETS = [(-6, -7), (6, -7), (-6, 7), (6, 7)]
LARGE_ENEMY_TILE_OFFSETS = [0, 1, 19, 20]

# Środek canvasu dla MegaShape
MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y = 128, 128

# --- MAPOWANIE SHAPEBANK NA NAZWY FOLDERÓW (na podstawie Twoich plików) ---
def shapebank_to_foldername(shapebank):
    """
    Konwertuje wartość shapebank na nazwę folderu z kafelkami.
    Na podstawie rzeczywistych nazw folderów z ekstraktora.
    """
    if 0 <= shapebank <= 9:
        return f"extracted_newsh{shapebank}.shp"
    elif 10 <= shapebank <= 25:
        # a-p (10=a, 11=b, ..., 25=p)
        letter = chr(ord('a') + (shapebank - 10))
        return f"extracted_newsh{letter}.shp"
    elif shapebank == 26:
        # Brakuje newshq - może to błąd w danych lub specjalny przypadek
        # Spróbujmy newsh~ lub newsh#
        print(f"  UWAGA: shapebank=26 (newshq) - brak folderu, próbuję alternatyw")
        return None  # Zwróć None, zostanie obsłużone w get_tiles_dir
    elif 27 <= shapebank <= 29:
        # r, s, t (27=r, 28=s, 29=t)
        letter = chr(ord('a') + (shapebank - 10))
        return f"extracted_newsh{letter}.shp"
    else:
        # Pozostałe wartości (30+)
        return f"extracted_newsh{shapebank}.shp"

def get_tiles_dir(shapebank):
    """
    Zwraca ścieżkę do folderu z kafelkami dla danego shapebank.
    """
    # Specjalne przypadki dla brakujących folderów
    if shapebank == 26:
        # Próbuj alternatywnych folderów dla newshq
        alternatives = [
            "extracted_newsh~.shp",
            "extracted_newsh#.shp",
            "extracted_newsh^.shp",
            "extracted_newshq.shp",  # na wypadek gdybyś dodał później
        ]
        for alt in alternatives:
            path = os.path.join(BASE_TILES_DIR, alt)
            if os.path.exists(path) and os.path.isdir(path):
                print(f"  -> Dla shapebank=26 używam alternatywy: {alt}")
                return path
        print(f"  ! Brak folderu dla shapebank=26 (newshq)")
        return None
    
    # Normalne mapowanie
    foldername = shapebank_to_foldername(shapebank)
    if not foldername:
        return None
    
    path = os.path.join(BASE_TILES_DIR, foldername)
    if os.path.exists(path) and os.path.isdir(path):
        return path
    
    # Jeśli nie znaleziono, spróbuj bez 'extracted_' prefixu
    fallback = foldername.replace("extracted_", "")
    path = os.path.join(BASE_TILES_DIR, fallback)
    if os.path.exists(path) and os.path.isdir(path):
        return path
    
    print(f"  ! Nie znaleziono folderu dla shapebank={shapebank}: {foldername}")
    return None

def to_s16(val):
    """Konwertuje unsigned 16-bit na signed 16-bit."""
    return val if val < 32768 else val - 65536

def render_frame_1x1(tile_idx, tiles_dir):
    """Renderuje pojedynczy kafelek 1x1."""
    tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
    if os.path.exists(tile_path):
        with Image.open(tile_path).convert("RGBA") as img:
            return img.copy()
    return None

def render_frame_2x2(start_tile, tiles_dir):
    """Renderuje ramkę 2x2 dla dużego wroga (esize=1)."""
    canvas = Image.new('RGBA', (TILE_W * 2, TILE_H * 2), (0, 0, 0, 0))
    
    for tile_offset, (dx, dy) in zip(LARGE_ENEMY_TILE_OFFSETS, LARGE_ENEMY_OFFSETS):
        tile_idx = start_tile + tile_offset
        tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
        
        if os.path.exists(tile_path):
            with Image.open(tile_path).convert("RGBA") as img:
                paste_x = TILE_W + dx
                paste_y = TILE_H + dy
                canvas.paste(img, (paste_x, paste_y), img)
    
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    return canvas

def render_megashape(egraphic, tiles_dir):
    """Renderuje złożony obiekt MegaShape."""
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
        tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
        
        if os.path.exists(tile_path):
            with Image.open(tile_path).convert("RGBA") as img:
                canvas.paste(img, (curr_x, curr_y), img)
                curr_x += TILE_W
                found_any = True
    
    if found_any:
        bbox = canvas.getbbox()
        if bbox:
            canvas = canvas.crop(bbox)
        return canvas
    return None

def get_frames_to_render(ani, animate_mode, egraphic_len):
    """Określa które klatki animacji należy renderować."""
    if animate_mode == 0:
        return [0]
    elif animate_mode == 1:
        max_frames = min(ani, egraphic_len)
        return list(range(max_frames))
    elif animate_mode == 2:
        print("    -> animate=2 (animacja tylko przy strzale) - renderuję pierwszą klatkę")
        return [0]
    else:
        return list(range(min(ani, egraphic_len)))

def assemble_enemy(enemy_data, out_dir):
    """Główna funkcja składająca wroga z danych."""
    idx = enemy_data.get("index")
    egraphic = enemy_data.get("egraphic", [])
    shapebank = enemy_data.get("shapebank")
    esize = enemy_data.get("esize", 0)
    ani = enemy_data.get("ani", 1)
    animate = enemy_data.get("animate", 0)
    dani = enemy_data.get("dani", 0)
    
    if not egraphic:
        print(f"! Pomijam wroga {idx}: brak danych egraphic")
        return
    
    # Pobieramy folder z kafelkami dla danego shapebank
    tiles_dir = get_tiles_dir(shapebank)
    if not tiles_dir:
        print(f"! BŁĄD: Nie można znaleźć kafelków dla shapebank={shapebank} (wróg {idx})")
        return
    
    print(f"-> Wróg {idx}: shapebank={shapebank} -> {os.path.basename(tiles_dir)}")
    
    if dani < 0:
        print(f"  Zaczyna jako uszkodzony (dani={dani})")
    
    # Sprawdzamy czy to MegaShape
    is_megashape = False
    for v in egraphic[:10]:
        if v == 999 or to_s16(v) < 0:
            is_megashape = True
            break
    
    if is_megashape:
        print(f"  Tryb MegaShape (złożony)...")
        canvas = render_megashape(egraphic, tiles_dir)
        if canvas:
            canvas.save(os.path.join(out_dir, f"enemy_{idx:03d}_megashape.png"))
        else:
            print(f"  ! Nie udało się wyrenderować MegaShape")
        return
    
    frames_to_render = get_frames_to_render(ani, animate, len(egraphic))
    
    if esize == 1:
        print(f"  Tryb 2x2 (duży), animate={animate}, klatki={frames_to_render}")
        for f_idx in frames_to_render:
            if f_idx >= len(egraphic):
                continue
            base_tile = egraphic[f_idx]
            if base_tile <= 0 or base_tile == 999:
                continue
            start_tile = base_tile - 1
            canvas = render_frame_2x2(start_tile, tiles_dir)
            if canvas:
                damage_suffix = "_damaged" if dani < 0 else ""
                canvas.save(os.path.join(out_dir, f"enemy_{idx:03d}_f{f_idx:02d}{damage_suffix}.png"))
    
    elif esize == 0:
        print(f"  Tryb 1x1, animate={animate}, klatki={frames_to_render}")
        for f_idx in frames_to_render:
            if f_idx >= len(egraphic):
                continue
            val = egraphic[f_idx]
            if val <= 0 or val == 999:
                continue
            tile_idx = val - 1
            img = render_frame_1x1(tile_idx, tiles_dir)
            if img:
                damage_suffix = "_damaged" if dani < 0 else ""
                img.save(os.path.join(out_dir, f"enemy_{idx:03d}_f{f_idx:02d}{damage_suffix}.png"))
    
    else:
        print(f"  ! Nieznana wartość esize={esize}")

def analyze_shapebank_values(all_enemies):
    """Analizuje wszystkie wartości shapebank w pliku JSON."""
    shapebanks = set()
    for enemy in all_enemies:
        sb = enemy.get("shapebank")
        if sb is not None:
            shapebanks.add(sb)
    
    print("\n=== Analiza shapebank ===")
    print(f"Znalezione unikalne wartości shapebank: {sorted(shapebanks)}")
    print(f"\nLiczba wrogów: {len(all_enemies)}")
    print("\nSzczegółowe mapowanie:")
    print("-" * 60)
    
    missing_folders = []
    for sb in sorted(shapebanks):
        tiles_dir = get_tiles_dir(sb)
        if tiles_dir:
            print(f"  {sb:2d} -> {os.path.basename(tiles_dir)} ✓")
        else:
            print(f"  {sb:2d} -> BRAK FOLDERU ✗")
            missing_folders.append(sb)
    
    if missing_folders:
        print(f"\n⚠️ Brakujące foldery dla shapebank: {missing_folders}")
        print("  Dla shapebank=26 (newshq) możesz:")
        print("  1. Skopiować któryś z istniejących folderów (np. extracted_newsh~.shp)")
        print("  2. Lub zignorować wrogów z tym shapebank (mogą nie występować w grze)")
    
    # Policz wrogów dla każdego shapebank
    print("\n=== Statystyka wrogów według shapebank ===")
    sb_count = {}
    for enemy in all_enemies:
        sb = enemy.get("shapebank")
        if sb is not None:
            sb_count[sb] = sb_count.get(sb, 0) + 1
    
    for sb in sorted(sb_count.keys()):
        tiles_dir = get_tiles_dir(sb)
        status = "✓" if tiles_dir else "✗"
        print(f"  {sb:2d}: {sb_count[sb]:3d} wrogów {status}")

def main():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    if not os.path.exists(JSON_FILE):
        print(f"Błąd: Nie znaleziono pliku {JSON_FILE}")
        return
    
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)
    
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python compose_enemy.py <indeks>       - renderuj konkretnego wroga")
        print("  python compose_enemy.py --all          - renderuj wszystkich wrogów")
        print("  python compose_enemy.py --info <indeks> - pokaż informacje o wrogu")
        print("  python compose_enemy.py --analyze      - analizuj wszystkie shapebank")
        return
    
    command = sys.argv[1]
    
    if command == "--analyze":
        analyze_shapebank_values(all_enemies)
    
    elif command == "--info" and len(sys.argv) > 2:
        target_idx = int(sys.argv[2])
        enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
        if enemy:
            print_enemy_info(enemy)
        else:
            print(f"Nie znaleziono wroga o indeksie {target_idx}")
    
    elif command == "--all":
        print(f"Renderowanie wszystkich {len(all_enemies)} wrogów...")
        success_count = 0
        fail_count = 0
        for enemy in all_enemies:
            try:
                assemble_enemy(enemy, OUTPUT_PATH)
                success_count += 1
            except Exception as e:
                print(f"  Błąd przy wrogu {enemy.get('index')}: {e}")
                fail_count += 1
        print(f"\nZakończono! Sukces: {success_count}, Błędy: {fail_count}")
    
    else:
        try:
            target_idx = int(command)
            enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
            if enemy:
                assemble_enemy(enemy, OUTPUT_PATH)
            else:
                print(f"Nie znaleziono wroga o indeksie {target_idx}")
        except ValueError:
            print(f"Nieznana komenda: {command}")

def print_enemy_info(enemy_data):
    """Wyświetla szczegółowe informacje o wrogu."""
    idx = enemy_data.get("index")
    shapebank = enemy_data.get("shapebank")
    print(f"\n=== Informacje o wrogu {idx} ===")
    print(f"  shapebank: {shapebank}")
    print(f"  ani: {enemy_data.get('ani')}")
    print(f"  tur: {enemy_data.get('tur')}")
    print(f"  freq: {enemy_data.get('freq')}")
    print(f"  armor: {enemy_data.get('armor')}")
    print(f"  esize: {enemy_data.get('esize')}")
    print(f"  animate: {enemy_data.get('animate')}")
    print(f"  value: {enemy_data.get('value')}")

if __name__ == "__main__":
    main()