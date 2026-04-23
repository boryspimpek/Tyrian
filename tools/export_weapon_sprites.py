"""
Tworzy folder weapon_sprites/ z kopiami sprite'ow nazwanymi wedlug schematu:
  port{idx:02d}_{name}__lvl{lvl:02d}__w{weapon_idx:04d}__{sheet}_{sprite_idx:04d}.bmp

Dla kazdego portu i poziomu mocy kopiowane sa wszystkie unikalne sprite'y.
"""

import json
import os
import shutil
import re

PORTS_JSON   = r"C:\Users\borys\projekty\Tyrian\data\weapon_ports.json"
MAP_JSON     = r"C:\Users\borys\projekty\Tyrian\data\weapon_sprite_map.json"
SPRITE_DIR   = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"
OUT_DIR      = r"C:\Users\borys\projekty\Tyrian\tyrian21\weapon_sprites"


def slugify(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    return name.strip('_')


def load():
    with open(PORTS_JSON) as f:
        ports = json.load(f)["weapon_ports"]
    with open(MAP_JSON) as f:
        smap = {w["weapon_index"]: w for w in json.load(f)}
    return ports, smap


def unique_sprites(sm):
    """Zwraca liste unikalnych (sheet, index, file) z pierwszych klatek wszystkich patternow."""
    seen = set()
    result = []
    for p in sm["patterns"]:
        fr = p["frames"][0]
        key = fr.get("file", "")
        if key and fr.get("exists") and key not in seen:
            seen.add(key)
            result.append(fr)
    return result


def export():
    ports, smap = load()
    os.makedirs(OUT_DIR, exist_ok=True)

    copied = 0
    skipped = 0

    for port in ports:
        port_idx  = port["index"]
        port_slug = slugify(port["name"])

        for mode_name in ("mode_1", "mode_2"):
            wpn_indices = port["firing_modes"].get(mode_name, [])
            mode_suffix = "" if mode_name == "mode_1" else "__mode2"

            for lvl, wpn_idx in enumerate(wpn_indices, start=1):
                if wpn_idx == 0:
                    continue
                sm = smap.get(wpn_idx)
                if not sm:
                    continue

                sprites = unique_sprites(sm)
                if not sprites:
                    skipped += 1
                    continue

                for fr in sprites:
                    src = os.path.join(SPRITE_DIR, fr["file"])
                    # Wyodrebnij sheet i indeks z nazwy pliku np. shots_0067.bmp
                    base = fr["file"].replace(".bmp", "")  # shots_0067

                    dst_name = (
                        f'port{port_idx:02d}_{port_slug}'
                        f'{mode_suffix}'
                        f'__lvl{lvl:02d}'
                        f'__w{wpn_idx:04d}'
                        f'__{base}.bmp'
                    )
                    dst = os.path.join(OUT_DIR, dst_name)
                    shutil.copy2(src, dst)
                    copied += 1

    print(f"Skopiowano: {copied} plikow  (pominieto {skipped} broni bez sprite'ow)")
    print(f"Folder: {OUT_DIR}")

    # Przyklad nazw
    examples = sorted(os.listdir(OUT_DIR))[:6]
    print("\nPrzykladowe nazwy:")
    for e in examples:
        print(f"  {e}")


if __name__ == "__main__":
    export()
