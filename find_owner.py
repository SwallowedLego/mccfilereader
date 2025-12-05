#!/usr/bin/env python3
"""
Erweiterte Analyse - Suche nach Spieler-Informationen
"""
import zlib
import struct
from io import BytesIO
import json

class DetailedNBTReader:
    TAG_Compound = 10
    TAG_List = 9
    TAG_String = 8
    TAG_Int = 3
    TAG_Long = 4
    TAG_End = 0
    
    def __init__(self, data):
        self.stream = BytesIO(data)
        self.player_info = []
    
    def read_ubyte(self):
        return struct.unpack('>B', self.stream.read(1))[0]
    
    def read_int(self):
        return struct.unpack('>i', self.stream.read(4))[0]
    
    def read_long(self):
        return struct.unpack('>q', self.stream.read(8))[0]
    
    def read_string(self):
        length = struct.unpack('>H', self.stream.read(2))[0]
        return self.stream.read(length).decode('utf-8', errors='replace')
    
    def skip_tag(self, tag_type):
        """Skip a tag without parsing"""
        if tag_type == 0:  # End
            return
        elif tag_type == 1:  # Byte
            self.stream.read(1)
        elif tag_type == 2:  # Short
            self.stream.read(2)
        elif tag_type == 3:  # Int
            self.stream.read(4)
        elif tag_type == 4:  # Long
            self.stream.read(8)
        elif tag_type == 5:  # Float
            self.stream.read(4)
        elif tag_type == 6:  # Double
            self.stream.read(8)
        elif tag_type == 7:  # Byte Array
            length = self.read_int()
            self.stream.read(length)
        elif tag_type == 8:  # String
            self.read_string()
        elif tag_type == 9:  # List
            list_type = self.read_ubyte()
            length = self.read_int()
            for _ in range(length):
                self.skip_tag(list_type)
        elif tag_type == 10:  # Compound
            self.skip_compound()
        elif tag_type == 11:  # Int Array
            length = self.read_int()
            self.stream.read(length * 4)
        elif tag_type == 12:  # Long Array
            length = self.read_int()
            self.stream.read(length * 8)
    
    def skip_compound(self):
        while True:
            tag_type = self.read_ubyte()
            if tag_type == 0:
                break
            self.read_string()  # name
            self.skip_tag(tag_type)
    
    def search_for_owners(self):
        """Search specifically for owner information"""
        try:
            # Read root compound
            root_type = self.read_ubyte()
            if root_type != 10:
                return
            
            root_name = self.read_string()
            print(f"Root tag: {root_name}")
            
            self.search_compound(depth=0)
            
        except Exception as e:
            print(f"Error during search: {e}")
    
    def search_compound(self, depth=0, max_depth=20):
        """Recursively search compound tags"""
        if depth > max_depth:
            return
        
        try:
            while True:
                tag_type = self.read_ubyte()
                if tag_type == 0:  # End tag
                    break
                
                name = self.read_string()
                
                # Check for owner-related fields
                if any(keyword in name.lower() for keyword in ['owner', 'thrower', 'source', 'player']):
                    print(f"{'  ' * depth}Found: {name} (type {tag_type})")
                    
                    if tag_type == 8:  # String
                        value = self.read_string()
                        print(f"{'  ' * depth}  Value: {value}")
                        self.player_info.append({name: value})
                    elif tag_type in [3, 4]:  # Int or Long (might be UUID parts)
                        if tag_type == 3:
                            value = self.read_int()
                        else:
                            value = self.read_long()
                        print(f"{'  ' * depth}  Value: {value}")
                        self.player_info.append({name: value})
                    else:
                        self.skip_tag(tag_type)
                elif tag_type == 10:  # Nested compound
                    if depth < 5:  # Only recurse a bit
                        self.search_compound(depth + 1, max_depth)
                    else:
                        self.skip_compound()
                else:
                    self.skip_tag(tag_type)
                    
        except Exception as e:
            if depth == 0:
                print(f"Search ended: {e}")

# Main analysis
print("=" * 80)
print("ERWEITERTE SPIELER-ANALYSE")
print("=" * 80)

with open('c.2.-50.mcc', 'rb') as f:
    compressed = f.read()

data = zlib.decompress(compressed)
print(f"\nDekomprimierte Größe: {len(data):,} bytes\n")

reader = DetailedNBTReader(data)
print("Suche nach Owner-Informationen in der NBT-Struktur...\n")
reader.search_for_owners()

if reader.player_info:
    print(f"\n{'=' * 80}")
    print("GEFUNDENE SPIELER-INFORMATIONEN:")
    print("=" * 80)
    for info in reader.player_info[:20]:
        print(f"  {info}")
else:
    print(f"\n{'=' * 80}")
    print("❌ KEINE SPIELER-INFORMATIONEN IN DEN SCHNEEBÄLLEN")
    print("=" * 80)
    print("\nMögliche Erklärungen:")
    print("1. Die Schneebälle wurden von einem Command Block erzeugt")
    print("2. Die Owner-Daten wurden bereits entfernt (Server-Optimierung)")
    print("3. Die Schneebälle stammen von einem Schneemann (Snow Golem)")
    print("4. Die Chunk-Datei wurde bereinigt/gefiltert")
