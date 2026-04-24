"""
Tworzy folder weapon_sprites/ z kopiami sprite'ow nazwanymi wedlug schematu:
  port{idx:02d}_{name}__lvl{lvl:02d}__w{weapon_idx:04d}__{sheet}_{sprite_idx:04d}.png

Dla kazdego portu i poziomu mocy kopiowane sa wszystkie unikalne sprite'y.
"""

import json
import os
import shutil
import re

PORTS_JSON   = r"C:\Users\borys\projekty\Tyrian\data\weapon_ports.json"
WEAPONS_JSON = r"C:\Users\borys\projekty\Tyrian\data\weapon.json"
SPRITE_DIR   = r"C:\Users\borys\projekty\Tyrian\extracted_tiles\extracted_tyrian_shp"
OUT_DIR      = r"C:\Users\borys\projekty\Tyrian\extracted_weapon_sprites"


def sg_to_file(sg):
    """Przelicza wartosc sg na nazwe pliku PNG. Zwraca None dla wartosci specjalnych."""
    if sg == 0 or sg >= 60000:
        return None
    frame = sg % 1000 if sg > 1000 else sg
    if frame > 500:
        return f"shots2_{frame - 500:04d}.png"
    if frame > 0:
        return f"shots_{frame:04d}.png"
    return None


def slugify(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    return name.strip('_')


def load():
    with open(PORTS_JSON)   as f: ports   = json.load(f)["weapon_ports"]
    with open(WEAPONS_JSON) as f: weapons = json.load(f)["TyrianHDT"]["weapon"]
    weapons = {int(w["index"], 16) if isinstance(w["index"], str) else w["index"]: w
               for w in weapons}
    return ports, weapons


def export():
    ports, weapons = load()
    os.makedirs(OUT_DIR, exist_ok=True)

    copied  = 0
    missing = 0

    for port in ports:
        port_idx  = port["index"]
        port_slug = slugify(port["name"])

        for mode_name in ("mode_1", "mode_2"):
            wpn_indices = port["firing_modes"].get(mode_name, [])
            mode_suffix = "" if mode_name == "mode_1" else "__mode2"

            for lvl, wpn_idx in enumerate(wpn_indices, start=1):
                if wpn_idx == 0:
                    continue
                w = weapons.get(wpn_idx)
                if not w:
                    continue

                # Unikalne sprite'y ze wszystkich aktywnych patternow
                seen = set()
                for p in w["patterns"][:w["max"]]:
                    fname = sg_to_file(p["sg"])
                    if not fname or fname in seen:
                        continue
                    seen.add(fname)

                    src = os.path.join(SPRITE_DIR, fname)
                    if not os.path.exists(src):
                        missing += 1
                        continue

                    base = fname.replace(".png", "")
                    dst_name = (
                        f'port{port_idx:02d}_{port_slug}'
                        f'{mode_suffix}'
                        f'__lvl{lvl:02d}'
                        f'__w{wpn_idx:04d}'
                        f'__{base}.png'
                    )
                    shutil.copy2(src, os.path.join(OUT_DIR, dst_name))
                    copied += 1

    print(f"Skopiowano: {copied} plikow  (brakujacych sprite'ow: {missing})")
    print(f"Folder: {OUT_DIR}")
    examples = sorted(os.listdir(OUT_DIR))[:6]
    print("\nPrzykladowe nazwy:")
    for e in examples:
        print(f"  {e}")


if __name__ == "__main__":
    export()
