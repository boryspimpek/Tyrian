import struct
import os
import json

def resolve_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, filename)

def extract_sidekicks_complete():
    hdt_path = resolve_path("tyrian.hdt")
    
    # Stałe strukturalne
    WEAP_NUM, PORT_NUM, SPECIAL_NUM, POWER_NUM, SHIP_NUM, OPTION_NUM = 780, 42, 46, 6, 13, 30
    SIZES = {'weap': 80, 'port': 82, 'spec': 37, 'pwr': 37, 'ship': 41}
    
    # B(len), 30s(name), B(pwr), H(gr), H(cost), B(tr), B(opt), b(spd), B(ani), 20H(sprites), B(wport), H(wpnum), B(ammo), B(stop), B(icon)
    OPTION_FMT = "<B30sBHH BBB B 20H B H B B B"

    try:
        with open(hdt_path, "rb") as f:
            data_loc = struct.unpack("<i", f.read(4))[0]
            f.seek(data_loc + 14) # Skok do danych + pominięcie nagłówka

            # Precyzyjny skok do sekcji Options
            f.seek(((WEAP_NUM+1)*SIZES['weap']) + ((PORT_NUM+1)*SIZES['port']) + 
                   ((SPECIAL_NUM+1)*SIZES['spec']) + ((POWER_NUM+1)*SIZES['pwr']) + 
                   ((SHIP_NUM+1)*SIZES['ship']), 1)

            results = []
            for i in range(OPTION_NUM + 1):
                chunk = f.read(struct.calcsize(OPTION_FMT))
                if not chunk: break
                r = struct.unpack(OPTION_FMT, chunk)
                
                results.append({
                    "index": i,
                    "name": r[1][:r[0]].decode('ascii', errors='ignore').strip(),
                    "charge_stages": r[2],
                    "shop_graphic": r[3],
                    "cost": r[4],
                    "movement_type": r[5],
                    "animation_mode": r[6],
                    "rotation_speed": r[7],
                    "animation_frames_count": r[8],
                    "sprites": list(r[9:29]),
                    "weapon_port_index": r[29],
                    "bullet_pattern_id": r[30],
                    "ammo": r[31],
                    "icon_id": r[33]
                })

        with open(resolve_path("sidekicks.json"), "w", encoding="utf-8") as out:
            json.dump(results, out, indent=2, ensure_ascii=False)
        print(f"Wyciągnięto {len(results)} sidekicków.")
    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    extract_sidekicks_complete()