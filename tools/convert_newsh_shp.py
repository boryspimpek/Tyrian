import struct
import os


def decode_sprite2(data):
    """Nibble-RLE (Sprite2): low nibble=skip, high nibble=draw, 0x0F=terminator, width=12."""
    W = 12
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
                if i >= len(data): break
                if x < W: row[x] = data[i]
                x += 1; i += 1
    h = len(rows)
    if h == 0:
        return None, W, 0
    pixels = bytearray(W * h)
    for r, rowdata in enumerate(rows):
        pixels[r * W: r * W + W] = rowdata
    return pixels, W, h


def save_bmp(w, h, pixels, pal_path, name):
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
        line = pixels[(h - 1 - row_idx) * w: (h - row_idx) * w]
        if len(line) < w: line += bytearray(w - len(line))
        bmp_pixels += line + bytearray(row_size - w)

    header = struct.pack('<2sIHHI', b'BM', 54 + 1024 + len(bmp_pixels), 0, 0, 1078)
    dib    = struct.pack('<IiiHHIIIIII', 40, w, h, 1, 8, 0, len(bmp_pixels), 0, 0, 256, 0)
    with open(name, "wb") as out:
        out.write(header); out.write(dib); out.write(palette); out.write(bmp_pixels)


def extract_newsh(file_path, pal_path):
    if not os.path.exists(file_path):
        print(f"Nie znaleziono: {file_path}"); return

    base = os.path.basename(file_path).lower()
    out_dir = os.path.join(
        r"C:\Users\borys\projekty\Tyrian\extracted_tiles",
        f"extracted_{base}",
    )
    os.makedirs(out_dir, exist_ok=True)

    with open(file_path, "rb") as f:
        raw = f.read()

    # Word[0] = offset do sprite'a 1 = rozmiar tabeli = 2 * N
    first_offset = struct.unpack_from('<H', raw, 0)[0]
    n_sprites = first_offset // 2

    offsets = [struct.unpack_from('<H', raw, i * 2)[0] for i in range(n_sprites)]
    saved = 0

    for i, off in enumerate(offsets):
        next_off = offsets[i + 1] if i + 1 < n_sprites else len(raw)
        sprite_data = raw[off:next_off]

        pixels, w, h = decode_sprite2(sprite_data)
        if pixels is None:
            continue  # pusty slot - pomijamy (brak danych do narysowania)

        save_bmp(w, h, pixels, pal_path, f"{out_dir}/block_{i:04d}.bmp")
        saved += 1

    print(f"{base}: {n_sprites} sprite'ow w tabeli, zapisano {saved} BMP -> {out_dir}/")


extract_newsh(
    r"C:\Users\borys\projekty\Tyrian\tyrian21\newsh2.shp",
    r"C:\Users\borys\projekty\Tyrian\tyrian21\palette.dat",
)
