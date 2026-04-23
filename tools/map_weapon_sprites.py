"""
Mapuje bronie z weapon.json na konkretne sprite'y z bankow 7 i 11 tyrian.shp.

Logika z shots.c:
  anim_frame = sg + shotAni  (shotAni: 0..weapAni)
  jesli anim_frame > 60000  -> OPTION_SHAPES, indeks = anim_frame - 60001
  jesli anim_frame > 1000   -> iskra koloru (anim_frame//1000), potem mod 1000
  jesli anim_frame > 500    -> shots2 (bank 11), indeks = anim_frame - 500
  jesli anim_frame <= 500   -> shots  (bank 7),  indeks = anim_frame
"""

import json
import os

WEAPON_JSON = r"C:\Users\borys\projekty\Tyrian\data\weapon.json"
OUT_JSON    = r"C:\Users\borys\projekty\Tyrian\data\weapon_sprite_map.json"
SPRITE_DIR  = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"


def sg_to_sprite(sg, wea_ani):
    """Zwraca listę klatek animacji: [{sheet, index, spark_color?}]"""
    frames = []
    for ani in range(wea_ani + 1):
        frame = sg + ani

        if frame >= 60000:
            frames.append({
                "sheet": "option_shapes",
                "index": frame - 60001,
            })
            continue

        spark_color = None
        if frame > 1000:
            spark_color = frame // 1000
            frame = frame % 1000

        if frame > 500:
            entry = {"sheet": "shots2", "index": frame - 500,
                     "file": f"shots2_{frame - 500:04d}.bmp"}
        else:
            entry = {"sheet": "shots",  "index": frame,
                     "file": f"shots_{frame:04d}.bmp"}

        if spark_color is not None:
            entry["spark_color"] = spark_color

        entry["exists"] = os.path.exists(os.path.join(SPRITE_DIR, entry["file"]))
        frames.append(entry)

    return frames


def build_map():
    with open(WEAPON_JSON, encoding="utf-8") as f:
        data = json.load(f)
    weapons = data["TyrianHDT"]["weapon"]

    result = []
    for w in weapons:
        idx   = int(w["index"], 16) if isinstance(w["index"], str) else w["index"]
        max_p = w["max"]        # ile aktywnych patternow (1..max)
        ani   = w["weapAni"]    # klatek animacji = ani+1

        patterns_out = []
        for p_i in range(max_p):
            if p_i >= len(w["patterns"]):
                break
            sg = w["patterns"][p_i]["sg"]
            if sg == 0:
                continue

            frames = sg_to_sprite(sg, ani)
            patterns_out.append({
                "pattern": p_i + 1,
                "sg": sg,
                "frames": frames,
            })

        if not patterns_out:
            continue

        result.append({
            "weapon_index": idx,
            "weapAni": ani,
            "multi": w["multi"],
            "patterns": patterns_out,
        })

    return result


def print_summary(mapping):
    missing = 0
    for w in mapping:
        for p in w["patterns"]:
            for fr in p["frames"]:
                if fr.get("exists") is False:
                    missing += 1

    print(f"Broni z aktywnymi sprite'ami: {len(mapping)}")
    print(f"Brakujacych plikow BMP:        {missing}")

    # Przykladowe wpisy
    print("\nPrzyklad weapon[1]:")
    first = next((w for w in mapping if w["weapon_index"] == 1), None)
    if first:
        print(json.dumps(first, indent=2))


if __name__ == "__main__":
    mapping = build_map()
    print_summary(mapping)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"\nZapisano: {OUT_JSON}  ({len(mapping)} broni)")
