#!/usr/bin/env python3
"""
MCC File Reader - Extracts information from .mcc files
"""
import zlib
import struct
import json
from pathlib import Path

def read_mcc_file(filepath):
    """Read and parse an MCC file"""
    with open(filepath, 'rb') as f:
        compressed_data = f.read()
    
    print(f"[*] File size: {len(compressed_data)} bytes")
    print(f"[*] File type: zlib compressed data")
    
    # Decompress the data
    try:
        decompressed_data = zlib.decompress(compressed_data)
        print(f"[*] Decompressed size: {len(decompressed_data)} bytes")
    except Exception as e:
        print(f"[!] Error decompressing: {e}")
        return None
    
    return decompressed_data

def parse_nbt_data(data):
    """Parse NBT (Named Binary Tag) format used in Minecraft"""
    results = {
        'file_info': {},
        'coordinates': [],
        'blocks': [],
        'entities': [],
        'metadata': {}
    }
    
    pos = 0
    try:
        # Try to find common NBT patterns
        data_str = data.decode('latin-1', errors='ignore')
        
        # Look for coordinate patterns (common in Minecraft region files)
        import re
        
        # Search for x, y, z coordinate patterns
        coord_patterns = [
            r'x["\']?\s*[:=]\s*(-?\d+)',
            r'y["\']?\s*[:=]\s*(-?\d+)',
            r'z["\']?\s*[:=]\s*(-?\d+)',
            r'Pos.*?(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)',
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, data_str, re.IGNORECASE)
            if matches:
                results['coordinates'].extend(matches)
        
        # Look for player/entity names
        name_patterns = [
            r'name["\']?\s*[:=]\s*["\']([^"\']+)',
            r'CustomName["\']?\s*[:=]\s*["\']([^"\']+)',
            r'Owner["\']?\s*[:=]\s*["\']([^"\']+)',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, data_str, re.IGNORECASE)
            if matches:
                results['entities'].extend(matches)
        
        # Look for block types
        block_pattern = r'id["\']?\s*[:=]\s*["\']minecraft:([^"\']+)'
        blocks = re.findall(block_pattern, data_str, re.IGNORECASE)
        results['blocks'] = list(set(blocks))[:50]  # Limit to 50 unique blocks
        
        # Look for timestamps
        time_pattern = r'(?:time|timestamp|date)["\']?\s*[:=]\s*(\d+)'
        times = re.findall(time_pattern, data_str, re.IGNORECASE)
        if times:
            results['metadata']['timestamps'] = times[:10]
        
        # Look for UUIDs (player/entity identifiers)
        uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
        uuids = re.findall(uuid_pattern, data_str)
        if uuids:
            results['metadata']['uuids'] = list(set(uuids))
        
    except Exception as e:
        print(f"[!] Error parsing NBT data: {e}")
    
    return results

def analyze_binary_structure(data):
    """Analyze the binary structure of the data"""
    print("\n" + "="*80)
    print("BINARY STRUCTURE ANALYSIS")
    print("="*80)
    
    # Check for magic numbers or headers
    if len(data) >= 4:
        header = data[:4]
        print(f"Header (first 4 bytes): {header.hex()} = {header}")
        
        # Check for common format signatures
        if header[:2] == b'\x0a\x00':
            print("  -> Possible NBT format (TAG_Compound)")
        elif header == b'RIFF':
            print("  -> RIFF format")
        elif header == b'PK\x03\x04':
            print("  -> ZIP format")
    
    # Look for repeating patterns
    print(f"\nData statistics:")
    print(f"  - Total size: {len(data)} bytes")
    print(f"  - Null bytes: {data.count(0)}")
    print(f"  - Printable characters: {sum(1 for b in data if 32 <= b <= 126)}")
    
    # Try to find readable strings (minimum 4 characters)
    strings = []
    current_string = []
    for byte in data:
        if 32 <= byte <= 126:  # Printable ASCII
            current_string.append(chr(byte))
        else:
            if len(current_string) >= 4:
                strings.append(''.join(current_string))
            current_string = []
    
    if current_string and len(current_string) >= 4:
        strings.append(''.join(current_string))
    
    if strings:
        print(f"\nFound {len(strings)} readable strings")
        print("Sample strings (first 30):")
        for s in strings[:30]:
            print(f"  - {s}")
    
    return strings

def extract_minecraft_info(data):
    """Extract Minecraft-specific information"""
    print("\n" + "="*80)
    print("MINECRAFT DATA EXTRACTION")
    print("="*80)
    
    results = parse_nbt_data(data)
    
    print(f"\nCoordinates found: {len(results['coordinates'])}")
    if results['coordinates']:
        print("Sample coordinates (first 20):")
        for coord in results['coordinates'][:20]:
            print(f"  {coord}")
    
    print(f"\nEntities/Names found: {len(results['entities'])}")
    if results['entities']:
        unique_entities = list(set(results['entities']))[:20]
        for entity in unique_entities:
            print(f"  - {entity}")
    
    print(f"\nBlock types found: {len(results['blocks'])}")
    if results['blocks']:
        for block in results['blocks'][:30]:
            print(f"  - minecraft:{block}")
    
    if results['metadata'].get('uuids'):
        print(f"\nUUIDs found: {len(results['metadata']['uuids'])}")
        for uuid in results['metadata']['uuids'][:10]:
            print(f"  - {uuid}")
    
    if results['metadata'].get('timestamps'):
        print(f"\nTimestamps found: {len(results['metadata']['timestamps'])}")
        for ts in results['metadata']['timestamps'][:10]:
            print(f"  - {ts}")
    
    return results

def main():
    filepath = Path("c.2.-50.mcc")
    
    print("="*80)
    print(f"MCC FILE READER - Analyzing: {filepath}")
    print("="*80)
    
    if not filepath.exists():
        print(f"[!] File not found: {filepath}")
        return
    
    # Read and decompress
    data = read_mcc_file(filepath)
    if data is None:
        return
    
    # Analyze binary structure
    strings = analyze_binary_structure(data)
    
    # Extract Minecraft-specific information
    minecraft_info = extract_minecraft_info(data)
    
    # Save raw decompressed data for inspection
    output_file = filepath.stem + "_decompressed.dat"
    with open(output_file, 'wb') as f:
        f.write(data)
    print(f"\n[*] Raw decompressed data saved to: {output_file}")
    
    # Save results to JSON
    json_output = filepath.stem + "_analysis.json"
    with open(json_output, 'w') as f:
        json.dump({
            'file': str(filepath),
            'compressed_size': len(open(filepath, 'rb').read()),
            'decompressed_size': len(data),
            'strings': strings[:100],  # Limit to 100 strings
            'minecraft_data': {
                'coordinates': [str(c) for c in minecraft_info['coordinates'][:100]],
                'entities': list(set(minecraft_info['entities']))[:50],
                'blocks': minecraft_info['blocks'][:50],
                'metadata': minecraft_info['metadata']
            }
        }, f, indent=2)
    print(f"[*] Analysis results saved to: {json_output}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
