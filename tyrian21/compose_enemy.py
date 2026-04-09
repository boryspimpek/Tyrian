#!/usr/bin/env python3
"""
compose_enemy2.py - Składanie wrogów z kafelków na podstawie danych z JSON
Zgodny z dokumentacją z tyrian2.c
"""

import os
import json
import sys
import time
from functools import lru_cache
from PIL import Image

# --- KONFIGURACJA ---
BASE_TILES_DIR = "."
OUTPUT_PATH = "assembled_enemies"
JSON_FILE = "enemy.json"

TILE_W, TILE_H = 12, 14

# Offsets dla dużych wrogów (esize=1) - zgodne z tyrian2.c linia ~1480
LARGE_ENEMY_OFFSETS = [(-6, -7), (6, -7), (-6, 7), (6, 7)]
LARGE_ENEMY_TILE_OFFSETS = [0, 1, 19, 20]

# Środek canvasu dla MegaShape
MEGASHAPE_CENTER_X, MEGASHAPE_CENTER_Y = 128, 128

# Specjalne mapowania dla shapebank (zgodne z tyrian2.c linia ~2560-2570)
SPECIAL_SHAPEBANKS = {
    21: "coins_gems",      # spriteSheet11 - monety i klejnoty
    26: "two_player",      # spriteSheet10 - rzeczy dla dwóch graczy
}

# Mapowanie shapebank 26 na istniejący folder (jeśli brakuje newshq)
SHAPEBANK_26_FALLBACK = "extracted_newsh~.shp"  # lub "extracted_newshq.shp"

# --- MAPOWANIE SHAPEBANK NA NAZWY FOLDERÓW ---
def shapebank_to_foldername(shapebank):
    """
    Konwertuje wartość shapebank na nazwę folderu z kafelkami.
    Na podstawie rzeczywistych nazw folderów z ekstraktora.
    """
    # Specjalne przypadki
    if shapebank == 26:
        return SHAPEBANK_26_FALLBACK
    
    if 0 <= shapebank <= 9:
        return f"extracted_newsh{shapebank}.shp"
    elif 10 <= shapebank <= 25:
        # a-p (10=a, 11=b, ..., 25=p)
        letter = chr(ord('a') + (shapebank - 10))
        return f"extracted_newsh{letter}.shp"
    elif 27 <= shapebank <= 29:
        # r, s, t (27=r, 28=s, 29=t)
        letter = chr(ord('a') + (shapebank - 10))
        return f"extracted_newsh{letter}.shp"
    else:
        return f"extracted_newsh{shapebank}.shp"

def get_tiles_dir(shapebank):
    """
    Zwraca ścieżkę do folderu z kafelkami dla danego shapebank.
    """
    # Sprawdź specjalne mapowania
    if shapebank in SPECIAL_SHAPEBANKS:
        special_dir = SPECIAL_SHAPEBANKS[shapebank]
        path = os.path.join(BASE_TILES_DIR, special_dir)
        if os.path.exists(path) and os.path.isdir(path):
            return path
    
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
    
    # Ostatnia deska ratunku - przeszukaj wszystkie foldery
    if os.path.exists(BASE_TILES_DIR):
        for item in os.listdir(BASE_TILES_DIR):
            item_path = os.path.join(BASE_TILES_DIR, item)
            if os.path.isdir(item_path) and shapebank_name_in_folder(item, shapebank):
                print(f"  -> Znaleziono alternatywny folder dla shapebank={shapebank}: {item}")
                return item_path
    
    return None

def shapebank_name_in_folder(folder_name, shapebank):
    """Sprawdza czy nazwa folderu pasuje do shapebank."""
    if shapebank <= 9:
        return f"newsh{shapebank}" in folder_name
    elif 10 <= shapebank <= 25:
        letter = chr(ord('a') + (shapebank - 10))
        return f"newsh{letter}" in folder_name
    elif shapebank == 26:
        return "newshq" in folder_name or "newsh~" in folder_name or "newsh#" in folder_name or "newsh^" in folder_name
    elif 27 <= shapebank <= 29:
        letter = chr(ord('a') + (shapebank - 10))
        return f"newsh{letter}" in folder_name
    return False

# --- CACHE'OWANIE KAFELKÓW ---
@lru_cache(maxsize=512)
def load_tile_cached(tiles_dir, tile_idx):
    """Cache'owanie załadowanych kafelków dla wydajności."""
    tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
    if os.path.exists(tile_path):
        try:
            with Image.open(tile_path) as img:
                return img.convert("RGBA").copy()
        except Exception as e:
            return None
    return None

def tile_exists(tiles_dir, tile_idx):
    """Sprawdza czy kafelek istnieje bez ładowania."""
    tile_path = os.path.join(tiles_dir, f"block_{tile_idx:04d}.bmp")
    return os.path.exists(tile_path)

# --- FUNKCJE RENDERUJĄCE ---
def to_s16(val):
    """Konwertuje unsigned 16-bit na signed 16-bit."""
    return val if val < 32768 else val - 65536

def render_frame_1x1(tile_idx, tiles_dir):
    """Renderuje pojedynczy kafelek 1x1."""
    img = load_tile_cached(tiles_dir, tile_idx)
    if img:
        return img.copy()
    return None

def render_frame_2x2(start_tile, tiles_dir):
    """Renderuje ramkę 2x2 dla dużego wroga (esize=1)."""
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

def get_egraphic_for_state(enemy_data, is_damaged=False):
    """
    Zwraca odpowiednią tablicę egraphic dla danego stanu wroga.
    Zgodne z tyrian2.c linia ~1540-1550.
    """
    if is_damaged:
        edgr = enemy_data.get("edgr", 0)
        if edgr > 0 and edgr != 999:
            return [edgr]
    return enemy_data.get("egraphic", [])

def get_frames_to_render(ani, animate_mode, egraphic_len):
    """Określa które klatki animacji należy renderować."""
    if animate_mode == 0:
        return [0]
    elif animate_mode == 1:
        max_frames = min(ani, egraphic_len)
        return list(range(max_frames))
    elif animate_mode == 2:
        # animate=2 - animacja tylko przy strzale, renderujemy pierwszą klatkę
        return [0]
    else:
        return list(range(min(ani, egraphic_len)))

def save_enemy_image(canvas, out_dir, filename):
    """Zapisuje obrazek wroga."""
    if canvas and canvas.getbbox():
        # Konwersja do palety 256 kolorów (oszczędność miejsca)
        if canvas.mode == 'RGBA':
            # Tworzymy białe tło dla przezroczystości
            bg = Image.new('RGB', canvas.size, (0, 0, 0))
            bg.paste(canvas, mask=canvas.split()[3])
            canvas = bg
        canvas.save(os.path.join(out_dir, filename), optimize=True)
        return True
    return False

def assemble_enemy(enemy_data, out_dir):
    """Główna funkcja składająca wroga z danych."""
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
    
    # Pobieramy folder z kafelkami dla danego shapebank
    tiles_dir = get_tiles_dir(shapebank)
    if not tiles_dir:
        print(f"! BŁĄD: Nie można znaleźć kafelków dla shapebank={shapebank} (wróg {idx})")
        return False
    
    # Sprawdź czy to MegaShape
    is_megashape = False
    for v in egraphic[:10]:
        if v == 999 or to_s16(v) < 0:
            is_megashape = True
            break
    
    # Sprawdź czy wróg zaczyna jako uszkodzony (zgodne z tyrian2.c)
    starts_damaged = dani < 0
    
    if is_megashape:
        # Renderuj MegaShape
        canvas = render_megashape(egraphic, tiles_dir)
        if canvas:
            save_enemy_image(canvas, out_dir, f"enemy_{idx:03d}_megashape.png")
        
        # Jeśli ma osobną grafikę uszkodzenia, renderuj też ją
        if edgr > 0 and edgr != 999:
            damaged_egraphic = [edgr]
            canvas_damaged = render_megashape(damaged_egraphic, tiles_dir)
            if canvas_damaged:
                save_enemy_image(canvas_damaged, out_dir, f"enemy_{idx:03d}_megashape_damaged.png")
        return True
    
    # Normalny wróg (nie MegaShape)
    frames_to_render = get_frames_to_render(ani, animate, len(egraphic))
    
    if esize == 1:
        # Duży wróg 2x2
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
        # Mały wróg 1x1
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
    
    # Renderuj osobną wersję uszkodzoną jeśli edgr jest zdefiniowane i różne od normalnego
    if edgr > 0 and edgr != 999 and not starts_damaged:
        damaged_egraphic = [edgr]
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

# --- FUNKCJE POMOCNICZE ---
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

def print_enemy_info(enemy_data):
    """Wyświetla szczegółowe informacje o wrogu."""
    idx = enemy_data.get("index")
    print(f"\n=== Informacje o wrogu {idx} ===")
    print(f"  shapebank: {enemy_data.get('shapebank')}")
    print(f"  esize: {enemy_data.get('esize')}")
    print(f"  ani: {enemy_data.get('ani')}")
    print(f"  animate: {enemy_data.get('animate')}")
    print(f"  dani: {enemy_data.get('dani')}")
    print(f"  edgr: {enemy_data.get('edgr')}")
    print(f"  armor: {enemy_data.get('armor')}")
    print(f"  value: {enemy_data.get('value')}")
    print(f"  tur: {enemy_data.get('tur')}")
    print(f"  freq: {enemy_data.get('freq')}")
    print(f"  egraphic (pierwsze 10): {enemy_data.get('egraphic', [])[:10]}")

def check_all_tiles(all_enemies):
    """Sprawdza które kafelki istnieją dla wszystkich wrogów."""
    missing_tiles = set()
    total_tiles_needed = 0
    
    for enemy in all_enemies:
        shapebank = enemy.get("shapebank")
        if not shapebank:
            continue
        
        tiles_dir = get_tiles_dir(shapebank)
        if not tiles_dir:
            continue
        
        egraphic = enemy.get("egraphic", [])
        for val in egraphic[:20]:  # sprawdzamy tylko pierwsze 20
            if val > 0 and val != 999 and val < 1000:
                tile_idx = val - 1
                total_tiles_needed += 1
                if not tile_exists(tiles_dir, tile_idx):
                    missing_tiles.add((shapebank, tile_idx))
    
    if missing_tiles:
        print(f"\n⚠️ Brakujące kafelki: {len(missing_tiles)} z {total_tiles_needed}")
        for sb, tile in list(missing_tiles)[:20]:
            print(f"  shapebank {sb}, tile {tile}")
    else:
        print(f"\n✅ Wszystkie potrzebne kafelki istnieją! ({total_tiles_needed} tile references)")

# --- MAIN ---
def main():
    # Utwórz folder wyjściowy
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    # Wczytaj JSON
    if not os.path.exists(JSON_FILE):
        print(f"Błąd: Nie znaleziono pliku {JSON_FILE}")
        return
    
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_enemies = json.load(f)
    
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python compose_enemy2.py <indeks>       - renderuj konkretnego wroga")
        print("  python compose_enemy2.py --all          - renderuj wszystkich wrogów")
        print("  python compose_enemy2.py --info <indeks> - pokaż informacje o wrogu")
        print("  python compose_enemy2.py --analyze      - analizuj wszystkie shapebank")
        print("  python compose_enemy2.py --check-tiles  - sprawdź czy wszystkie kafelki istnieją")
        return
    
    command = sys.argv[1]
    
    if command == "--analyze":
        analyze_shapebank_values(all_enemies)
    
    elif command == "--check-tiles":
        check_all_tiles(all_enemies)
    
    elif command == "--info" and len(sys.argv) > 2:
        target_idx = int(sys.argv[2])
        enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
        if enemy:
            print_enemy_info(enemy)
        else:
            print(f"Nie znaleziono wroga o indeksie {target_idx}")
    
    elif command == "--all":
        print(f"Renderowanie wszystkich {len(all_enemies)} wrogów...")
        print(f"Folder wyjściowy: {OUTPUT_PATH}")
        print("-" * 60)
        
        start_time = time.time()
        success_count = 0
        fail_count = 0
        skipped_count = 0
        
        for i, enemy in enumerate(all_enemies, 1):
            idx = enemy.get("index", "?")
            try:
                if assemble_enemy(enemy, OUTPUT_PATH):
                    success_count += 1
                else:
                    fail_count += 1
                
                # Pokazuj postęp co 50 wrogów
                if i % 50 == 0:
                    print(f"  Postęp: {i}/{len(all_enemies)} ({i*100//len(all_enemies)}%)")
                    
            except Exception as e:
                print(f"\n  Błąd przy wrogu {idx}: {e}")
                fail_count += 1
        
        elapsed = time.time() - start_time
        
        print("-" * 60)
        print(f"\n✅ Zakończono!")
        print(f"  Sukces: {success_count}")
        print(f"  Błędy: {fail_count}")
        print(f"  Razem: {len(all_enemies)}")
        print(f"  Czas: {elapsed:.1f} sekund")
        print(f"  Średnio: {elapsed/len(all_enemies):.2f} sekund/wróg")
        
        # Podsumowanie plików
        output_files = [f for f in os.listdir(OUTPUT_PATH) if f.endswith('.png')]
        print(f"  Utworzono plików: {len(output_files)}")
    
    else:
        try:
            target_idx = int(command)
            enemy = next((e for e in all_enemies if e.get("index") == target_idx), None)
            if enemy:
                if assemble_enemy(enemy, OUTPUT_PATH):
                    print(f"✅ Wróg {target_idx} wyrenderowany pomyślnie")
                else:
                    print(f"❌ Nie udało się wyrenderować wroga {target_idx}")
            else:
                print(f"Nie znaleziono wroga o indeksie {target_idx}")
        except ValueError:
            print(f"Nieznana komenda: {command}")

if __name__ == "__main__":
    main()