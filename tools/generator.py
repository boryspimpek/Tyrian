import struct
import os
import json

def resolve_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, filename)

def extract_generators():
    hdt_path = resolve_path("tyrian.hdt")
    output_path = resolve_path("generators.json")

    # Stałe strukturalne
    WEAP_NUM, PORT_NUM, SPECIAL_NUM, POWER_NUM = 780, 42, 46, 6
    SIZES = {'weap': 80, 'port': 82, 'spec': 37, 'pwr': 37}

    # Format struktury generatora: str_len(1), name(30), itemGraphic(2), power(1 signed), speed(1), cost(2)
    POWER_FMT = "<B30sHbBH"

    try:
        with open(hdt_path, "rb") as f:
            data_loc = struct.unpack("<i", f.read(4))[0]
            f.seek(data_loc + 14) # Skok do danych + pominięcie nagłówka

            # Oblicz offset do sekcji generatorów
            offset = (((WEAP_NUM + 1) * SIZES['weap']) +
                      ((PORT_NUM + 1) * SIZES['port']) +
                      ((SPECIAL_NUM + 1) * SIZES['spec']))
            f.seek(offset, 1)

            generators_data = []
            for i in range(POWER_NUM + 1):
                chunk = f.read(struct.calcsize(POWER_FMT))
                if not chunk: break

                r = struct.unpack(POWER_FMT, chunk)

                # Dekodowanie nazwy Pascal
                name_len = r[0]
                name = r[1][:name_len].decode('ascii', errors='ignore').strip()

                generators_data.append({
                    "index": i,
                    "name": name,
                    "stats": {
                        "item_graphic": r[2],
                        "power": r[3],  # Szybkość regeneracji (signed byte)
                        "speed": r[4],  # Nieużywane
                        "cost": r[5]
                    }
                })

        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(generators_data, out, indent=2, ensure_ascii=False)

        print(f"Wyciągnięto {len(generators_data)} generatorów.")
        for gen in generators_data:
            print(f"  {gen['index']}: {gen['name']} (power={gen['stats']['power']}, cost={gen['stats']['cost']})")

    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    extract_generators()
