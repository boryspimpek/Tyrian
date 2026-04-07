import os

def save_raw_sprite():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "tyrian.shp")
    
    # Zakładamy wymiary dla testu (np. 24x24 to standard dla małych wrogów)
    W, H = 24, 24 
    
    with open(file_path, "rb") as f:
        # Skaczemy tam, gdzie zaczynają się "pstrokate" dane w Banku 4
        # Omijamy nagłówek banku (8 bajtów)
        f.seek(0x2016B + 8) 
        raw_pixels = f.read(W * H)

    # Zapisujemy jako surowy plik danych (możesz go otworzyć w Photoshopie/GIMP jako Raw Data)
    out_path = os.path.join(script_dir, "test_sprite.raw")
    with open(out_path, "wb") as out:
        out.write(raw_pixels)
    
    print(f"Zapisano surowe piksele do: {out_path}")
    print(f"Wymiary testowe: {W}x{H}. Otwórz w GIMP jako 'Raw Image Data', Gray8 lub Indexed.")

if __name__ == "__main__":
    save_raw_sprite()