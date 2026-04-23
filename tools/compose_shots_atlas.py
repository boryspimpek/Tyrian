"""
Generuje annotowane atlasy shots i shots2 z numerami broni pod kazda grafika.
Tworzy tez plik reverse_map.json: sprite -> lista broni ktore go uzywaja.
"""

import json
import os
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

WEAPON_MAP  = r"C:\Users\borys\projekty\Tyrian\data\weapon_sprite_map.json"
SPRITE_DIR  = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"
OUT_DIR     = r"C:\Users\borys\projekty\Tyrian\tyrian21\atlases"

TILES_PER_ROW = 20
LABEL_TOP  = 10   # miejsce na indeks sprite'a
LABEL_BOT  = 18   # miejsce na numery broni (moze byc kilka linii)
GAP        = 2


def build_reverse_map():
    """sprite_key -> lista weapon_index ktore go uzywaja (tylko pierwsza klatka animacji)."""
    with open(WEAPON_MAP, encoding="utf-8") as f:
        mapping = json.load(f)

    rev = defaultdict(list)
    for w in mapping:
        widx = w["weapon_index"]
        for p in w["patterns"]:
            for fr in p["frames"]:
                key = fr.get("file")
                if key and fr.get("exists"):
                    if widx not in rev[key]:
                        rev[key].append(widx)
    return dict(rev)


def make_atlas(bank_prefix, reverse_map):
    files = sorted(
        f for f in os.listdir(SPRITE_DIR)
        if f.startswith(bank_prefix + "_") and f.endswith(".bmp")
    )
    if not files:
        print(f"Brak plikow dla {bank_prefix}"); return

    # Wczytaj wszystkie obrazy
    images = []
    for fname in files:
        img = Image.open(os.path.join(SPRITE_DIR, fname)).convert("RGBA")
        weapons = reverse_map.get(fname, [])
        images.append((fname, img, weapons))

    max_w = max(img.width  for _, img, _ in images)
    max_h = max(img.height for _, img, _ in images)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    cell_w = max_w + GAP * 2
    cell_h = max_h + LABEL_TOP + LABEL_BOT + GAP * 2

    cols = min(len(images), TILES_PER_ROW)
    rows = (len(images) + cols - 1) // cols

    atlas = Image.new("RGBA", (cols * cell_w, rows * cell_h), (30, 30, 30, 255))
    draw  = ImageDraw.Draw(atlas)

    for i, (fname, img, weapons) in enumerate(images):
        col = i % cols
        row = i // cols
        cx  = col * cell_w
        cy  = row * cell_h

        # Indeks sprite'a (z nazwy pliku)
        sprite_idx = int(fname.split("_")[1].replace(".bmp", ""))
        draw.text((cx + 1, cy + 1), str(sprite_idx), fill=(160, 160, 255), font=font)

        # Sprite wycentrowany
        ox = cx + GAP + (max_w - img.width)  // 2
        oy = cy + LABEL_TOP + (max_h - img.height) // 2
        atlas.paste(img, (ox, oy), img)

        # Numery broni pod sprite'm
        if weapons:
            # Skroc jesli za duzo
            label = ",".join(str(w) for w in weapons[:6])
            if len(weapons) > 6:
                label += f"+{len(weapons)-6}"
            draw.text((cx + 1, cy + LABEL_TOP + max_h + GAP + 1),
                      label, fill=(255, 200, 80), font=font)
        else:
            draw.text((cx + 1, cy + LABEL_TOP + max_h + GAP + 1),
                      "-", fill=(80, 80, 80), font=font)

    out_path = os.path.join(OUT_DIR, f"atlas_tyrian_{bank_prefix}_annotated.png")
    atlas.save(out_path)
    print(f"{bank_prefix}: {len(images)} sprite'ow -> {os.path.basename(out_path)}  ({atlas.width}x{atlas.height}px)")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Buduje odwrocona mape sprite -> bronie...")
    rev = build_reverse_map()

    used = sum(1 for v in rev.values() if v)
    print(f"Sprite'ow uzywanych przez bronie: {used}\n")

    make_atlas("shots",  rev)
    make_atlas("shots2", rev)
