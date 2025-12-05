#!/usr/bin/env python3
"""
Advanced MCC File Reader - Extracts detailed Minecraft chunk information
"""
import zlib
import nbtlib
from nbtlib import nbt
from pathlib import Path
import json
from collections import defaultdict

def read_and_decompress(filepath):
    """Read and decompress the MCC file"""
    with open(filepath, 'rb') as f:
        compressed_data = f.read()
    
    print(f"📦 Compressed size: {len(compressed_data):,} bytes")
    decompressed_data = zlib.decompress(compressed_data)
    print(f"📂 Decompressed size: {len(decompressed_data):,} bytes")
    
    return decompressed_data

def parse_nbt_chunk(data):
    """Parse NBT chunk data"""
    try:
        nbt_data = nbtlib.File.from_buffer(data)
        return nbt_data
    except Exception as e:
        print(f"⚠️  NBT parsing error: {e}")
        return None

def extract_detailed_info(nbt_data):
    """Extract detailed information from NBT data"""
    info = {
        'chunk_info': {},
        'blocks': defaultdict(int),
        'entities': [],
        'block_entities': [],
        'coordinates': set(),
        'players': [],
        'metadata': {}
    }
    
    def traverse(obj, path="", depth=0):
        """Recursively traverse NBT structure"""
        if depth > 20:  # Prevent infinite recursion
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Extract coordinates
                if key.lower() in ['x', 'y', 'z', 'pos', 'position']:
                    if isinstance(value, (int, float)):
                        info['coordinates'].add((key, value))
                
                # Extract entity information
                if key == 'id' and isinstance(value, str):
                    if 'minecraft:' in value:
                        info['blocks'][value] += 1
                
                # Extract player/owner information
                if key.lower() in ['owner', 'playername', 'name', 'customname']:
                    if isinstance(value, str) and value:
                        info['players'].append(value)
                
                # Extract spawn reason
                if key == 'Paper.SpawnReason' and isinstance(value, str):
                    info['metadata']['spawn_reason'] = value
                
                # Extract world info
                if key.lower() in ['worlduuidmost', 'worlduuidleast']:
                    info['metadata'][key] = str(value)
                
                # Extract data version
                if key == 'DataVersion':
                    info['metadata']['data_version'] = value
                
                traverse(value, current_path, depth + 1)
        
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                
                # Check if this is an entity
                if isinstance(item, dict):
                    if 'id' in item:
                        entity = {
                            'type': str(item.get('id', 'unknown')),
                            'pos': None,
                            'rotation': None,
                            'attributes': {}
                        }
                        
                        # Get position
                        if 'Pos' in item:
                            entity['pos'] = [float(x) for x in item['Pos']]
                        
                        # Get rotation
                        if 'Rotation' in item:
                            entity['rotation'] = [float(x) for x in item['Rotation']]
                        
                        # Get attributes
                        if 'attributes' in item:
                            for attr in item['attributes']:
                                if 'id' in attr and 'base' in attr:
                                    entity['attributes'][str(attr['id'])] = float(attr['base'])
                        
                        info['entities'].append(entity)
                
                traverse(item, current_path, depth + 1)
    
    traverse(nbt_data)
    return info

def format_coordinates(coords):
    """Format coordinates for display"""
    coord_dict = defaultdict(list)
    for key, value in coords:
        coord_dict[key].append(value)
    return coord_dict

def main():
    filepath = Path("c.2.-50.mcc")
    
    print("=" * 80)
    print(f"🔍 DETAILED MCC FILE ANALYSIS: {filepath.name}")
    print("=" * 80)
    print()
    
    # Read and decompress
    data = read_and_decompress(filepath)
    
    # Parse NBT
    print("\n📖 Parsing NBT structure...")
    nbt_data = parse_nbt_chunk(data)
    
    if nbt_data is None:
        print("❌ Could not parse NBT data")
        return
    
    # Extract information
    print("🔎 Extracting detailed information...")
    info = extract_detailed_info(nbt_data)
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 ANALYSIS RESULTS")
    print("=" * 80)
    
    # Metadata
    if info['metadata']:
        print("\n📝 METADATA:")
        for key, value in info['metadata'].items():
            print(f"  • {key}: {value}")
    
    # Coordinates
    if info['coordinates']:
        print(f"\n📍 COORDINATES ({len(info['coordinates'])} found):")
        coord_dict = format_coordinates(info['coordinates'])
        for coord_type, values in sorted(coord_dict.items()):
            print(f"  • {coord_type}: {values[:10]}" + (" ..." if len(values) > 10 else ""))
    
    # Entities
    if info['entities']:
        print(f"\n🐾 ENTITIES ({len(info['entities'])} found):")
        entity_types = defaultdict(int)
        for entity in info['entities']:
            entity_types[entity['type']] += 1
        
        for entity_type, count in sorted(entity_types.items(), key=lambda x: -x[1]):
            print(f"  • {entity_type}: {count}x")
        
        # Show first 5 entities with details
        print("\n  📋 Sample Entity Details (first 5):")
        for i, entity in enumerate(info['entities'][:5], 1):
            print(f"\n  [{i}] {entity['type']}")
            if entity['pos']:
                print(f"      Position: ({entity['pos'][0]:.1f}, {entity['pos'][1]:.1f}, {entity['pos'][2]:.1f})")
            if entity['rotation']:
                print(f"      Rotation: ({entity['rotation'][0]:.1f}°, {entity['rotation'][1]:.1f}°)")
            if entity['attributes']:
                print(f"      Attributes:")
                for attr_name, attr_value in entity['attributes'].items():
                    attr_short = attr_name.replace('minecraft:', '')
                    print(f"        - {attr_short}: {attr_value:.2f}")
    
    # Blocks
    if info['blocks']:
        print(f"\n🧱 BLOCK TYPES ({len(info['blocks'])} unique):")
        sorted_blocks = sorted(info['blocks'].items(), key=lambda x: -x[1])
        for block, count in sorted_blocks[:20]:
            print(f"  • {block}: {count}x")
        if len(sorted_blocks) > 20:
            print(f"  ... and {len(sorted_blocks) - 20} more")
    
    # Players
    if info['players']:
        print(f"\n👤 PLAYERS/OWNERS ({len(set(info['players']))} unique):")
        for player in sorted(set(info['players'])):
            print(f"  • {player}")
    
    # Save detailed JSON
    output = {
        'file': str(filepath),
        'metadata': info['metadata'],
        'entity_summary': {entity_type: count for entity_type, count in 
                          [(e['type'], 1) for e in info['entities']]},
        'entities': info['entities'][:50],  # First 50 entities
        'blocks': dict(sorted(info['blocks'].items(), key=lambda x: -x[1])[:100]),
        'coordinates': {k: v for k, v in format_coordinates(info['coordinates']).items()},
        'players': sorted(set(info['players']))
    }
    
    json_file = filepath.stem + "_detailed.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n💾 Detailed analysis saved to: {json_file}")
    
    # Save human-readable report
    report_file = filepath.stem + "_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("MCC FILE ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"File: {filepath}\n")
        f.write(f"Analysis Date: {Path(__file__).stat().st_mtime}\n\n")
        
        if info['metadata']:
            f.write("METADATA:\n")
            for key, value in info['metadata'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
        
        if info['entities']:
            f.write(f"ENTITIES ({len(info['entities'])} total):\n")
            entity_types = defaultdict(int)
            for entity in info['entities']:
                entity_types[entity['type']] += 1
            for entity_type, count in sorted(entity_types.items()):
                f.write(f"  {entity_type}: {count}x\n")
            f.write("\n")
            
            f.write("DETAILED ENTITY LIST:\n")
            for i, entity in enumerate(info['entities'], 1):
                f.write(f"\n[{i}] {entity['type']}\n")
                if entity['pos']:
                    f.write(f"    Position: ({entity['pos'][0]:.1f}, {entity['pos'][1]:.1f}, {entity['pos'][2]:.1f})\n")
                if entity['rotation']:
                    f.write(f"    Rotation: ({entity['rotation'][0]:.1f}°, {entity['rotation'][1]:.1f}°)\n")
                if entity['attributes']:
                    f.write(f"    Attributes:\n")
                    for attr_name, attr_value in entity['attributes'].items():
                        f.write(f"      - {attr_name}: {attr_value:.2f}\n")
    
    print(f"📄 Human-readable report saved to: {report_file}")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
