import os
import struct

def extract_tyrian_ultimate(target_index, output_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # --- KROK 1: IDENTYFIKACJA BANKU ---
    current_index = target_index
    shp_files = ["newsh1.shp", "newsh2.shp", "newsh3.shp", "newsh4.shp"]
    selected_file = None
    
    for shp in shp_files:
        path = os.path.join(script_dir, shp)
        if not os.path.exists(path): continue
        
        with open(path, "rb") as f:
            first_off = struct.unpack('<H', f.read(2))[0]
            num_in_bank = first_off // 2
            if current_index < num_in_bank:
                selected_file = shp
                break
            else:
                current_index -= num_in_bank

    if not selected_file:
        print(f"Nie znaleziono indeksu {target_index} w plikach SHP.")
        return

    print(f"Dekodowanie: {selected_file} | Lokalny ID: {current_index}")

    # --- KROK 2: ODCZYT STRUKTURY ---
    with open(os.path.join(script_dir, selected_file), "rb") as f:
        f.seek(current_index * 2)
        shape_start = struct.unpack('<H', f.read(2))[0]
        
        f.seek(shape_start)
        width = struct.unpack('B', f.read(1))[0]
        height = struct.unpack('B', f.read(1))[0]
        
        if width == 0 or height == 0: return

        # Odczyt tabeli offsetów dla KAŻDEJ linii (klucz do poprawnego obrazu)
        line_offsets = []
        for _ in range(height):
            line_offsets.append(struct.unpack('<H', f.read(2))[0])

        # --- KROK 3: DEKODOWANIE RLE LINIA PO LINII ---
        pixels = bytearray(width * height)
        
        for y in range(height):
            # Skok do danych konkretnej linii
            f.seek(line_offsets[y])
            x = 0
            while x < width:
                control = f.read(2)
                if len(control) < 2: break
                skip, draw = struct.unpack('BB', control)
                
                # Warunek końca linii (Tyrian często używa 0,0 lub skip=255)
                if skip == 0 and draw == 0 and x > 0: break
                
                x += skip
                if draw > 0:
                    colors = f.read(draw)
                    for c in colors:
                        if x < width:
                            pixels[y * width + x] = c
                            x += 1

    # --- KROK 4: GENEROWANIE BMP Z ROZJAŚNIONĄ PALETĄ ---
    # Używamy mnożnika *4, aby ciemne kolory Tyriana były widoczne w szarości
    file_size = 54 + 1024 + (width * height)
    bmp_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54 + 1024)
    dib_header = struct.pack('<IiiHHIIIIII', 40, width, -height, 1, 8, 0, width * height, 0, 0, 256, 0)
    
    palette = b""
    for i in range(256):
        # Rozjaśniamy, żeby "wyciągnąć" detale z ciemnych indeksów
        v = min(i * 4, 255) 
        palette += struct.pack('BBBB', v, v, v, 0)

    with open(os.path.join(script_dir, output_name), "wb") as f:
        f.write(bmp_header)
        f.write(dib_header)
        f.write(palette)
        f.write(pixels)
    
    print(f"Gotowe! Wymiary: {width}x{height}. Plik: {output_name}")

# Przykładowe wywołanie dla Twojego wroga i chmury
# Szybka identyfikacja obiektu 450
extract_tyrian_ultimate(100, "identyfikacja_100.bmp")