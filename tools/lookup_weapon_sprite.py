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
SPRITE_DIR   = r"C:\Users\borys\projekty\Tyrian\tyrian21\extracted_tiles\extracted_tyrian_shp"


def sg_to_file(sg):
    """Przelicza wartosc sg na nazwe pliku BMP. Zwraca None dla wartosci specjalnych."""
    if sg == 0 or sg >= 60000:
        return None
    frame = sg % 1000 if sg > 1000 else sg
    if frame > 500:
        return f"shots2_{frame - 500:04d}.bmp"
    if frame > 0:
        return f"shots_{frame:04d}.bmp"
    return None


def load():
    with open(PORTS_JSON)   as f: ports   = json.load(f)["weapon_ports"]
    with open(WEAPONS_JSON) as f: weapons = json.load(f)["TyrianHDT"]["weapon"]
    weapons = {int(w["index"], 16) if isinstance(w["index"], str) else w["index"]: w
               for w in weapons}
    return ports, weapons


def find_port(ports, query):
    try:
        idx = int(query)
        return [p for p in ports if p["index"] == idx]
    except (ValueError, TypeError):
        return [p for p in ports if query.lower() in p["name"].lower()]


def show_port(port, weapons):
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
            if not w:
                print(f'    [lvl {power_lvl+1}] weapon {wpn_idx}: brak danych')
                continue

            max_pos = w["max"]
            multi   = w["multi"]
            ani     = w["weapAni"]

            # Unikalne sprite'y ze wszystkich aktywnych patternow
            unique = {}
            for p in w["patterns"][:max_pos]:
                fname = sg_to_file(p["sg"])
                if fname:
                    mark = "" if os.path.exists(os.path.join(SPRITE_DIR, fname)) else " [BRAK]"
                    unique[fname + mark] = unique.get(fname + mark, 0) + 1

            parts = [f'{f} x{n}' if n > 1 else f for f, n in unique.items()]
            sprite_str = ", ".join(parts) if parts else "brak sprite'a"

            ani_note   = f'  anim={ani+1}kl' if ani > 0   else ''
            multi_note = f'  multi={multi}'   if multi > 1 else ''

            print(f'    [lvl {power_lvl+1}] weapon {wpn_idx}'
                  f'  cykl={max_pos}{multi_note}{ani_note}'
                  f'  ->  {sprite_str}')


def list_ports(ports):
    print("\nDostepne porty:")
    for p in ports:
        print(f'  {p["index"]:3d}  {p["name"]}')


if __name__ == "__main__":
    ports, weapons = load()

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
        show_port(port, weapons)
