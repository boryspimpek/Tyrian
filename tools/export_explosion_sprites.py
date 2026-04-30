"""
Wyciąga sprite'y eksplozji z newsh6.shp i zapisuje jako PNG.

Naming: explo_t{type:02d}_{label}_f{frame:02d}.png
  - type  = indeks w tablicy explosion_data (0-52)
  - label = krótki opis (z TYPE_LABELS)
  - frame = klatka animacji (0-based)

Indeksowanie: blit_sprite2(sheet, index) używa 1-based index.
  sprite_start = explosion_data[type][0]
  klatka 0 → blit(sprite_start + 1) → offset table entry [sprite_start]
"""

import struct
import os
from PIL import Image

SHP_PATH = r"C:\Users\borys\projekty\Tyrian\tyrian21\newsh6.shp"
PAL_PATH = r"C:\Users\borys\projekty\Tyrian\tyrian21\palette.dat"
OUT_DIR  = r"C:\Users\borys\projekty\Tyrian\extracted_tiles\explosions"

# (sprite_start, ttl) — indeksowanie 0-based, zgodne z JE_setupExplosion explosion_data[53]
EXPLOSION_DATA = [
    (144,  7),  #  0
    (120, 12),  #  1
    (190, 12),  #  2
    (209, 12),  #  3
    (152, 12),  #  4
    (171, 12),  #  5
    (133,  7),  #  6
    (  1, 12),  #  7
    ( 20, 12),  #  8
    ( 39, 12),  #  9
    ( 58, 12),  # 10
    (110,  3),  # 11
    ( 76,  7),  # 12
    ( 91,  3),  # 13
    (227,  3),  # 14
    (230,  3),  # 15
    (233,  3),  # 16
    (252,  3),  # 17
    (246,  3),  # 18
    (249,  3),  # 19
    (265,  3),  # 20
    (268,  3),  # 21
    (271,  3),  # 22
    (236,  3),  # 23
    (239,  3),  # 24
    (242,  3),  # 25
    (261,  3),  # 26
    (274,  3),  # 27
    (277,  3),  # 28
    (280,  3),  # 29
    (299,  3),  # 30
    (284,  3),  # 31
    (287,  3),  # 32
    (290,  3),  # 33
    (293,  3),  # 34
    (165,  8),  # 35 coin values
    (184,  8),  # 36
    (203,  8),  # 37
    (222,  8),  # 38
    (168,  8),  # 39
    (187,  8),  # 40
    (206,  8),  # 41
    (225, 10),  # 42
    (169, 10),  # 43
    (188, 10),  # 44
    (207, 20),  # 45
    (226, 14),  # 46
    (170, 14),  # 47
    (189, 14),  # 48
    (208, 14),  # 49
    (246, 14),  # 50
    (227, 14),  # 51
    (265, 14),  # 52
]

TYPE_LABELS = {
    0:  "hit_flash",
    1:  "small_enemy",
    2:  "large_ground_tl",
    3:  "large_ground_bl",
    4:  "large_ground_tr",
    5:  "large_ground_br",
    6:  "white_smoke",
    7:  "large_air_tl",
    8:  "large_air_bl",
    9:  "large_air_tr",
    10: "large_air_br",
    11: "flash_short",
    12: "medium",
    13: "brief",
    35: "coin_value",
}


def load_palette(path):
    """Wczytuje palettę Tyrian (768 bajtów, wartości 0-63 → skalowane ×4 do 0-255).
    Indeks 0 staje się przezroczysty (alpha=0)."""
    with open(path, "rb") as f:
        raw = f.read(768)
    palette = []
    for i in range(256):
        r = min(255, raw[i * 3]     * 4)
        g = min(255, raw[i * 3 + 1] * 4)
        b = min(255, raw[i * 3 + 2] * 4)
        a = 0 if i == 0 else 255
        palette.append((r, g, b, a))
    return palette


def parse_shp(path):
    """Parsuje plik .shp (Sprite2 nibble-RLE). Zwraca listę (pixels_bytearray, width, height)
    indeksowaną od 0. Pusty slot → None."""
    with open(path, "rb") as f:
        raw = f.read()

    first_offset = struct.unpack_from("<H", raw, 0)[0]
    n = first_offset // 2
    offsets = [struct.unpack_from("<H", raw, i * 2)[0] for i in range(n)]

    sprites = []
    W = 12
    for idx, off in enumerate(offsets):
        next_off = offsets[idx + 1] if idx + 1 < n else len(raw)
        data = raw[off:next_off]

        rows = []
        row = bytearray(W)
        x = 0
        i = 0
        while i < len(data):
            ctrl = data[i]; i += 1
            if ctrl == 0x0F:
                break
            skip = ctrl & 0x0F
            draw = (ctrl >> 4) & 0x0F
            x += skip
            if draw == 0:
                rows.append(bytes(row))
                row = bytearray(W)
                x = 0
            else:
                for _ in range(draw):
                    if i >= len(data):
                        break
                    if x < W:
                        row[x] = data[i]
                    x += 1
                    i += 1

        if not rows:
            sprites.append(None)
            continue

        h = len(rows)
        pixels = bytearray(W * h)
        for r, rowdata in enumerate(rows):
            pixels[r * W: r * W + W] = rowdata
        sprites.append((pixels, W, h))

    return sprites


def make_png(pixels, w, h, palette):
    img = Image.new("RGBA", (w, h))
    rgba_pixels = [palette[p] for p in pixels]
    img.putdata(rgba_pixels)
    return img


def export():
    os.makedirs(OUT_DIR, exist_ok=True)

    palette = load_palette(PAL_PATH)
    sprites = parse_shp(SHP_PATH)

    saved = 0
    skipped = 0

    for type_idx, (sprite_start, ttl) in enumerate(EXPLOSION_DATA):
        label = TYPE_LABELS.get(type_idx, f"type{type_idx:02d}")

        for frame in range(ttl):
            # blit_sprite2(index) → 1-based → offset table entry [index - 1]
            # frame 0 → blit(sprite_start + 1) → entry sprite_start
            sheet_idx = sprite_start + frame  # 0-based index do tablicy sprites[]

            if sheet_idx >= len(sprites) or sprites[sheet_idx] is None:
                print(f"  BRAK: type={type_idx} frame={frame} sheet_idx={sheet_idx}")
                skipped += 1
                continue

            pixels, w, h = sprites[sheet_idx]
            img = make_png(pixels, w, h, palette)

            filename = f"explo_t{type_idx:02d}_{label}_f{frame:02d}.png"
            img.save(os.path.join(OUT_DIR, filename))
            saved += 1

    print(f"\nZapisano: {saved}  Pominięto (brak danych): {skipped}")
    print(f"Folder: {OUT_DIR}")


if __name__ == "__main__":
    export()
