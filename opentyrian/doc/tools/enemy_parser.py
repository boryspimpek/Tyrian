import struct
import json
import sys
import os

def resolve_path(filename):
    """Zamienia ścieżkę na bezwzględną, obsługuje ścieżki względne do skryptu"""
    if not os.path.isabs(filename):
        # Jeśli ścieżka jest względna, zwróć ją względem katalogu skryptu
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, filename)
    return filename

# Liczba wrogów w Tyrianie (zgodnie z kodem źródłowym)
ENEMY_NUM = 850 

# Definicja struktury binarnej jednego wroga (na podstawie JE_EnemyDatType z episodes.h)
# < - mały endian (Little Endian)
# B - unsigned byte (1 bajt), b - signed byte (1 bajt), H - unsigned short (2 bajty), h - signed short (2 bajty), i - signed int (2 bajty)
struct_fmt = "<B 3B 3B bbbbb bb hh BB 20H B BB bb H H h h B H h"

def unpack_enemy(data):
    tup = struct.unpack(struct_fmt, data)
    d = {}
    
    d['ani'] = tup[0]               # Animacja
    d['tur'] = list(tup[1:4])       # ID broni (3 bronie)
    d['freq'] = list(tup[4:7])      # Częstotliwość strzału (3 wartości)
    d['xmove'] = tup[7]             # Prędkość X (signed byte)
    d['ymove'] = tup[8]             # Prędkość Y (signed byte)
    d['xaccel'] = tup[9]            # Akceleracja X (signed byte)
    d['yaccel'] = tup[10]           # Akceleracja Y (signed byte)
    d['xcaccel'] = tup[11]          # Dodatkowa akceleracja X (signed byte)
    d['ycaccel'] = tup[12]          # Dodatkowa akceleracja Y (signed byte)
    d['startx'] = tup[13]           # Pozycja startowa X (signed short)
    d['starty'] = tup[14]           # Pozycja startowa Y (signed short)
    d['startxc'] = tup[15]          # Prędkość startowa X (signed byte)
    d['startyc'] = tup[16]          # Prędkość startowa Y (signed byte)
    d['armor'] = tup[17]             # HP wroga (unsigned byte)
    d['esize'] = tup[18]            # Rozmiar Hitboxa (unsigned byte)
    d['egraphic'] = list(tup[19:39]) # Klatki animacji (20 klatek, unsigned short)
    d['explosiontype'] = tup[39]     # Typ eksplozji (unsigned byte)
    d['animate'] = tup[40]           # Flaga animacji (unsigned byte)
    d['shapebank'] = tup[41]         # Bank kształtów (unsigned byte)
    d['xrev'] = tup[42]              # Reverse X (signed byte)
    d['yrev'] = tup[43]              # Reverse Y (signed byte)
    d['elaunchfreq'] = tup[44]       # Częstotliwość launch (unsigned byte)
    d['elaunchtype'] = tup[45]       # Typ launch (unsigned short)
    d['value'] = tup[46]             # Punkty za zniszczenie (signed short)
    
    return d

def parse_hdt_enemies(hdt_path, output_json):
    enemies_data = []

    try:
        with open(hdt_path, "rb") as f:
            # Wczytujemy offset z nagłówka i ustawiamy pozycję na końcu pliku
            # Dane wrogów prawdopodobnie są na końcu pliku .hdt
            file_size = os.path.getsize(hdt_path)
            
            # Wrogowie zajmują 850 * 77 = 65450 bajtów
            enemy_start = file_size - (ENEMY_NUM * struct.calcsize(struct_fmt))
            f.seek(enemy_start)
            
            print(f"Wczytywanie wrogów z offsetu: {enemy_start} (rozmiar pliku: {file_size})")

            print("Konwertowanie wrogów...")
            for i in range(ENEMY_NUM):
                chunk = f.read(struct.calcsize(struct_fmt))
                if len(chunk) < struct.calcsize(struct_fmt):
                    break
                
                enemy_dict = unpack_enemy(chunk)
                enemy_dict['index'] = i
                enemies_data.append(enemy_dict)
                
                if i % 100 == 0:
                    print(f"Przetworzono {i} wrogów...")

        # Zapis do JSON
        with open(output_json, "w", encoding="utf-8") as outf:
            json.dump(enemies_data, outf, indent=2, ensure_ascii=False)
        
        print(f"Gotowe! Dane zapisano w {output_json}")
        
    except IOError:
        print(f"Błąd: Nie można otworzyć {hdt_path}")
        return

if __name__ == "__main__":
    # Domyślne ścieżki jeśli nie podano argumentów
    if len(sys.argv) < 3:
        hdt_path = resolve_path("tyrian.hdt")
        output_path = resolve_path("enemies.json")
        print(f"Użycie domyślne ścieżek:")
        print(f"  Wejście: {hdt_path}")
        print(f"  Wyjście: {output_path}")
    else:
        hdt_path = resolve_path(sys.argv[1])
        output_path = resolve_path(sys.argv[2])
    
    parse_hdt_enemies(hdt_path, output_path)