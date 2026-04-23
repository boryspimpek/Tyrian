import os
from PIL import Image, ImageDraw, ImageFont

# --- KONFIGURACJA ---
BASE_FOLDER = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles"  # Folder bazowy z podfolderami
OUTPUT_FOLDER = r"C:\Users\borys\projekty\Tyrian\tyrian21\atlases"  # Folder na wygenerowane atlasy
TILES_PER_ROW = 20  # Ile kafelków w jednym rzędzie atlasu
TILE_W, TILE_H = 12, 14
PADDING = 10  # Miejsce na tekst (indeks kafelka)

def create_atlas(folder_path, output_path):
    # Pobierz listę plików i posortuj je numerami (block_0000, block_0001...)
    files = [f for f in os.listdir(folder_path) if f.endswith('.bmp')]
    files.sort()

    if not files:
        print("Brak plików BMP w folderze!")
        return

    num_tiles = len(files)
    num_rows = (num_tiles + TILES_PER_ROW - 1) // TILES_PER_ROW

    # Rozmiar pojedynczej komórki w atlasie (kafelek + miejsce na tekst)
    cell_w = TILE_W + 4
    cell_h = TILE_H + PADDING + 4

    atlas_w = TILES_PER_ROW * cell_w
    atlas_h = num_rows * cell_h

    # Stwórz obraz atlasu (ciemne tło, żeby widzieć jasne kafelki)
    atlas = Image.new('RGBA', (atlas_w, atlas_h), (40, 40, 40, 255))
    draw = ImageDraw.Draw(atlas)
    
    # Próba załadowania czcionki (jeśli nie masz, użyje domyślnej)
    try:
        font = ImageFont.load_default()
    except:
        font = None

    for i, filename in enumerate(files):
        row = i // TILES_PER_ROW
        col = i % TILES_PER_ROW

        x = col * cell_w
        y = row * cell_h

        # Ścieżka do kafelka
        tile_path = os.path.join(folder_path, filename)
        
        with Image.open(tile_path) as img:
            # Wklej kafelek
            atlas.paste(img.convert("RGBA"), (x + 2, y + PADDING))
            
            # Wyciągnij numer z nazwy (np. block_0077.bmp -> 77)
            # Uwaga: Tyrian w JSON może mieć przesunięcie +1 lub 0
            tile_num = int(filename.split('_')[1].split('.')[0])
            
            # Napisz numer nad kafelkiem
            draw.text((x + 2, y), str(tile_num), fill=(200, 200, 200), font=font)

    atlas.save(output_path)
    print(f"Atlas gotowy: {output_path} ({num_tiles} kafelków)")

if __name__ == "__main__":
    # Utwórz folder na wyjściowe atlasy jeśli nie istnieje
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Utworzono folder: {OUTPUT_FOLDER}")
    
    # Pobierz listę wszystkich podfolderów
    if not os.path.exists(BASE_FOLDER):
        print(f"Folder bazowy {BASE_FOLDER} nie istnieje!")
    else:
        subfolders = [f for f in os.listdir(BASE_FOLDER) if os.path.isdir(os.path.join(BASE_FOLDER, f))]
        subfolders.sort()
        
        print(f"Znaleziono {len(subfolders)} podfolderów")
        
        for folder_name in subfolders:
            folder_path = os.path.join(BASE_FOLDER, folder_name)
            output_filename = f"atlas_{folder_name}.png"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            print(f"\nPrzetwarzanie: {folder_name}")
            create_atlas(folder_path, output_path)
        
        print(f"\nZakończono! Atlasy zapisano w: {OUTPUT_FOLDER}")