import struct
import os
import json

def resolve_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, filename)

def extract_ships_final_victory():
    hdt_path = resolve_path("tyrian.hdt")
    output_path = resolve_path("ships.json")

    # Stałe Episode 1
    WEAP_NUM, PORT_NUM, SPECIAL_NUM, POWER_NUM, SHIP_NUM = 780, 42, 46, 6, 13
    SIZES = {'weap': 80, 'port': 82, 'spec': 37, 'pwr': 37}

    SHIP_FMT = "<B30s H H B b B H B"
    # 1+30 + 2 + 2 + 1 + 1 + 1 + 2 + 1 = 41 bajtów

    try:
        with open(hdt_path, "rb") as f:
            data_loc = struct.unpack("<i", f.read(4))[0]
            f.seek(data_loc + 14)
            offset = (((WEAP_NUM + 1) * SIZES['weap']) +
                      ((PORT_NUM + 1) * SIZES['port']) +
                      ((SPECIAL_NUM + 1) * SIZES['spec']) +
                      ((POWER_NUM + 1) * SIZES['pwr']))
            f.seek(offset, 1)

            ships_data = []
            for i in range(SHIP_NUM + 1):
                chunk = f.read(41)
                if not chunk: break
                r = struct.unpack(SHIP_FMT, chunk)
                
                name = r[1][:r[0]].decode('ascii', errors='ignore').strip()

                ships_data.append({
                    "index": i,
                    "name": name,
                    "stats": {
                        "ship_graphic": r[2],    # indeks sprite'a w spriteSheet9
                        "item_graphic": r[3],    # indeks sprite'a w menu przedmiotów
                        "ani": r[4],             # typ animacji (0=szeroki, 1=wąski)
                        "speed": r[5],           # modyfikator prędkości (signed)
                        "armor": r[6],           # punkty wytrzymałości kadłuba (max 28 w grze)
                        "cost": r[7],            # cena w sklepie
                        "big_ship_graphic": r[8] # indeks dużego sprite'a w menu
                    },
                })

        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(ships_data, out, indent=2, ensure_ascii=False)
        
        print("Zwycięstwo! Statki wyeksportowane poprawnie.")

    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    extract_ships_final_victory()