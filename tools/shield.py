import struct
import os
import json

def resolve_path(path):
    """Zamienia ścieżkę na bezwzględną, obsługuje ścieżki względne do skryptu"""
    if not os.path.isabs(path):
        # Jeśli ścieżka jest względna, zwróć ją względem katalogu skryptu
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, path)
    return path

# Definicje na podstawie tyrian.hdt.txt
WEAP_NUM = 780
PORT_NUM = 42
SPECIAL_NUM = 46
POWER_NUM = 6
SHIP_NUM = 13
OPTION_NUM = 30
SHIELD_NUM = 10  # Razem 11 rekordów (0-10) 

# Rozmiary struktur w bajtach
WEAPON_SIZE = 80      # 0x50 [cite: 2]
PORT_SIZE = 1 + 30 + 1 + (22 * 2) + 2 + 2 + 2  # 82 bajty [cite: 4, 8]
SPECIAL_SIZE = 1 + 30 + 2 + 1 + 1 + 2          # 37 bajtów
POWER_SIZE = 1 + 30 + 2 + 1 + 1 + 2            # 37 bajtów [cite: 9]
SHIP_SIZE = 1 + 30 + 2 + 2 + 1 + 1 + 1 + 2 + 1 # 41 bajtów
OPTION_SIZE = 1 + 30 + 1 + 2 + 2 + 1 + 1 + 1 + 1 + (20 * 2) + 1 + 2 + 1 + 1 + 1 # 86 bajtów [cite: 10]

# Struktura tarczy: str_len(1), name(30), tpwr(1), mpwr(1), graphic(2), cost(2) 
SHIELD_FMT = "<B30sBBHH" 

def extract_all_shields():
    file_path = resolve_path("tyrian.hdt")
    output_path = resolve_path("shields.json")
    
    if not os.path.exists(file_path):
        print("Błąd: Brak pliku tyrian.hdt")
        return

    print(f"Odczyt z: {file_path}")
    print(f"Zapis do: {output_path}")

    with open(file_path, "rb") as f:
        # 1. Pobierz offset początku danych [cite: 1]
        data_loc = struct.unpack("<i", f.read(4))[0]
        f.seek(data_loc)
        
        # 2. Pomiń nagłówek (7 zmiennych po 2 bajty każda) [cite: 1]
        f.read(14)

        # 3. Oblicz skok do sekcji tarcz (pomijamy wszystko przed nimi)
        offset_to_shields = (
            ((WEAP_NUM + 1) * WEAPON_SIZE) +
            ((PORT_NUM + 1) * PORT_SIZE) +
            ((SPECIAL_NUM + 1) * SPECIAL_SIZE) +
            ((POWER_NUM + 1) * POWER_SIZE) +
            ((SHIP_NUM + 1) * SHIP_SIZE) +
            ((OPTION_NUM + 1) * OPTION_SIZE)
        )
        
        f.seek(offset_to_shields, 1) # Przesunięcie relatywne

        print(f"{'NR':<3} | {'NAZWA TARCZY':<30} | {'TPWR':<5} | {'MPWR':<5} | {'KOSZT'}")
        print("-" * 65)

        shields_data = []
        for i in range(SHIELD_NUM + 1):
            chunk = f.read(struct.calcsize(SHIELD_FMT))
            if not chunk: break
            
            res = struct.unpack(SHIELD_FMT, chunk)
            
            # Dekodowanie nazwy Pascal 
            name_len = res[0]
            name = res[1][:name_len].decode('ascii', errors='ignore').strip()
            
            tpwr = res[2] # Generator power needed 
            mpwr = res[3] # Amount of protection 
            cost = res[5] # Cost in shop 

            print(f"{i:<3} | {name:<30} | {tpwr:<5} | {mpwr:<5} | {cost}")
            
            shields_data.append({
                "index": i,
                "name": name,
                "generator_needed": tpwr,
                "protection": mpwr,
                "cost": cost
            })

    # Zapis do JSON
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(shields_data, out, indent=2)
    print(f"\nZapisano {len(shields_data)} rekordów.")

if __name__ == "__main__":
    extract_all_shields()