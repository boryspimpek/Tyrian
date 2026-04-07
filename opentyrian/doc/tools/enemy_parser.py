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

# Liczba wrogów (850 zgodnie z ENEMY_NUM, ale często +1 jako pusty slot) [cite: 2]
ENEMY_NUM = 851 

# NOWY FORMAT (80 bajtów):
# < - Little Endian
# B/b (1 bajt), H/h (2 bajty)
# egraphic zajmuje 40 bajtów (20 klatek * 2 bajty) 
struct_fmt = "<B 3B 3B bbbbbb hh bb BB 20H B BB bb H b b B H h H"

def unpack_enemy(data):
    try:
        tup = struct.unpack(struct_fmt, data)
        d = {}
        
        # Podstawowe parametry 
        d['ani'] = tup[0]
        d['tur'] = list(tup[1:4])       # Strzały (down, right, left) 
        d['freq'] = list(tup[4:7])      # Częstotliwość strzału 
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
        d['armor'] = tup[17]            # HP wroga 
        d['esize'] = tup[18]            # Hitbox 
        
        # TWOJE KAFELKI (20 wartości 16-bitowych) [cite: 10]
        # To tutaj znajdziesz te numery, z których składasz obraz
        d['egraphic'] = list(tup[19:39]) 
        
        # Pola po grafice (przesunięte o 19 pozycji w krotce) 
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
        d['value'] = tup[49]            # Punkty 
        d['enemydie'] = tup[50]         # Akcja przy śmierci 
        
        return d
    except struct.error:
        return None

def parse_hdt_enemies(hdt_path, output_json):
    enemies_data = []
    record_size = struct.calcsize(struct_fmt)

    try:
        with open(hdt_path, "rb") as f:
            file_size = os.path.getsize(hdt_path)
            # Tyrian przechowuje wrogów na końcu pliku .hdt 
            enemy_start = file_size - (ENEMY_NUM * record_size)
            
            if enemy_start < 0:
                print("Błąd: Obliczony offset jest ujemny. Sprawdź ENEMY_NUM.")
                return

            f.seek(enemy_start)
            print(f"Rozpoczynam czytanie z offsetu: {enemy_start}")

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
        print(f"Błąd: {e}")

if __name__ == "__main__":
    hdt_in = resolve_path("tyrian.hdt")
    json_out = resolve_path("enemies.json")
    parse_hdt_enemies(hdt_in, json_out)