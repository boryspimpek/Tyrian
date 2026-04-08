#!/bin/env python
import struct
import sys
import json
import os

# Dane na podstawie tyrian.hdt.txt
WEAP_NUM = 780
PORT_NUM = 42
WEAPON_STRUCT_SIZE = 0x50 # 80 bajtów

# Format dla weaponPort: B (str_len), 30s (name), B (opnum), 22H (11 levels * 2 modes), H (cost), H (graphic), H (power)
PORT_FMT = "<B30sB22HHH H"

def unpack_port(data):
    tup = struct.unpack(PORT_FMT, data)
    
    # Dekodowanie nazwy typu Pascal/String30 
    name_len = tup[0]
    raw_name = tup[1][:name_len]
    try:
        clean_name = raw_name.decode('ascii').strip()
    except:
        clean_name = "Unknown"

    port = {
        'name': clean_name,
        'opnum': tup[2], # Tryby strzelania
        'modes': {
            'mode1': list(tup[3:14]), # 11 poziomów mocy
            'mode2': list(tup[14:25])
        },
        'cost': tup[25],        # Koszt w sklepie
        'itemGraphic': tup[26], # Grafika w sklepie
        'powerUse': tup[27]     # Zużycie energii
    }
    return port

def resolve_path(path):
    """Zamienia ścieżkę na bezwzględną, obsługuje ścieżki względne do skryptu"""
    if not os.path.isabs(path):
        # Jeśli ścieżka jest względna, zwróć ją względem katalogu skryptu
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, path)
    return path

def toJSON(hdt_path, output_path):
    # Konwertuj ścieżki na bezwzględne
    hdt_path = resolve_path(hdt_path)
    output_path = resolve_path(output_path)
    
    print(f"Odczyt z: {hdt_path}")
    print(f"Zapis do: {output_path}")
    
    ports_data = {
        "weapon_ports": [],
        "metadata": {
            "total_ports": PORT_NUM + 1,
            "source_file": os.path.basename(hdt_path)
        }
    }

    try:
        with open(hdt_path, "rb") as f:
            # 1. Odczytaj offset danych i pomiń nagłówek
            data_offset = struct.unpack("<i", f.read(4))[0]
            f.seek(data_offset)
            f.read(7 * 2) # Pomiń zmienne WEAP_NUM, PORT_NUM itd.

            # 2. Przeskocz dane wzorców broni (te, które parsuje Twój pierwszy skrypt) 
            # Przesuwamy o (780+1) * 80 bajtów
            f.seek((WEAP_NUM + 1) * WEAPON_STRUCT_SIZE, 1)

            print(f"Parsowanie {PORT_NUM + 1} portów broni...")

            # 3. Czytaj struktury weaponPort 
            for i in range(PORT_NUM + 1):
                chunk = f.read(struct.calcsize(PORT_FMT))
                if not chunk: break
                
                port_data = unpack_port(chunk)
                
                # Tworzenie struktury JSON
                port_entry = {
                    "index": i,
                    "name": port_data['name'],
                    "stats": {
                        "cost": port_data['cost'],
                        "power_use": port_data['powerUse'],
                        "item_graphic": port_data['itemGraphic'],
                        "modes_count": port_data['opnum']
                    },
                    "firing_modes": {
                        "mode_1": port_data['modes']['mode1'],
                        "mode_2": port_data['modes']['mode2']
                    }
                }
                
                ports_data["weapon_ports"].append(port_entry)

        with open(output_path, "w") as outf:
            json.dump(ports_data, outf, indent=2)
        print("Gotowe!")

    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    # Domyślne wartości
    default_hdt_file = "tyrian.hdt"
    default_output_file = "weapon_ports.json"
    
    if len(sys.argv) == 1:
        # Tylko plik .hdt - użyj domyślnej nazwy wyjściowej
        hdt_file = sys.argv[1] if len(sys.argv) > 1 else default_hdt_file
        output_file = default_output_file
        print(f"Processing {hdt_file} -> {output_file}")
    elif len(sys.argv) == 2:
        # Plik .hdt i plik wyjściowy
        hdt_file = sys.argv[1]
        output_file = sys.argv[2]
        print(f"Processing {hdt_file} -> {output_file}")
    elif len(sys.argv) < 2:
        # Brak argumentów - użyj domyślnych wartości
        hdt_file = default_hdt_file
        output_file = default_output_file
        print(f"No arguments provided - using defaults: {default_hdt_file} -> {default_output_file}")
    else:
        print("Usage: python weapon_port.py <hdt_file> [output_file]")
        print(f"Example: python weapon_port.py {default_hdt_file} {default_output_file}")
        print(f"Default: {default_hdt_file} -> {default_output_file} if not specified")
    
    toJSON(hdt_file, output_file)