import os
import struct
import json

def tyrian_master_link_decoder():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "tyrian.shp")
    
    if not os.path.exists(file_path):
        print(f"Błąd: Nie znaleziono pliku TYRIAN.SHP")
        return

    with open(file_path, "rb") as f:
        f.seek(2) # Pomijamy nagłówek 'num_records'
        # Czytamy pierwsze 150 linków (600 bajtów)
        raw_data = f.read(600)

    movement_data = []

    print(f"{'ID':<4} | {'X':<4} | {'Y':<4} | {'TIME':<4} | {'FLAG':<4} | {'TYP I INTERPRETACJA'}")
    print("-" * 85)

    for i in range(150):
        start = i * 4
        chunk = raw_data[start : start + 4]
        if len(chunk) < 4: break
        
        # Interpretacja jako signed char (bajt ze znakiem -128 do 127)
        x, y, t, f = struct.unpack('bbbb', chunk)
        

        print(f"{i:<2} | {x:<4} | {y:<4} | {t:<4} | {f:<4}")
        
        # Zbieranie danych do zapisu
        movement_data.append({
            "id": i,
            "x": x,
            "y": y,
            "time": t,
            "flag": f,
        })
    
    # Zapis do pliku JSON
    output_file = os.path.join(script_dir, "enemy_movement.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(movement_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDane zapisane do pliku: {output_file}")
    return movement_data

if __name__ == "__main__":
    tyrian_master_link_decoder()
