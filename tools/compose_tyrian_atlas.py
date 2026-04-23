import os
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

SRC_FOLDER  = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"
OUT_FOLDER  = r"C:\Users\borys\projekty\Tyrian\tyrian21\atlases"
TILES_PER_ROW = 20
LABEL_H = 10   # piksele na etykietę indeksu nad sprite'em
GAP = 3        # odstęp między komórkami


def group_sprites(folder):
    """Zwraca dict: prefix -> posortowana lista (index, filepath)."""
    groups = defaultdict(list)
    for fname in os.listdir(folder):
        if not fname.endswith('.bmp'):
            continue
        parts = fname.rsplit('_', 1)
        if len(parts) != 2:
            continue
        prefix = parts[0]
        idx = int(parts[1].replace('.bmp', ''))
        groups[prefix].append((idx, os.path.join(folder, fname)))
    for v in groups.values():
        v.sort()
    return groups


def create_atlas(group_name, sprites, out_path):
    # Wczytaj wszystkie obrazy i wyznacz maksymalne wymiary komórki
    images = []
    for idx, path in sprites:
        img = Image.open(path).convert('RGBA')
        images.append((idx, img))

    if not images:
        return

    max_w = max(img.width  for _, img in images)
    max_h = max(img.height for _, img in images)
    cell_w = max_w + GAP
    cell_h = max_h + LABEL_H + GAP

    n = len(images)
    cols = min(n, TILES_PER_ROW)
    rows = (n + cols - 1) // cols

    atlas = Image.new('RGBA', (cols * cell_w, rows * cell_h), (40, 40, 40, 255))
    draw  = ImageDraw.Draw(atlas)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for i, (idx, img) in enumerate(images):
        col = i % cols
        row = i // cols
        x = col * cell_w
        y = row * cell_h
        # Wyśrodkuj sprite w komórce
        ox = x + (max_w - img.width)  // 2
        oy = y + LABEL_H + (max_h - img.height) // 2
        atlas.paste(img, (ox, oy), img)
        draw.text((x + 1, y + 1), str(idx), fill=(200, 200, 200), font=font)

    atlas.save(out_path)
    print(f"  {group_name}: {n} sprite'ow, rozmiar atlasu {atlas.width}x{atlas.height} -> {os.path.basename(out_path)}")


def main():
    if not os.path.exists(SRC_FOLDER):
        print(f"Brak folderu: {SRC_FOLDER}"); return

    os.makedirs(OUT_FOLDER, exist_ok=True)
    groups = group_sprites(SRC_FOLDER)

    if not groups:
        print("Brak sprite'ow do przetworzenia."); return

    print(f"Grupy: {sorted(groups.keys())}\n")
    for name in sorted(groups.keys()):
        out_path = os.path.join(OUT_FOLDER, f"atlas_tyrian_{name}.png")
        create_atlas(name, groups[name], out_path)

    print(f"\nZakonczono. Atlasy w: {OUT_FOLDER}")


if __name__ == "__main__":
    main()
