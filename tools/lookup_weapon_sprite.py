"""
Lookup: port -> weapon -> sprite

Uzycie:
  py lookup_weapon_sprite.py 20          # po indeksie portu
  py lookup_weapon_sprite.py "missile"   # po fragmencie nazwy (case-insensitive)
  py lookup_weapon_sprite.py             # wylistuj wszystkie porty
"""

import json
import sys
import os

PORTS_JSON   = r"C:\Users\borys\projekty\Tyrian\data\weapon_ports.json"
WEAPONS_JSON = r"C:\Users\borys\projekty\Tyrian\data\weapon.json"
MAP_JSON     = r"C:\Users\borys\projekty\Tyrian\data\weapon_sprite_map.json"
SPRITE_DIR   = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"


def load():
    with open(PORTS_JSON)   as f: ports_data   = json.load(f)
    with open(WEAPONS_JSON) as f: weapons_data = json.load(f)
    with open(MAP_JSON)     as f: sprite_map   = json.load(f)

    ports   = ports_data["weapon_ports"]
    weapons = {int(w["index"], 16) if isinstance(w["index"], str) else w["index"]: w
               for w in weapons_data["TyrianHDT"]["weapon"]}
    smap    = {w["weapon_index"]: w for w in sprite_map}
    return ports, weapons, smap


def find_port(ports, query):
    try:
        idx = int(query)
        found = [p for p in ports if p["index"] == idx]
    except (ValueError, TypeError):
        found = [p for p in ports if query.lower() in p["name"].lower()]
    return found


def show_port(port, weapons, smap):
    print(f'\n=== Port {port["index"]}: {port["name"]} ===')
    print(f'    koszt: {port["stats"]["cost"]}  '
          f'zuzycie mocy: {port["stats"]["power_use"]}')

    for mode_name in ("mode_1", "mode_2"):
        wpn_indices = port["firing_modes"].get(mode_name, [])
        active = [(i, idx) for i, idx in enumerate(wpn_indices) if idx != 0]
        if not active:
            continue

        print(f'\n  {mode_name}:')
        for power_lvl, wpn_idx in active:
            w = weapons.get(wpn_idx)
            sm = smap.get(wpn_idx)
            if not w or not sm:
                print(f'    [lvl {power_lvl+1}] weapon {wpn_idx}: brak danych')
                continue

            # Unikalne sprite'y (pierwsza klatka kazdego patternu)
            unique_sprites = {}
            for p in sm["patterns"]:
                fr = p["frames"][0]
                fname = fr.get("file", "")
                mark = "" if fr.get("exists", False) else " [BRAK]"
                unique_sprites[fname + mark] = unique_sprites.get(fname + mark, 0) + 1

            ani     = w["weapAni"]
            max_pos = w["max"]
            multi   = w["multi"]

            parts = []
            for fname, count in unique_sprites.items():
                parts.append(f'{fname} x{count}' if count > 1 else fname)
            sprite_str = ", ".join(parts)

            ani_note  = f'  anim={ani+1}kl'   if ani > 0   else ''
            multi_note = f'  multi={multi}'    if multi > 1 else ''

            print(f'    [lvl {power_lvl+1}] weapon {wpn_idx}'
                  f'  cykl={max_pos}{multi_note}{ani_note}'
                  f'  ->  {sprite_str}')


def list_ports(ports):
    print("\nDostepne porty:")
    for p in ports:
        print(f'  {p["index"]:3d}  {p["name"]}')


if __name__ == "__main__":
    ports, weapons, smap = load()

    if len(sys.argv) < 2:
        list_ports(ports)
        sys.exit(0)

    query = sys.argv[1]
    found = find_port(ports, query)

    if not found:
        print(f'Nie znaleziono portu dla: "{query}"')
        list_ports(ports)
        sys.exit(1)

    for port in found:
        show_port(port, weapons, smap)
