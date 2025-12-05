#!/usr/bin/env python3
"""
Complete MCC File Reader - Extracts all information from Minecraft chunk files
"""
import zlib
import struct
import json
from pathlib import Path
from collections import defaultdict
from io import BytesIO

class NBTReader:
    """NBT (Named Binary Tag) format reader"""
    
    TAG_End = 0
    TAG_Byte = 1
    TAG_Short = 2
    TAG_Int = 3
    TAG_Long = 4
    TAG_Float = 5
    TAG_Double = 6
    TAG_Byte_Array = 7
    TAG_String = 8
    TAG_List = 9
    TAG_Compound = 10
    TAG_Int_Array = 11
    TAG_Long_Array = 12
    
    def __init__(self, data):
        self.stream = BytesIO(data)
    
    def read_byte(self):
        return struct.unpack('>b', self.stream.read(1))[0]
    
    def read_ubyte(self):
        return struct.unpack('>B', self.stream.read(1))[0]
    
    def read_short(self):
        return struct.unpack('>h', self.stream.read(2))[0]
    
    def read_int(self):
        return struct.unpack('>i', self.stream.read(4))[0]
    
    def read_long(self):
        return struct.unpack('>q', self.stream.read(8))[0]
    
    def read_float(self):
        return struct.unpack('>f', self.stream.read(4))[0]
    
    def read_double(self):
        return struct.unpack('>d', self.stream.read(8))[0]
    
    def read_string(self):
        length = struct.unpack('>H', self.stream.read(2))[0]
        return self.stream.read(length).decode('utf-8', errors='replace')
    
    def read_tag(self, tag_type):
        """Read a tag based on its type"""
        if tag_type == self.TAG_End:
            return None
        elif tag_type == self.TAG_Byte:
            return self.read_byte()
        elif tag_type == self.TAG_Short:
            return self.read_short()
        elif tag_type == self.TAG_Int:
            return self.read_int()
        elif tag_type == self.TAG_Long:
            return self.read_long()
        elif tag_type == self.TAG_Float:
            return self.read_float()
        elif tag_type == self.TAG_Double:
            return self.read_double()
        elif tag_type == self.TAG_Byte_Array:
            length = self.read_int()
            return [self.read_byte() for _ in range(length)]
        elif tag_type == self.TAG_String:
            return self.read_string()
        elif tag_type == self.TAG_List:
            return self.read_list()
        elif tag_type == self.TAG_Compound:
            return self.read_compound()
        elif tag_type == self.TAG_Int_Array:
            length = self.read_int()
            return [self.read_int() for _ in range(length)]
        elif tag_type == self.TAG_Long_Array:
            length = self.read_int()
            return [self.read_long() for _ in range(length)]
        else:
            raise ValueError(f"Unknown tag type: {tag_type}")
    
    def read_list(self):
        """Read a TAG_List"""
        tag_type = self.read_ubyte()
        length = self.read_int()
        return [self.read_tag(tag_type) for _ in range(length)]
    
    def read_compound(self):
        """Read a TAG_Compound"""
        result = {}
        while True:
            tag_type = self.read_ubyte()
            if tag_type == self.TAG_End:
                break
            name = self.read_string()
            result[name] = self.read_tag(tag_type)
        return result
    
    def read_root(self):
        """Read the root NBT structure"""
        tag_type = self.read_ubyte()
        if tag_type == self.TAG_End:
            return None
        name = self.read_string()
        data = self.read_tag(tag_type)
        return {name: data}

def analyze_mcc_file(filepath):
    """Analyze the MCC file and extract all information"""
    
    print("=" * 80)
    print(f"🔍 MCC FILE ANALYSIS: {filepath.name}")
    print("=" * 80)
    print()
    
    # Read and decompress
    with open(filepath, 'rb') as f:
        compressed_data = f.read()
    
    print(f"📦 Compressed size: {len(compressed_data):,} bytes")
    
    try:
        decompressed_data = zlib.decompress(compressed_data)
        print(f"📂 Decompressed size: {len(decompressed_data):,} bytes")
    except Exception as e:
        print(f"❌ Decompression error: {e}")
        return
    
    # Parse NBT
    print("\n📖 Parsing NBT structure...")
    try:
        reader = NBTReader(decompressed_data)
        nbt_data = reader.read_root()
    except Exception as e:
        print(f"⚠️  NBT parsing error: {e}")
        print("   Trying alternative parsing...")
        nbt_data = None
    
    if not nbt_data:
        print("❌ Could not parse NBT data")
        return
    
    # Extract information
    print("🔎 Extracting information...\n")
    
    info = {
        'entities': [],
        'blocks': defaultdict(int),
        'coordinates': [],
        'metadata': {},
        'players': set(),
        'chunk_info': {}
    }
    
    def extract_info(obj, path=""):
        """Recursively extract information"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Chunk position
                if key == "Position":
                    info['chunk_info']['position'] = value
                
                # Data version
                if key == "DataVersion":
                    info['metadata']['data_version'] = value
                
                # Entities
                if key == "Entities" and isinstance(value, list):
                    for entity in value:
                        if isinstance(entity, dict):
                            entity_info = {
                                'id': entity.get('id', 'unknown'),
                                'pos': entity.get('Pos'),
                                'rotation': entity.get('Rotation'),
                                'motion': entity.get('Motion'),
                                'on_ground': entity.get('OnGround'),
                                'spawn_reason': entity.get('Paper.SpawnReason'),
                                'attributes': {}
                            }
                            
                            # Extract attributes
                            if 'attributes' in entity and isinstance(entity['attributes'], list):
                                for attr in entity['attributes']:
                                    if isinstance(attr, dict) and 'id' in attr:
                                        entity_info['attributes'][attr['id']] = attr.get('base')
                            
                            info['entities'].append(entity_info)
                
                # Block entities
                if key == "block_entities" and isinstance(value, list):
                    for block_entity in value:
                        if isinstance(block_entity, dict) and 'id' in block_entity:
                            info['blocks'][block_entity['id']] += 1
                
                # Sections (blocks)
                if key == "sections" and isinstance(value, list):
                    for section in value:
                        if isinstance(section, dict) and 'block_states' in section:
                            block_states = section['block_states']
                            if isinstance(block_states, dict) and 'palette' in block_states:
                                for block in block_states['palette']:
                                    if isinstance(block, dict) and 'Name' in block:
                                        info['blocks'][block['Name']] += 1
                
                extract_info(value, current_path)
        
        elif isinstance(obj, list):
            for item in obj:
                extract_info(item, path)
    
    extract_info(nbt_data)
    
    # Display results
    print("=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    
    # Metadata
    if info['metadata']:
        print("\n📝 METADATA:")
        for key, value in info['metadata'].items():
            print(f"  • {key}: {value}")
    
    # Chunk info
    if info['chunk_info']:
        print("\n🗺️  CHUNK INFORMATION:")
        for key, value in info['chunk_info'].items():
            print(f"  • {key}: {value}")
    
    # Entities
    if info['entities']:
        print(f"\n🐾 ENTITIES ({len(info['entities'])} found):")
        
        # Count by type
        entity_counts = defaultdict(int)
        for entity in info['entities']:
            entity_counts[entity['id']] += 1
        
        for entity_type, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
            print(f"  • {entity_type}: {count}x")
        
        # Show details for first 10 entities
        print("\n  📋 Entity Details (showing first 10):")
        for i, entity in enumerate(info['entities'][:10], 1):
            print(f"\n  [{i}] {entity['id']}")
            
            if entity['pos']:
                x, y, z = entity['pos']
                print(f"      📍 Position: ({x:.2f}, {y:.2f}, {z:.2f})")
            
            if entity['rotation']:
                yaw, pitch = entity['rotation']
                print(f"      🧭 Rotation: Yaw={yaw:.1f}°, Pitch={pitch:.1f}°")
            
            if entity['motion']:
                mx, my, mz = entity['motion']
                print(f"      💨 Motion: ({mx:.3f}, {my:.3f}, {mz:.3f})")
            
            if entity['on_ground'] is not None:
                print(f"      🌍 On Ground: {entity['on_ground']}")
            
            if entity['spawn_reason']:
                print(f"      🎯 Spawn Reason: {entity['spawn_reason']}")
            
            if entity['attributes']:
                print(f"      ⚡ Attributes:")
                for attr_name, attr_value in entity['attributes'].items():
                    attr_short = attr_name.replace('minecraft:', '')
                    if isinstance(attr_value, (int, float)):
                        print(f"         - {attr_short}: {attr_value:.2f}")
                    else:
                        print(f"         - {attr_short}: {attr_value}")
    
    # Blocks
    if info['blocks']:
        print(f"\n🧱 BLOCKS ({len(info['blocks'])} unique types, {sum(info['blocks'].values())} total):")
        sorted_blocks = sorted(info['blocks'].items(), key=lambda x: -x[1])
        for block_type, count in sorted_blocks[:25]:
            block_short = block_type.replace('minecraft:', '')
            print(f"  • {block_short}: {count}x")
        if len(sorted_blocks) > 25:
            remaining = sum(count for _, count in sorted_blocks[25:])
            print(f"  ... and {len(sorted_blocks) - 25} more types ({remaining:,} blocks)")
    
    # Save results
    print("\n💾 Saving results...")
    
    # JSON output
    json_output = {
        'file': str(filepath),
        'metadata': info['metadata'],
        'chunk_info': info['chunk_info'],
        'entity_count': len(info['entities']),
        'entity_types': {k: v for k, v in entity_counts.items()},
        'entities': info['entities'],
        'block_count': sum(info['blocks'].values()),
        'unique_blocks': len(info['blocks']),
        'blocks': dict(sorted(info['blocks'].items(), key=lambda x: -x[1]))
    }
    
    json_file = filepath.stem + "_complete.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, default=str)
    print(f"  ✅ JSON saved to: {json_file}")
    
    # Text report
    report_file = filepath.stem + "_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"MCC FILE ANALYSIS REPORT\n")
        f.write(f"File: {filepath}\n")
        f.write("=" * 80 + "\n\n")
        
        if info['metadata']:
            f.write("METADATA:\n")
            for key, value in info['metadata'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
        
        if info['chunk_info']:
            f.write("CHUNK INFO:\n")
            for key, value in info['chunk_info'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
        
        f.write(f"ENTITIES: {len(info['entities'])} total\n")
        for entity_type, count in sorted(entity_counts.items()):
            f.write(f"  {entity_type}: {count}x\n")
        f.write("\n")
        
        f.write("ENTITY DETAILS:\n")
        f.write("-" * 80 + "\n")
        for i, entity in enumerate(info['entities'], 1):
            f.write(f"\n[{i}] {entity['id']}\n")
            if entity['pos']:
                f.write(f"  Position: ({entity['pos'][0]:.2f}, {entity['pos'][1]:.2f}, {entity['pos'][2]:.2f})\n")
            if entity['rotation']:
                f.write(f"  Rotation: Yaw={entity['rotation'][0]:.1f}°, Pitch={entity['rotation'][1]:.1f}°\n")
            if entity['motion']:
                f.write(f"  Motion: ({entity['motion'][0]:.3f}, {entity['motion'][1]:.3f}, {entity['motion'][2]:.3f})\n")
            if entity['on_ground'] is not None:
                f.write(f"  On Ground: {entity['on_ground']}\n")
            if entity['spawn_reason']:
                f.write(f"  Spawn Reason: {entity['spawn_reason']}\n")
            if entity['attributes']:
                f.write(f"  Attributes:\n")
                for attr_name, attr_value in entity['attributes'].items():
                    f.write(f"    - {attr_name}: {attr_value}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"BLOCKS: {sum(info['blocks'].values())} total, {len(info['blocks'])} unique\n")
        f.write("=" * 80 + "\n")
        for block_type, count in sorted(info['blocks'].items(), key=lambda x: -x[1]):
            f.write(f"  {block_type}: {count}x\n")
    
    print(f"  ✅ Report saved to: {report_file}")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    filepath = Path("c.2.-50.mcc")
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
    else:
        analyze_mcc_file(filepath)
