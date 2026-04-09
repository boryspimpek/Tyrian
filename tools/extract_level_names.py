#!/usr/bin/env python3
"""
Skrypt do wyciągania nazw poziomów z plików levels*.dat Tyriana.
"""

CRYPT_KEY = bytes([204, 129, 63, 255, 71, 19, 25, 62, 1, 99])


def decrypt_string(data: bytes) -> bytes:
    """Deszyfruje string używając algorytmu Tyriana."""
    if len(data) == 0:
        return b''
    
    result = bytearray(data)
    for i in range(len(result) - 1, -1, -1):
        result[i] ^= CRYPT_KEY[i % len(CRYPT_KEY)]
        if i > 0:
            result[i] ^= result[i - 1]
    
    return bytes(result)


def read_pascal_strings(filepath: str):
    """Czyta zaszyfrowane Pascal strings z pliku."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    pos = 0
    while pos < len(data):
        if pos + 1 > len(data):
            break
        
        length = data[pos]
        pos += 1
        
        if pos + length > len(data):
            break
        
        string_bytes = data[pos:pos + length]
        pos += length
        
        decrypted = decrypt_string(string_bytes)
        try:
            yield decrypted.decode('ascii', errors='replace')
        except:
            yield decrypted.decode('latin-1', errors='replace')


def extract_level_names(filepath: str):
    """Wyciąga nazwy poziomów z pliku levels*.dat."""
    level_names = []
    
    for s in read_pascal_strings(filepath):
        if ']L[' in s:
            parts = s.split()
            if len(parts) >= 4:
                level_name = parts[3]
                level_names.append(level_name)
    
    return level_names


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Użycie: python extract_level_names.py <plik_levels.dat>")
        print("Przykład: python extract_level_names.py levels1.dat")
        sys.exit(1)
    
    filepath = sys.argv[1]
    level_names = extract_level_names(filepath)
    
    print(f"Nazwy poziomów z {filepath}:")
    for name in level_names:
        print(name)
