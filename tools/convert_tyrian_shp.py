"""
Wyodrebnia sprite'y z pliku tyrian.shp do osobnych plikow BMP.

tyrian.shp zawiera 12 bankow grafik uzywanych przez interfejs i statki gracza:
  Banki 0-6  (font_a..interface3) — format sekwencyjny (load_sprites):
               liczba sprite'ow (U16), nastepnie dla kazdego:
               populated (U8), szerokosc (U16), wysokosc (U16), rozmiar (U16), dane.
               Kompresja: 0xFF=pominij_n, 0xFE=nowy_wiersz, 0xFD=pominij_1, else=piksel.
  Banki 7-11 (shots, ships, powerups, items, shots2) — format Nibble-RLE (Sprite2),
               identyczny z plikami newsh*.shp: tabela offsetow WORD na poczatku banku,
               szerokosc stala = 12px, wysokosc wykrywana automatycznie z danych,
               terminator 0x0F konczy sprite.

Paleta: plik palette.dat (768 bajtow RGB, wartosci 6-bit VGA mnozone x4).
Wynik:  folder extracted_tyrian_shp/ z plikami {bank}_{index:04d}.bmp.
"""

import struct
import os

BANK_NAMES = {
    0: "font_a", 1: "font_b", 2: "font_c",
    3: "interface", 4: "options", 5: "interface2", 6: "interface3",
    7: "shots", 8: "ships", 9: "powerups", 10: "items", 11: "shots2",
}

def save_bmp(w, h, pixels, pal_path, name):
    if not pixels or len(pixels) == 0: return
    palette = b""
    if os.path.exists(pal_path):
        with open(pal_path, "rb") as pf:
            raw = pf.read(768)
            for i in range(0, 768, 3):
                palette += struct.pack('BBBB', min(255, raw[i+2]*4), min(255, raw[i+1]*4), min(255, raw[i]*4), 0)
    else:
        for i in range(256): palette += struct.pack('BBBB', i, i, i, 0)

    row_size = (w + 3) & ~3
    bmp_pixels = bytearray()
    for row_idx in range(h):
        line = pixels[(h - 1 - row_idx) * w : (h - row_idx) * w]
        if len(line) < w: line += bytearray([0] * (w - len(line)))
        bmp_pixels += line + bytearray([0] * (row_size - w))

    header = struct.pack('<2sIHHI', b'BM', 54 + 1024 + len(bmp_pixels), 0, 0, 1078)
    dib = struct.pack('<IiiHHIIIIII', 40, w, h, 1, 8, 0, len(bmp_pixels), 0, 0, 256, 0)

    with open(name, "wb") as out:
        out.write(header); out.write(dib); out.write(palette); out.write(bmp_pixels)


def decode_sprite1(data, w, h):
    """Sprite1 format: 0xFF=skip_n(next byte=count), 0xFE=newline, 0xFD=skip1, else=pixel"""
    pixels = bytearray(w * h)
    x, y = 0, 0
    i = 0
    while i < len(data):
        b = data[i]; i += 1
        if b == 0xFF:
            if i >= len(data): break
            count = data[i]; i += 1
            x += count
        elif b == 0xFE:
            x = w  # force row advance below
        elif b == 0xFD:
            x += 1
        else:
            if y < h and x < w:
                pixels[y * w + x] = b
            x += 1
        while x >= w:
            x -= w
            y += 1
            if y >= h: return pixels
    return pixels


def decode_sprite2(data, w=12):
    """Nibble-RLE (Sprite2): same as newsh format, width fixed at 12, height auto-detected."""
    rows = []
    row = bytearray(w)
    x = 0
    i = 0
    while i < len(data):
        ctrl = data[i]; i += 1
        if ctrl == 0x0F: break
        skip = ctrl & 0x0F
        draw = (ctrl >> 4) & 0x0F
        x += skip
        if draw == 0:
            rows.append(bytes(row))
            row = bytearray(w)
            x = 0
        else:
            for _ in range(draw):
                if i >= len(data): break
                if x < w: row[x] = data[i]
                x += 1; i += 1
    h = len(rows)
    if h == 0: return None, w, 0
    pixels = bytearray(w * h)
    for r, rowdata in enumerate(rows):
        pixels[r * w: r * w + w] = rowdata
    return pixels, w, h


def extract_banks_0_6(f, bank_idx, bank_start, out_dir, pal_path):
    """Sequential load_sprites format."""
    f.seek(bank_start)
    count = struct.unpack('<H', f.read(2))[0]
    name = BANK_NAMES.get(bank_idx, f"bank{bank_idx}")
    for i in range(count):
        populated = struct.unpack('B', f.read(1))[0]
        if not populated:
            continue
        w = struct.unpack('<H', f.read(2))[0]
        h = struct.unpack('<H', f.read(2))[0]
        size = struct.unpack('<H', f.read(2))[0]
        data = f.read(size)
        if w <= 0 or h <= 0 or w > 512 or h > 512: continue
        pixels = decode_sprite1(data, w, h)
        if any(pixels):
            save_bmp(w, h, pixels, pal_path, f"{out_dir}/{name}_{i:04d}.bmp")


def extract_banks_7_11(f, bank_idx, bank_start, bank_end, out_dir, pal_path):
    """Sprite2 / Nibble-RLE format — same as newsh files."""
    f.seek(bank_start)
    bank_size = bank_end - bank_start
    bank_data = f.read(bank_size)

    w0 = struct.unpack_from('<H', bank_data, 0)[0]
    n_sprites = w0 // 2
    if n_sprites == 0: return

    offsets = [struct.unpack_from('<H', bank_data, i * 2)[0] for i in range(n_sprites)]
    name = BANK_NAMES.get(bank_idx, f"bank{bank_idx}")

    for i in range(n_sprites):
        off = offsets[i]
        next_off = offsets[i + 1] if i + 1 < n_sprites else bank_size
        sprite_data = bank_data[off:next_off]
        if len(sprite_data) <= 1: continue  # only terminator or empty
        pixels, w, h = decode_sprite2(sprite_data)
        if pixels and any(pixels):
            save_bmp(w, h, pixels, pal_path, f"{out_dir}/{name}_{i+1:04d}.bmp")


def extract_tyrian_shp(file_path, pal_path):
    if not os.path.exists(file_path):
        print(f"Nie znaleziono pliku: {file_path}"); return

    out_dir = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"
    os.makedirs(out_dir, exist_ok=True)

    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        num_banks = struct.unpack('<H', f.read(2))[0]
        bank_offsets = [struct.unpack('<I', f.read(4))[0] for _ in range(num_banks)]
        bank_offsets.append(file_size)

        for b in range(num_banks):
            start = bank_offsets[b]
            end = bank_offsets[b + 1]
            print(f"Bank {b} ({BANK_NAMES.get(b, '?')}): offset={start}, size={end-start}")
            if b <= 6:
                extract_banks_0_6(f, b, start, out_dir, pal_path)
            else:
                extract_banks_7_11(f, b, start, end, out_dir, pal_path)

    count = len([x for x in os.listdir(out_dir) if x.endswith('.bmp')])
    print(f"\nWyodrebniono {count} sprite'ow -> {out_dir}/")


extract_tyrian_shp(
    r"C:\Users\borys\projekty\Tyrian\tyrian21\tyrian.shp",
    r"C:\Users\borys\projekty\Tyrian\tyrian21\palette.dat",
)
