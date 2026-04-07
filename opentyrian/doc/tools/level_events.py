#!/usr/bin/env python3
"""
Level Event Extractor for Tyrian
Extracts enemy spawn sequences from .lvl binary files
"""

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

# Event types based on JE_eventSystem() analysis
EVENT_TYPES = {
    1: "starfield_speed",
    2: "scroll_speed", 
    3: "scroll_speed_preset",
    4: "stop_background",
    5: "load_enemy_shapes",
    6: "spawn_ground_enemy",      # Y=25
    7: "spawn_top_enemy",         # Y=50  
    8: "disable_stars",
    9: "enable_stars",
    10: "spawn_ground_enemy2",     # Y=75
    11: "end_level",
    12: "spawn_4x4_ground",
    13: "disable_enemies",
    14: "enable_enemies", 
    15: "spawn_sky_enemy",         # Y=0
    16: "show_text",
    17: "spawn_ground_bottom",
    18: "spawn_sky_bottom",
    19: "enemy_global_move",
    23: "spawn_sky_bottom2",
    32: "spawn_enemy_special",
    56: "spawn_ground2_bottom"
}

# Enemy spawn events that we want to extract
SPAWN_EVENTS = {6, 7, 10, 12, 15, 17, 18, 23, 32, 56}

def read_level_header(filename):
    """Read level file header and extract level offsets"""
    with open(filename, 'rb') as f:
        # Read level count
        lvl_num = struct.unpack('<H', f.read(2))[0]
        
        # Read level offsets (4 bytes each)
        lvl_pos = list(struct.unpack(f'<{lvl_num}i', f.read(4 * lvl_num)))
        
        # Current position is after all offsets
        lvl_pos.append(f.tell())
        
    return lvl_num, lvl_pos

def read_level_events(filename, level_offset):
    """Extract events from a specific level"""
    with open(filename, 'rb') as f:
        # Seek to level start
        f.seek(level_offset)
        
        # Read level header
        map_file = f.read(1).decode('ascii', errors='ignore')
        shape_file = f.read(1).decode('ascii', errors='ignore')
        
        map_x = struct.unpack('<H', f.read(2))[0]
        map_x2 = struct.unpack('<H', f.read(2))[0] 
        map_x3 = struct.unpack('<H', f.read(2))[0]
        
        # Read enemy data (skip for now)
        level_enemy_max = struct.unpack('<H', f.read(2))[0]
        f.seek(level_enemy_max * 2, 1)  # Skip levelEnemy array
        
        # Read events
        try:
            max_event = struct.unpack('<H', f.read(2))[0]
        except struct.error:
            print(f"Warning: Could not read max_event at offset {level_offset}")
            return [], {}
            
        events = []
        
        for i in range(max_event):
            event_data = f.read(11)  # Fixed size event structure (11 bytes)
            if len(event_data) < 11:
                break
                
            # Unpack event structure
            event = struct.unpack('<H B h h b b b B', event_data)
            
            event_record = {
                'eventtime': event[0],      # Distance/timer trigger
                'eventtype': event[1],      # Command ID
                'eventdat': event[2],       # Enemy ID or parameter 1
                'eventdat2': event[3],      # X position or parameter 2  
                'eventdat3': event[4],      # Y velocity or parameter 3
                'eventdat5': event[5],      # Y position or parameter 4
                'eventdat6': event[6],      # Fixed move Y or parameter 5
                'eventdat4': event[7]       # Link number or parameter 6
            }
            events.append(event_record)
            
        return events, {
            'map_file': map_file,
            'shape_file': shape_file,
            'map_x': map_x,
            'map_x2': map_x2, 
            'map_x3': map_x3,
            'level_enemy_max': level_enemy_max,
            'max_event': max_event
        }

def extract_spawn_events(events):
    """Extract only enemy spawn events with position data"""
    spawns = []
    
    for event in events:
        event_type = event['eventtype']
        
        if event_type not in SPAWN_EVENTS:
            continue
            
        # Determine enemy type and position
        spawn_data = {
            'dist': event['eventtime'],
            'raw_event': event_type,
            'enemy_id': event['eventdat'],
            'x': event['eventdat2'] if event['eventdat2'] != -99 else 160,  # Default center
            'y_vel': event['eventdat3'],
            'y_offset': event['eventdat5'],
            'link_num': event['eventdat4'],
            'fixed_move_y': event['eventdat6']
        }
        
        # Map event type to spawn position
        if event_type == 6:      # Ground Enemy
            spawn_data['type'] = 'ground'
            spawn_data['base_y'] = 25
        elif event_type == 7:    # Top Enemy  
            spawn_data['type'] = 'top'
            spawn_data['base_y'] = 50
        elif event_type == 10:   # Ground Enemy 2
            spawn_data['type'] = 'ground'
            spawn_data['base_y'] = 75
        elif event_type == 12:   # 4x4 Ground (multiple enemies)
            spawn_data['type'] = 'ground_4x4'
            spawn_data['base_y'] = 25  # Will be adjusted by eventdat6
        elif event_type == 15:   # Sky Enemy
            spawn_data['type'] = 'sky'
            spawn_data['base_y'] = 0
        elif event_type == 17:   # Ground Bottom
            spawn_data['type'] = 'ground_bottom'
            spawn_data['base_y'] = 25
        elif event_type == 18:   # Sky Bottom
            spawn_data['type'] = 'sky_bottom'
            spawn_data['base_y'] = 0
        elif event_type == 23:   # Sky Bottom 2
            spawn_data['type'] = 'sky_bottom'
            spawn_data['base_y'] = 50
        elif event_type == 32:   # Special Enemy
            spawn_data['type'] = 'special'
            spawn_data['base_y'] = 50
        elif event_type == 56:   # Ground2 Bottom
            spawn_data['type'] = 'ground_bottom'
            spawn_data['base_y'] = 75
        else:
            continue
            
        spawns.append(spawn_data)
        
    return spawns

def process_level_file(filename, level_num=1):
    """Process entire level file or specific level"""
    filename = resolve_path(filename)
    
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return
        
    # Read level header
    lvl_count, lvl_offsets = read_level_header(filename)
    print(f"Found {lvl_count} levels in {filename}")
    
    results = {}
    
    # Process specific level or all levels
    if level_num is not None:
        if 1 <= level_num <= lvl_count:
            level_indices = [level_num - 1]
        else:
            print(f"Error: Level {level_num} not found (max: {lvl_count})")
            return
    else:
        level_indices = range(lvl_count)
    
    for i in level_indices:
        try:
            offset = lvl_offsets[i]
            events, header = read_level_events(filename, offset)
            spawns = extract_spawn_events(events)
            
            level_key = f"level_{i+1}"
            results[level_key] = {
                'header': header,
                'total_events': len(events),
                'spawn_events': len(spawns),
                'spawns': spawns
            }
            
        except Exception as e:
            print(f"Error processing level {i+1}: {e}")
            continue
    
    return results

def main():
    # Domyślne wartości
    default_lvl_file = "tyrian1.lvl"
    default_level_num = 1
    
    if len(sys.argv) < 2:
        # Brak argumentów - użyj domyślnych wartości
        lvl_file = default_lvl_file
        level_num = default_level_num
        print(f"No arguments provided - using defaults: {default_lvl_file} level {default_level_num}")
    elif len(sys.argv) == 1:
        # Tylko plik .lvl - użyj domyślnego poziomu
        lvl_file = sys.argv[1]
        level_num = default_level_num
        print(f"Processing {lvl_file} with default level {default_level_num}")
    elif len(sys.argv) == 2:
        # Plik .lvl i numer poziomu
        lvl_file = sys.argv[1]
        level_num = int(sys.argv[2])
        print(f"Processing {lvl_file} with level {level_num}")
    else:
        print("Usage: python level_events.py <lvl_file> [level_number]")
        print(f"Example: python level_events.py {default_lvl_file} 1")
        print(f"Default: {default_lvl_file} level {default_level_num} if not specified")
        return
    
    results = process_level_file(lvl_file, level_num)
    
    if results:
        # Save to JSON
        output_file = resolve_path("events.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
