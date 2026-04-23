import struct
import wave
import os

# Sound names from sndmast.h
SOUND_NAMES = [
    "S_NONE",              # 0
    "S_WEAPON_1",          # 1
    "S_WEAPON_2",          # 2
    "S_ENEMY_HIT",         # 3
    "S_EXPLOSION_4",       # 4
    "S_WEAPON_5",          # 5
    "S_WEAPON_6",          # 6
    "S_WEAPON_7",          # 7
    "S_SELECT_EXPLOSION_8",# 8 (both S_SELECT and S_EXPLOSION_8 map to 8)
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
]

def extract_tyrian_sounds(snd_file, output_dir):
    """Extract all sounds from Tyrian .snd file to WAV format"""
    
    with open(snd_file, 'rb') as f:
        data = f.read()
    
    # Read header
    num_sounds = struct.unpack('<H', data[:2])[0]
    offsets = struct.unpack(f'<{num_sounds}I', data[2:2+4*num_sounds])
    
    print(f'Extracting {num_sounds} sounds from {snd_file}')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create index file
    index_path = os.path.join(output_dir, 'sound_index.txt')
    with open(index_path, 'w') as idx:
        idx.write("Tyrian Sound Effects Index\n")
        idx.write("===========================\n\n")
        idx.write(f"Total sounds: {num_sounds}\n")
        idx.write(f"Format: 8-bit signed PCM, mono, 11025 Hz\n\n")
    
    # Extract each sound
    for i in range(num_sounds):
        start = offsets[i]
        end = offsets[i+1] if i < num_sounds-1 else len(data)
        sound_data = data[start:end]
        
        # Convert to signed 8-bit (0x80 = 0)
        signed_data = bytes([(b - 128) & 0xFF for b in sound_data])
        
        # Create WAV file with descriptive name
        sound_name = SOUND_NAMES[i] if i < len(SOUND_NAMES) else f"S_UNKNOWN_{i}"
        output_path = os.path.join(output_dir, f'{i:03d}_{sound_name}.wav')
        with wave.open(output_path, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(1)  # 8-bit
            wav.setframerate(11025)  # Tyrian uses 11025 Hz
            wav.writeframes(signed_data)
        
        # Add to index
        with open(index_path, 'a') as idx:
            duration_ms = len(sound_data) * 1000 // 11025
            idx.write(f"{i:3d}: {sound_name:25s} - {len(sound_data):6d} bytes ({duration_ms:4d} ms)\n")
        
        print(f'  Sound {i:3d}: {sound_name:25s} - {len(sound_data):6d} bytes -> {output_path}')
    
    print(f'\nAll sounds extracted to {output_dir}')
    print(f'Sound index saved to {index_path}')

if __name__ == '__main__':
    snd_file = r'c:\Users\borys\projekty\Tyrian\tyrian21\tyrian.snd'
    output_dir = r'c:\Users\borys\projekty\Tyrian\extracted_sounds'
    extract_tyrian_sounds(snd_file, output_dir)
