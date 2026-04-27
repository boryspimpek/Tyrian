"""
Eksportuje sprite'y pocisków używane przez wrogów do folderu weapon_sprites/ w Galaxid.
Naming convention (zgodna z DataManager._scan_weapon_sprites):
  enemy__w{weapon_idx:04d}__{sheet}_{sprite_idx:04d}.png

Ostatni segment po __ musi pasować do klucza sg_to_key() z DataManager.
"""

import json
import os
import shutil

ENEMIES_JSON = r"C:\Users\borys\projekty\Tyrian\data\enemies.json"
WEAPONS_JSON = r"C:\Users\borys\projekty\Tyrian\data\weapon.json"
SPRITE_DIR   = r"C:\Users\borys\projekty\Tyrian\extracted_tiles\extracted_tyrian_shp"
OUT_DIR      = r"C:\Users\borys\projekty\Galaxid\data\weapon_sprites"

SPECIAL_TUR = {251, 252, 253, 254, 255}


def sg_to_file(sg):
    if sg == 0 or sg >= 60000:
        return None
    frame = sg % 1000 if sg > 1000 else sg
    if frame > 500:
        return f"shots2_{frame - 500:04d}.png"
    if frame > 0:
        return f"shots_{frame:04d}.png"
    return None


def load():
    with open(ENEMIES_JSON) as f:
        enemies = json.load(f)
    with open(WEAPONS_JSON) as f:
        wdata = json.load(f)
    weapons = {
        (int(w["index"], 16) if isinstance(w["index"], str) else w["index"]): w
        for w in wdata["TyrianHDT"]["weapon"]
    }
    return enemies, weapons


def collect_enemy_weapon_ids(enemies):
    ids = set()
    for e in enemies:
        for t in e.get("tur", []):
            if t and t not in SPECIAL_TUR:
                ids.add(t)
    return ids


def export():
    enemies, weapons = load()
    os.makedirs(OUT_DIR, exist_ok=True)

    weapon_ids = collect_enemy_weapon_ids(enemies)

    copied  = 0
    skipped = 0
    missing = 0

    for wid in sorted(weapon_ids):
        w = weapons.get(wid)
        if not w:
            continue

        anim_count = max(1, w.get("weapAni", 0))
        seen = set()
        for p in w["patterns"][:w["max"]]:
            sg0 = p["sg"]
            fname0 = sg_to_file(sg0)
            if not fname0 or fname0 in seen:
                continue
            seen.add(fname0)

            # Eksportuj klatkę bazową + wszystkie klatki animacji
            for i in range(anim_count):
                fname = sg_to_file(sg0 + i)
                if not fname:
                    continue

                src = os.path.join(SPRITE_DIR, fname)
                if not os.path.exists(src):
                    missing += 1
                    print(f"  BRAK: {fname}  (wid={wid})")
                    continue

                dst_name = f"enemy__w{wid:04d}__{fname}"
                dst = os.path.join(OUT_DIR, dst_name)

                if os.path.exists(dst):
                    skipped += 1
                    continue

                shutil.copy2(src, dst)
                copied += 1

    print(f"\nSkopiowano: {copied}  Pominięto (już istnieje): {skipped}  Brak źródła: {missing}")
    print(f"Folder: {OUT_DIR}")


if __name__ == "__main__":
    export()
