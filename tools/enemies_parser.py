import struct
import json
import sys
import os

def resolve_path(filename):
    """Obsługuje ścieżki względne do skryptu."""
    if not os.path.isabs(filename):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)
    return filename

# Liczba wrogów w Tyrian (850 rekordów + 1 pusty)
ENEMY_NUM = 851 

struct_fmt = "<B 3B 3B bbbbbb hh bb BB 20H B BB bb H b b B H h H"

def unpack_enemy(data):
    try:
        tup = struct.unpack(struct_fmt, data)
        d = {}
        
        # Podstawowe parametry
        d['ani'] = tup[0]
        d['tur'] = list(tup[1:4])
        d['freq'] = list(tup[4:7])
        d['xmove'] = tup[7]
        d['ymove'] = tup[8]
        d['xaccel'] = tup[9]
        d['yaccel'] = tup[10]
        d['xcaccel'] = tup[11]
        d['ycaccel'] = tup[12]
        d['startx'] = tup[13]
        d['starty'] = tup[14]
        d['startxc'] = tup[15]
        d['startyc'] = tup[16]
        d['armor'] = tup[17]
        d['esize'] = tup[18]
        
        # Grafika (40 bajtów - 20 wartości 16-bitowych)
        d['egraphic'] = list(tup[19:39])
        
        # Pola po grafice
        d['explosiontype'] = tup[39]
        d['animate'] = tup[40]
        d['shapebank'] = tup[41]
        d['xrev'] = tup[42]
        d['yrev'] = tup[43]
        d['dgr'] = tup[44]
        d['dlevel'] = tup[45]
        d['dani'] = tup[46]
        d['elaunchfreq'] = tup[47]
        d['elaunchtype'] = tup[48]
        d['value'] = tup[49]
        d['eenemydie'] = tup[50]
        
        return d
    except struct.error as e:
        print(f"Błąd rozpakowywania: {e}")
        return None

def parse_hdt_enemies(hdt_path, output_json):
    enemies_data = []
    record_size = struct.calcsize(struct_fmt) # Powinno być dokładnie 80

    hdt_path = resolve_path(hdt_path)
    if not os.path.exists(hdt_path):
        print(f"Błąd: Nie znaleziono pliku {hdt_path}")
        return

    try:
        with open(hdt_path, "rb") as f:
            file_size = os.path.getsize(hdt_path)
            # Przeciwnicy znajdują się na samym końcu pliku HDT
            enemy_start = file_size - (ENEMY_NUM * record_size)
            
            if enemy_start < 0:
                print("Błąd: Rozmiar pliku za mały dla podanej liczby wrogów.")
                return

            f.seek(enemy_start)
            print(f"Parsowanie {ENEMY_NUM} przeciwników od offsetu {enemy_start}...")

            for i in range(ENEMY_NUM):
                chunk = f.read(record_size)
                if len(chunk) < record_size:
                    break
                
                enemy_dict = unpack_enemy(chunk)
                if enemy_dict:
                    enemy_dict['index'] = i
                    enemies_data.append(enemy_dict)

        with open(output_json, "w", encoding="utf-8") as outf:
            json.dump(enemies_data, outf, indent=2, ensure_ascii=False)
        
        print(f"Sukces! Zapisano {len(enemies_data)} rekordów do {output_json}")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    # Użycie: python enemies_parser.py tyrian.hdt enemies.json
    hdt_input = sys.argv[1] if len(sys.argv) > 1 else "tyrian.hdt"
    json_output = sys.argv[2] if len(sys.argv) > 2 else "enemies.json"
    
    parse_hdt_enemies(hdt_input, json_output)