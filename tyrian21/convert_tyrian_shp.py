import struct
import os

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
        out.write(header)
        out.write(dib)
        out.write(palette)
        out.write(bmp_pixels)

def extract_tyrian_main_shp(file_path, pal_path):
    if not os.path.exists(file_path): return
    
    output_dir = "extracted_tyrian_main"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    with open(file_path, "rb") as f:
        # tyrian.shp ma na początku liczbę banków (zwykle 12)
        num_banks = struct.unpack('<H', f.read(2))[0]
        # Potem idą 4-bajtowe offsety (longint)
        bank_offsets = []
        for _ in range(num_banks):
            bank_offsets.append(struct.unpack('<I', f.read(4))[0])
        
        bank_offsets.append(os.path.getsize(file_path)) # Koniec pliku jako ostatni offset

        for b_idx in range(num_banks):
            start_off = bank_offsets[b_idx]
            end_off = bank_offsets[b_idx + 1]
            f.seek(start_off)
            
            print(f"Przetwarzam Bank {b_idx} (Offset: {start_off})...")
            
            # Banki 0-6 to czcionki/interfejs (Format Sprite1: W, H na początku każdego sprita)
            if b_idx <= 7:
                # W tych bankach zazwyczaj jest pod-tabela offsetów
                try:
                    num_sub = struct.unpack('<H', f.read(2))[0]
                    sub_offsets = []
                    for _ in range(num_sub):
                        so = struct.unpack('<H', f.read(2))[0]
                        if so > 0: sub_offsets.append(start_off + so)
                    
                    for s_idx, off in enumerate(sub_offsets):
                        f.seek(off)
                        w, h = struct.unpack('BB', f.read(2))
                        if 0 < w < 320 and 0 < h < 240:
                            f.seek(off + 4) # Pomiń nagłówek
                            pixels = bytearray([0] * (w * h))
                            # Dekodowanie RLE typu 1
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
                                        if ptr < len(pixels): pixels[ptr] = b
                                        ptr += 1
                            save_bmp(w, h, pixels, pal_path, f"{output_dir}/bank{b_idx}_item{s_idx}.bmp")
                except: pass

            # Bank 9: STATKI GRACZA (Format Sprite2: klocki 12x14)
            elif b_idx == 9:
                # Statki gracza to po prostu ciąg klocków RLE-Nibble
                # Czytamy aż do końca banku
                block_idx = 0
                while f.tell() < end_off:
                    block_start = f.tell()
                    w, h = 12, 14
                    pixels = bytearray([0] * (w * h))
                    x, y = 0, 0
                    valid = False
                    while True:
                        byte = f.read(1)
                        if not byte or byte[0] == 0x0F: break
                        ctrl = byte[0]
                        skip = ctrl & 0x0F
                        draw = (ctrl & 0xF0) >> 4
                        x += skip
                        if draw == 0:
                            y += 1
                            x = 0
                        else:
                            valid = True
                            for _ in range(draw):
                                p = f.read(1)
                                if p and y < h and x < w: pixels[y*w + x] = p[0]
                                x += 1
                        if y >= h: break
                    
                    if valid and any(pixels):
                        save_bmp(w, h, pixels, pal_path, f"{output_dir}/player_ship_block_{block_idx:03d}.bmp")
                        block_idx += 1
                    
                    # Zabezpieczenie przed utknięciem
                    if f.tell() == block_start: f.read(1)

# Uruchomienie
extract_tyrian_main_shp("tyrian.shp", "palette.dat")