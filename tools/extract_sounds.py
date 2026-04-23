import struct
import wave
import os

# Sound names from sndmast.h (index = sound ID used in weapon.json)
# ID 0 = S_NONE = silence, not stored in the file
SOUND_NAMES = [
    None,                  # 0 - S_NONE (not in file)
    "S_WEAPON_1",          # 1
    "S_WEAPON_2",          # 2
    "S_ENEMY_HIT",         # 3
    "S_EXPLOSION_4",       # 4
    "S_WEAPON_5",          # 5
    "S_WEAPON_6",          # 6
    "S_WEAPON_7",          # 7
    "S_SELECT_EXPLOSION_8",# 8  (S_SELECT and S_EXPLOSION_8 are both 8)
    "S_EXPLOSION_9",       # 9
    "S_WEAPON_10",         # 10
    "S_EXPLOSION_11",      # 11
    "S_EXPLOSION_12",      # 12
    "S_WEAPON_13",         # 13
    "S_WEAPON_14",         # 14
    "S_WEAPON_15",         # 15
    "S_SPRING",            # 16
    "S_WARNING",           # 17
    "S_ITEM",              # 18
    "S_HULL_HIT",          # 19
    "S_MACHINE_GUN",       # 20
    "S_SOUL_OF_ZINGLON",   # 21
    "S_EXPLOSION_22",      # 22
    "S_CLINK",             # 23
    "S_CLICK",             # 24
    "S_WEAPON_25",         # 25
    "S_WEAPON_26",         # 26
    "S_SHIELD_HIT",        # 27
    "S_CURSOR",            # 28
    "S_POWERUP",           # 29
    "V_CLEARED_PLATFORM",  # 30 - "Cleared enemy platform."
    "V_BOSS",              # 31 - "Large enemy approaching."
    "V_ENEMIES",           # 32 - "Enemies ahead."
    "V_GOOD_LUCK",         # 33 - "Good luck."
    "V_LEVEL_END",         # 34 - "Level completed."
    "V_DANGER",            # 35 - "Danger."
    "V_SPIKES",            # 36 - "Warning: spikes ahead."
    "V_DATA_CUBE",         # 37 - "Data acquired."
    "V_ACCELERATE",        # 38 - "Unexplained speed increase."
]

def extract_tyrian_sounds(snd_file, output_dir):
    """Extract all sounds from Tyrian .snd file to WAV format"""

    with open(snd_file, "rb") as f:
        data = f.read()

    # Read header
    num_sounds = struct.unpack("<H", data[:2])[0]
    offsets = struct.unpack(f"<{num_sounds}I", data[2:2+4*num_sounds])

    print(f"Extracting {num_sounds} sounds from {snd_file}")

    os.makedirs(output_dir, exist_ok=True)

    index_path = os.path.join(output_dir, "sound_index.txt")
    with open(index_path, "w") as idx:
        idx.write("Tyrian Sound Effects Index\n")
        idx.write("===========================\n\n")
        idx.write(f"Total sounds: {num_sounds}\n")
        idx.write("Format: 8-bit signed PCM, mono, 11025 Hz\n\n")
        idx.write("Note: file entry i=0 -> sound ID 1 (S_NONE/ID=0 is silence, not stored)\n\n")

    for i in range(num_sounds):
        start = offsets[i]
        end = offsets[i+1] if i < num_sounds-1 else len(data)
        sound_data = data[start:end]

        # Convert from unsigned (0x80=silence) to signed 8-bit
        signed_data = bytes([(b - 128) & 0xFF for b in sound_data])

        # File entry i corresponds to sound ID i+1
        sound_id = i + 1
        sound_name = SOUND_NAMES[sound_id] if sound_id < len(SOUND_NAMES) else f"S_UNKNOWN_{sound_id}"

        output_path = os.path.join(output_dir, f"{sound_id:03d}_{sound_name}.wav")
        with wave.open(output_path, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(1)
            wav.setframerate(11025)
            wav.writeframes(signed_data)

        with open(index_path, "a") as idx:
            duration_ms = len(sound_data) * 1000 // 11025
            idx.write(f"{sound_id:3d}: {sound_name:25s} - {len(sound_data):6d} bytes ({duration_ms:4d} ms)\n")

        print(f"  Sound {sound_id:3d}: {sound_name:25s} - {len(sound_data):6d} bytes -> {output_path}")

    print(f"\nAll sounds extracted to {output_dir}")
    print(f"Sound index saved to {index_path}")

if __name__ == "__main__":
    snd_file = r"c:\Users\borys\projekty\Tyrian\tyrian21\tyrian.snd"
    output_dir = r"c:\Users\borys\projekty\Galaxid\data\extracted_sounds"
    extract_tyrian_sounds(snd_file, output_dir)
