#!/usr/bin/env python3
"""
Ekstraktor kafelków map dla Tyrian Episode 1.

Jak to działa:
  1. Czyta episode1_level_mapping.json → lista poziomów z lvl_pos_index i nazwami
  2. Dla każdego poziomu otwiera tyrian1.lvl i przeskakuje do odpowiedniego offsetu
     (lvlPos[lvl_pos_index]) żeby odczytać nagłówek poziomu:
       - shape_file: litera → plik shapesX.dat (np. 'Z' → shapesz.dat)
       - mapSh[3][128]: tabela mapowania slot→indeks w shapesX.dat (dla każdej z 3 warstw)
  3. Otwiera shapesX.dat i czyta 600 kafelków (1 bajt flaga blank + opcjonalnie 672 bajty pikseli 24×28)
     Zachowuje tylko te, które są referencjonowane przez mapSh danego poziomu.
  4. Czyta też tilemap: warstwa1=300×14, warstwa2=600×14, warstwa3=600×15 bajtów (indeksy slotów)
  5. Zapisuje kafelki jako PNG (indeks 0 = przezroczysty) w katalogu extracted_tiles/

Struktura wyjściowa:
  extracted_tiles/
    palette_0.png              ← podgląd palety
    lvl17_TYRIAN/
      layer1/
        tile_slot000_shp009.png   ← nazwa = slot w megaData + indeks w shapesX.dat
        ...
      layer2/
        ...
      layer3/
        ...
      tilemap_layer1.json       ← tablica 300×14 (indeksy slotów)
      tilemap_layer2.json
      tilemap_layer3.json
      meta.json                 ← shape_file, map_file, palette_idx itp.

Wymagania: pip install Pillow
"""

import json
import struct
import os
import sys
from pathlib import Path
from PIL import Image

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Ścieżki ─────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
BASE         = SCRIPT_DIR.parent
DATA_DIR     = BASE / 'tyrian21'
MAPPING_FILE = BASE / 'data' / 'episode1_level_mapping.json'
LVL_FILE     = DATA_DIR / 'tyrian1.lvl'
OUT_DIR      = BASE / 'extracted_map_tiles'

# ─── Stałe ───────────────────────────────────────────────────────────────────

TILE_W      = 24
TILE_H      = 28
TILE_BYTES  = TILE_W * TILE_H   # 672
SHAPES_TOTAL = 600
EVENT_STRUCT = '<H B h h b b b B'   # 2+1+2+2+1+1+1+1 = 11 bajtów
EVENT_SIZE   = struct.calcsize(EVENT_STRUCT)  # 11

# Ile slotów używa gra dla każdej warstwy (z src/tyrian2.c):
#   Warstwa 1 (megaData1.shapes[72]): for x = 0 to 71  → 72 sloty
#   Warstwa 2 (megaData2.shapes[71]): for x = 0 to 71, ale x!=71 → 71 slotów (slot 71 = NULL)
#   Warstwa 3 (megaData3.shapes[70]): for x = 0 to 71, ale x<70  → 70 slotów (slot 70,71 = NULL)
LAYER_VALID_SLOTS = [72, 71, 70]

# Indeks palety używanej podczas rozgrywki (palettes[0] = domyślna gry)
PALETTE_IDX  = 0

# ─── Paleta ──────────────────────────────────────────────────────────────────

def load_palette(idx: int = 0) -> list[tuple[int, int, int]]:
    """
    Czyta jedną z 23 palet z palette.dat.
    Format VGA: 256 kolorów × 3 bajty (R,G,B), wartości 0-63 → skaluj do 8-bit.
    Skalowanie: val8 = (val6 << 2) | (val6 >> 4)  (jak w src/palette.c)
    """
    path = DATA_DIR / 'palette.dat'
    with open(path, 'rb') as f:
        f.seek(idx * 256 * 3)
        raw = f.read(256 * 3)
    palette = []
    for i in range(256):
        r, g, b = raw[i*3], raw[i*3+1], raw[i*3+2]
        palette.append((
            (r << 2) | (r >> 4),
            (g << 2) | (g >> 4),
            (b << 2) | (b >> 4),
        ))
    return palette


def save_palette_preview(palette: list, out_path: Path):
    """Zapisuje podgląd palety: 16×16 kwadratów po 16×16 px."""
    sw, sh = 16, 16
    img = Image.new('RGB', (16 * sw, 16 * sh))
    for idx, (r, g, b) in enumerate(palette):
        cx = (idx % 16) * sw
        cy = (idx // 16) * sh
        for py in range(sh):
            for px in range(sw):
                img.putpixel((cx + px, cy + py), (r, g, b))
    img.save(out_path)

# ─── Czytanie pliku .lvl ─────────────────────────────────────────────────────

def read_lvl_offsets(lvl_path: Path) -> list[int]:
    """Czyta tabelę offsetów lvlPos z nagłówka tyrian*.lvl."""
    with open(lvl_path, 'rb') as f:
        lvl_num = struct.unpack('<H', f.read(2))[0]
        offsets = list(struct.unpack(f'<{lvl_num}i', f.read(4 * lvl_num)))
    return offsets


def read_level_header(lvl_path: Path, offset: int):
    """
    Czyta nagłówek jednego poziomu z pliku .lvl od podanego offsetu.
    Zwraca: (map_file, shape_file, map_sh, tilemap1, tilemap2, tilemap3)
      map_sh: list[3][128] — tabela mapowania slot → indeks w shapesX.dat (1-based)
      tilemapN: list[rows][cols] — indeksy slotów kafelków (0-based)
    """
    with open(lvl_path, 'rb') as f:
        f.seek(offset)

        map_file   = chr(f.read(1)[0])
        shape_file = chr(f.read(1)[0])
        map_x      = struct.unpack('<H', f.read(2))[0]
        map_x2     = struct.unpack('<H', f.read(2))[0]
        map_x3     = struct.unpack('<H', f.read(2))[0]

        level_enemy_max = struct.unpack('<H', f.read(2))[0]
        f.read(level_enemy_max * 2)   # lista ID wrogów

        max_event = struct.unpack('<H', f.read(2))[0]
        f.read(max_event * EVENT_SIZE) # eventy

        # mapSh[3][128] × uint16 — tabela mapowania slot → indeks w shapesX.dat
        # UWAGA: mapSh w pliku .lvl jest zapisane w big-endian!
        # Gra czyta fread_u16_die (little-endian, bez swapu na x86),
        # a potem robi SDL_Swap16() → efekt: dane w pliku to big-endian.
        map_sh = []
        for layer in range(3):
            row = list(struct.unpack('>128H', f.read(128 * 2)))
            map_sh.append(row)

        # Tilemapy (indeksy slotów, uint8)
        # Warstwa 1: 300 wierszy × 14 kolumn
        raw1 = f.read(14 * 300)
        tilemap1 = [[raw1[y * 14 + x] for x in range(14)] for y in range(300)]

        # Warstwa 2: 600 wierszy × 14 kolumn
        raw2 = f.read(14 * 600)
        tilemap2 = [[raw2[y * 14 + x] for x in range(14)] for y in range(600)]

        # Warstwa 3: 600 wierszy × 15 kolumn
        raw3 = f.read(15 * 600)
        tilemap3 = [[raw3[y * 15 + x] for x in range(15)] for y in range(600)]

    return map_file, shape_file, map_sh, tilemap1, tilemap2, tilemap3

# ─── Czytanie shapesX.dat ────────────────────────────────────────────────────

def shapes_filename(shape_file_char: str) -> Path:
    """'Z' → tyrian21/shapesz.dat"""
    return DATA_DIR / f'shapes{shape_file_char.lower()}.dat'


def read_shapes(shapes_path: Path, map_sh: list) -> dict:
    """
    Czyta 600 kafelków z shapesX.dat.
    Zwraca słownik: (layer, slot) → bytes(672 pikseli)
    Zachowuje tylko kafelki referencjonowane w map_sh ORAZ w zakresie slotów używanych przez grę:
      Warstwa 1: sloty 0-71 (gra: for x=0 to 71)
      Warstwa 2: sloty 0-70 (gra: x!=71 warunek → slot 71 = NULL/przezroczysty)
      Warstwa 3: sloty 0-69 (gra: x<70 warunek → sloty 70-71 = NULL)

    Format pliku: 600 × [1 bajt blank_flag + jeśli blank==0: 672 bajty pikseli]
      blank_flag == 0 → kafelek ma dane (czytaj 672 bajty)
      blank_flag != 0 → kafelek pusty (672 bajty zer, nic nie czytaj z pliku)
    """
    # Zbuduj odwrotny słownik: indeks_w_pliku_1based → [(layer, slot), ...]
    # Tylko dla slotów w zakresie używanym przez grę
    needed: dict[int, list] = {}
    for layer in range(3):
        max_slot = LAYER_VALID_SLOTS[layer]
        for slot in range(max_slot):
            idx = map_sh[layer][slot]
            if 1 <= idx <= SHAPES_TOTAL:   # mapSh=0 lub >600 → brak kafelka (przezroczysty)
                needed.setdefault(idx, []).append((layer, slot))

    tiles: dict[tuple, bytes] = {}

    with open(shapes_path, 'rb') as f:
        for z in range(SHAPES_TOTAL):
            blank_byte = f.read(1)[0]
            shape_blank = (blank_byte != 0)   # 0=ma dane, !=0=pusty

            if shape_blank:
                shape = bytes(TILE_BYTES)
            else:
                shape = f.read(TILE_BYTES)

            shape_idx = z + 1  # 1-based
            if shape_idx in needed:
                for (layer, slot) in needed[shape_idx]:
                    tiles[(layer, slot)] = shape

    return tiles

# ─── Konwersja kafelka → PNG ─────────────────────────────────────────────────

def tile_to_image(tile_bytes: bytes, palette: list) -> Image.Image:
    """
    Konwertuje 672 bajty (24×28, indeksy palety) na obraz RGBA.
    Indeks 0 = piksel przezroczysty.
    """
    img = Image.new('RGBA', (TILE_W, TILE_H))
    pixels = img.load()
    for row in range(TILE_H):
        for col in range(TILE_W):
            idx = tile_bytes[row * TILE_W + col]
            if idx == 0:
                pixels[col, row] = (0, 0, 0, 0)   # przezroczysty
            else:
                r, g, b = palette[idx]
                pixels[col, row] = (r, g, b, 255)
    return img

# ─── Główna pętla ────────────────────────────────────────────────────────────

def extract_all():
    palette = load_palette(PALETTE_IDX)

    # Zapisz podgląd palety
    OUT_DIR.mkdir(exist_ok=True)
    save_palette_preview(palette, OUT_DIR / f'palette_{PALETTE_IDX}.png')
    print(f"Zapisano podgląd palety: palette_{PALETTE_IDX}.png")

    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    offsets = read_lvl_offsets(LVL_FILE)
    print(f"Załadowano {len(offsets)} offsetów z tyrian1.lvl\n")

    for level in mapping['levels']:
        game_order   = level['game_order']
        name         = level['name']
        lvl_pos_idx  = level['lvl_pos_index']
        json_file    = level['extracted_json']
        bonus        = level.get('bonus', False)

        safe_name = name.replace(' ', '_').replace('?', 'Q').replace('*', 'X').replace('/', '-').replace('\\', '-')
        label = f"{json_file.replace('.json','')}_{safe_name}"
        level_out = OUT_DIR / label
        print(f"[{game_order:2d}] {name:15s} -> {label}")

        # Sprawdź czy offset istnieje w pliku
        if lvl_pos_idx >= len(offsets):
            print(f"      BRAK offsetu {lvl_pos_idx} (max: {len(offsets)-1})")
            continue

        file_offset = offsets[lvl_pos_idx]
        if file_offset <= 0:
            print(f"      Nieprawidłowy offset: {file_offset}")
            continue

        try:
            map_file, shape_file, map_sh, tilemap1, tilemap2, tilemap3 = \
                read_level_header(LVL_FILE, file_offset)
        except Exception as e:
            print(f"      BŁĄD czytania nagłówka: {e}")
            continue

        shapes_path = shapes_filename(shape_file)
        if not shapes_path.exists():
            print(f"      BRAK pliku: {shapes_path.name}")
            continue

        try:
            tiles = read_shapes(shapes_path, map_sh)
        except Exception as e:
            print(f"      BŁĄD czytania kształtów: {e}")
            continue

        # Utwórz katalogi
        for layer in range(3):
            (level_out / f'layer{layer+1}').mkdir(parents=True, exist_ok=True)

        # Zapisz kafelki PNG
        saved = [0, 0, 0]
        for (layer, slot), tile_bytes in sorted(tiles.items()):
            # Znajdź oryginalny indeks w shapes.dat (do nazwy pliku)
            shp_idx = map_sh[layer][slot]
            fname   = f'tile_slot{slot:03d}_shp{shp_idx:03d}.png'
            img     = tile_to_image(tile_bytes, palette)
            img.save(level_out / f'layer{layer+1}' / fname)
            saved[layer] += 1

        # Zapisz tilemapy jako JSON
        for layer_idx, tilemap in enumerate([tilemap1, tilemap2, tilemap3], 1):
            with open(level_out / f'tilemap_layer{layer_idx}.json', 'w') as f:
                json.dump(tilemap, f, separators=(',', ':'))

        # Zapisz meta
        meta = {
            'level_name':   name,
            'game_order':   game_order,
            'json_source':  json_file,
            'lvl_pos_index': lvl_pos_idx,
            'map_file':     map_file,
            'shape_file':   shape_file,
            'shapes_dat':   shapes_path.name,
            'palette_idx':  PALETTE_IDX,
            'bonus':        bonus,
            'tiles_per_layer': saved,
            'tilemap_size': {
                'layer1': '300 rows × 14 cols',
                'layer2': '600 rows × 14 cols',
                'layer3': '600 rows × 15 cols',
            },
            'tile_size_px': f'{TILE_W}×{TILE_H}',
            'map_sh_used': {
                f'layer{l+1}': [
                    {'slot': s, 'shp_idx': map_sh[l][s]}
                    for s in range(128) if map_sh[l][s] > 0
                ]
                for l in range(3)
            }
        }
        with open(level_out / 'meta.json', 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        print(f"      shapes: {shapes_path.name}  kafelki: L1={saved[0]} L2={saved[1]} L3={saved[2]}")

    print(f"\nGotowe! Kafelki w: {OUT_DIR}")


if __name__ == '__main__':
    extract_all()
