import struct
import os

def extract_any_shp(file_path, pal_path):
    base_name = os.path.basename(file_path).lower()
    output_dir = f"extracted_{base_name}"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    with open(file_path, "rb") as f:
        # Odczyt liczby spritów
        data = f.read(2)
        if not data: return
        num_sprites = struct.unpack('<H', data)[0]
        f.seek(0)
        offsets = [struct.unpack('<H', f.read(2))[0] for _ in range(num_sprites)]

        for i, off in enumerate(offsets):
            if off == 0 or off >= os.path.getsize(file_path): continue
            f.seek(off)
            
            # DECYZJA: Jaki to format?
            # Jeśli to NEWSH, używamy formatu klockowego 12x14 (Sprite2)
            if "newsh" in base_name:
                w, h = 12, 14
                f.seek(off) # Dane zaczynają się od razu
                decode_sprite2(f, w, h, i, output_dir, pal_path)
            
            # Jeśli to TYRIAN.SHP, czytamy nagłówek W, H (Sprite1)
            else:
                w, h = struct.unpack('BB', f.read(2))
                if 0 < w < 320 and 0 < h < 200:
                    f.seek(off + 4) # Przeskok nagłówka
                    decode_sprite1(f, w, h, i, output_dir, pal_path)

def decode_sprite2(f, w, h, idx, out_dir, pal):
    """Logika Nibble-RLE dla klocków 12x14"""
    pixels = bytearray([0] * (w * h))
    x, y = 0, 0
    while True:
        b = f.read(1)
        if not b or b[0] == 0x0F: break
        ctrl = b[0]
        skip = ctrl & 0x0F
        draw = (ctrl & 0xF0) >> 4
        x += skip
        if draw == 0:
            y += 1
            x = 0
        else:
            for _ in range(draw):
                p = f.read(1)
                if p and y < h and x < w: pixels[y*w + x] = p[0]
                x += 1
        if y >= h: break
    if any(pixels): save_bmp(w, h, pixels, pal, f"{out_dir}/block_{idx:04d}.bmp")

def decode_sprite1(f, w, h, idx, out_dir, pal):
    """Klasyczne RLE Tyriana (Skip/Draw)"""
    pixels = bytearray([0] * (w * h))
    ptr = 0
    while ptr < (w * h):
        ctrl = f.read(2)
        if len(ctrl) < 2: break
        skip, draw = struct.unpack('BB', ctrl)
        if skip == 0 and draw == 0: break
        ptr += skip
        if draw > 0:
            data = f.read(draw)
            for b in data:
                if ptr < len(pixels):
                    pixels[ptr] = b
                    ptr += 1
    if any(pixels): save_bmp(w, h, pixels, pal, f"{out_dir}/sprite_{idx:04d}.bmp")

def save_bmp(w, h, pixels, pal_path, name):
    # Twoja funkcja zapisu BMP (z Twojego pliku convert_to_bmp.py)
    # Pamiętaj o mnożeniu palety * 4, bo Tyrian ma 6-bit VGA
    palette = b""
    if os.path.exists(pal_path):
        with open(pal_path, "rb") as pf:
            raw = pf.read(768)
            for i in range(0, 768, 3):
                palette += struct.pack('BBBB', raw[i+2]*4, raw[i+1]*4, raw[i]*4, 0)
    else:
        for i in range(256): palette += struct.pack('BBBB', i, i, i, 0)

    row_size = (w + 3) & ~3
    bmp_pixels = bytearray()
    for row_idx in range(h):
        line = pixels[(h - 1 - row_idx) * w : (h - row_idx) * w]
        bmp_pixels += line + bytearray([0] * (row_size - w))

    header = struct.pack('<2sIHHI', b'BM', 54 + 1024 + len(bmp_pixels), 0, 0, 1078)
    dib = struct.pack('<IiiHHIIIIII', 40, w, h, 1, 8, 0, len(bmp_pixels), 0, 0, 256, 0)
    
    with open(name, "wb") as out:
        out.write(header)
        out.write(dib)
        out.write(palette)
        out.write(bmp_pixels)

extract_any_shp("newshu.shp", "palette.dat")