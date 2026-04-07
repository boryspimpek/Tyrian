import os
import struct

def save_as_bmp(width, height, offset, filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "tyrian.shp")
    
    if not os.path.exists(file_path):
        return

    with open(file_path, "rb") as f:
        f.seek(offset)
        raw_data = f.read(width * height)

    if len(raw_data) < width * height:
        return

    # Nagłówek BMP (prosty 8-bit grayscale)
    file_size = 54 + 1024 + (width * height)
    bmp_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54 + 1024)
    dib_header = struct.pack('<IiiHHIIIIII', 40, width, -height, 1, 8, 0, width * height, 0, 0, 256, 0)
    
    # Paleta grayscale (0-255)
    palette = b""
    for i in range(256):
        palette += struct.pack('BBBB', i, i, i, 0)

    with open(os.path.join(script_dir, filename), "wb") as f:
        f.write(bmp_header)
        f.write(dib_header)
        f.write(palette)
        f.write(raw_data)
    
    print(f"Utworzono: {filename} (Szerokość: {width})")

# --- GŁÓWNA PĘTLA TESTOWA ---
# Przeskakujemy nagłówek banku (te 8 bajtów o których rozmawialiśmy)
start_offset = 0x2016B + 8 

# Tyrian często używa szerokości będących wielokrotnością 4 lub 8
for w in [24, 32, 40, 48, 64]:
    save_as_bmp(w, w, start_offset, f"test_w{w}.bmp")

print("\nGotowe! Sprawdź teraz pliki .bmp w folderze.")