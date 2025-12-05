#!/usr/bin/env python3
"""
Schneeball Timeline Analyse - Extrahiert Spawn-Zeitpunkte
"""
import json
import zlib
from collections import defaultdict
import struct
from io import BytesIO

class NBTReader:
    """NBT Reader für detaillierte Entity-Analyse"""
    
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
    
    def read_list(self):
        tag_type = self.read_ubyte()
        length = self.read_int()
        return [self.read_tag(tag_type) for _ in range(length)]
    
    def read_compound(self):
        result = {}
        while True:
            tag_type = self.read_ubyte()
            if tag_type == self.TAG_End:
                break
            name = self.read_string()
            result[name] = self.read_tag(tag_type)
        return result
    
    def read_root(self):
        tag_type = self.read_ubyte()
        if tag_type == self.TAG_End:
            return None
        name = self.read_string()
        data = self.read_tag(tag_type)
        return {name: data}

def extract_snowball_ages(nbt_data):
    """Extrahiere Age-Daten von allen Schneebällen"""
    snowballs = []
    
    def traverse(obj, path=""):
        if isinstance(obj, dict):
            # Prüfe ob das eine Entities-Liste ist
            if 'Entities' in obj and isinstance(obj['Entities'], list):
                for entity in obj['Entities']:
                    if isinstance(entity, dict) and entity.get('id') == 'minecraft:snowball':
                        age = entity.get('Age', 0)
                        pos = entity.get('Pos', [0, 0, 0])
                        motion = entity.get('Motion', [0, 0, 0])
                        
                        snowballs.append({
                            'age': age,
                            'pos': pos,
                            'motion': motion
                        })
            
            for key, value in obj.items():
                traverse(value, f"{path}.{key}" if path else key)
        
        elif isinstance(obj, list):
            for item in obj:
                traverse(item, path)
    
    traverse(nbt_data)
    return snowballs

print("=" * 80)
print("⏰ SCHNEEBALL TIMELINE ANALYSE")
print("=" * 80)

# Lade und dekomprimiere
print("\n📂 Lade MCC-Datei...")
with open('c.2.-50.mcc', 'rb') as f:
    compressed = f.read()

print(f"   Komprimierte Größe: {len(compressed):,} bytes")

decompressed = zlib.decompress(compressed)
print(f"   Dekomprimierte Größe: {len(decompressed):,} bytes")

# Parse NBT
print("\n📖 Parse NBT-Struktur...")
try:
    reader = NBTReader(decompressed)
    nbt_data = reader.read_root()
    print("   ✓ NBT erfolgreich geparst")
except Exception as e:
    print(f"   ❌ Fehler: {e}")
    exit(1)

# Extrahiere Schneeball-Daten
print("\n🔍 Extrahiere Schneeball-Informationen...")
snowballs = extract_snowball_ages(nbt_data)

if not snowballs:
    print("❌ Keine Schneeball-Daten gefunden!")
    exit(1)

print(f"   ✓ {len(snowballs):,} Schneebälle gefunden")

# Analysiere Ages
print("\n" + "=" * 80)
print("📊 ZEITLICHE ANALYSE")
print("=" * 80)

ages = [sb['age'] for sb in snowballs]
ages.sort()

min_age = min(ages)
max_age = max(ages)
avg_age = sum(ages) / len(ages)

print(f"\nJüngster Schneeball:  {min_age:>8} Ticks = {min_age/20:>8.1f}s = {min_age/1200:>6.1f} min")
print(f"Ältester Schneeball:  {max_age:>8} Ticks = {max_age/20:>8.1f}s = {max_age/1200:>6.1f} min")
print(f"Durchschnittsalter:   {avg_age:>8.0f} Ticks = {avg_age/20:>8.1f}s = {avg_age/1200:>6.1f} min")
print(f"\nZeitspanne:           {(max_age-min_age)/1200:.1f} Minuten")
print(f"                      {(max_age-min_age)/72000:.2f} Stunden")

# Berechne Spawn-Rate
spawn_rate = 0
if max_age > 0:
    total_seconds = max_age / 20
    spawn_rate = len(snowballs) / total_seconds
    print(f"\n📈 Durchschnittliche Spawn-Rate:")
    print(f"   {spawn_rate:.2f} Schneebälle/Sekunde")
    print(f"   {spawn_rate*60:.0f} Schneebälle/Minute")
    print(f"   {spawn_rate*3600:.0f} Schneebälle/Stunde")

# Gruppiere nach Zeit
print("\n" + "=" * 80)
print("📅 SPAWN-TIMELINE (in 5-Minuten-Intervallen)")
print("=" * 80)

age_groups = defaultdict(int)
for age in ages:
    minute_group = age // 6000  # 6000 Ticks = 5 Minuten
    age_groups[minute_group] += 1

sorted_groups = sorted(age_groups.items())

print(f"\n{'Zeit vor Save':<25} {'Anzahl':<12} {'Visualisierung'}")
print("-" * 80)

max_count = max(age_groups.values())
for group, count in sorted_groups[:50]:
    minutes = group * 5
    hours = minutes / 60
    bar_length = int(50 * count / max_count)
    bar = "█" * bar_length
    
    if hours >= 1:
        time_str = f"{hours:.1f}h vor Save"
    else:
        time_str = f"{minutes} min vor Save"
    
    print(f"{time_str:<25} {count:>6} │ {bar}")

# Finde Anomalien/Spikes
print("\n" + "=" * 80)
print("🔍 ANOMALIE-DETEKTION")
print("=" * 80)

# 30-Sekunden-Buckets
fine_buckets = defaultdict(int)
for age in ages:
    bucket = age // 600  # 600 Ticks = 30 Sekunden
    fine_buckets[bucket] += 1

avg_bucket = sum(fine_buckets.values()) / len(fine_buckets)
spikes = [(k*30, v) for k, v in fine_buckets.items() if v > avg_bucket * 3]

if spikes:
    print(f"\n⚠️  {len(spikes)} ANOMALIEN GEFUNDEN!")
    print("\nZeitpunkte mit ungewöhnlich hoher Aktivität (>3x Durchschnitt):")
    print(f"\n{'Zeit vor Save':<20} {'Anzahl':<12} {'Faktor'}")
    print("-" * 60)
    
    for seconds_ago, count in sorted(spikes, key=lambda x: x[1], reverse=True)[:20]:
        minutes = seconds_ago / 60
        factor = count / avg_bucket
        if minutes >= 60:
            time_str = f"{minutes/60:.1f}h"
        else:
            time_str = f"{minutes:.1f} min"
        print(f"{time_str:<20} {count:>6} │ {factor:>5.1f}x normal")
    
    print("\n🐛 VERDACHT: Bug-Event oder Lag-Spike!")
else:
    print("\n✓ Keine signifikanten Anomalien gefunden")
    print("  → Gleichmäßige Spawn-Rate über die Zeit")

# Motion-Analyse
print("\n" + "=" * 80)
print("💨 BEWEGUNGS-ANALYSE")
print("=" * 80)

motions = [sb['motion'] for sb in snowballs]
stationary = sum(1 for m in motions if all(abs(x) < 0.01 for x in m))
moving = len(motions) - stationary

avg_motion = sum(sum(abs(x) for x in m) for m in motions) / len(motions)

print(f"\nSchneebälle in Bewegung:    {moving:>6} ({moving/len(motions)*100:.1f}%)")
print(f"Stationäre Schneebälle:     {stationary:>6} ({stationary/len(motions)*100:.1f}%)")
print(f"Durchschnittliche Bewegung: {avg_motion:.6f}")

if stationary > len(motions) * 0.5:
    print("\n🐛 KRITISCH: Über 50% der Schneebälle sind eingefroren!")
    print("   → Entity-Tick Bug oder Stuck State bestätigt!")

# Y-Level Analyse
print("\n" + "=" * 80)
print("📉 FALL-ANALYSE")
print("=" * 80)

y_levels = [sb['pos'][1] for sb in snowballs]
min_y = min(y_levels)
max_y = max(y_levels)
avg_y = sum(y_levels) / len(y_levels)

print(f"\nNiedrigste Position:  Y = {min_y:.2f}")
print(f"Höchste Position:     Y = {max_y:.2f}")
print(f"Durchschnitt:         Y = {avg_y:.2f}")
print(f"Spannweite:          ΔY = {max_y - min_y:.2f}")

# Korreliere Age mit Y-Position
old_snowballs = [sb for sb in snowballs if sb['age'] > 1200]
young_snowballs = [sb for sb in snowballs if sb['age'] < 200]

if old_snowballs and young_snowballs:
    avg_y_old = sum(sb['pos'][1] for sb in old_snowballs) / len(old_snowballs)
    avg_y_young = sum(sb['pos'][1] for sb in young_snowballs) / len(young_snowballs)
    
    print(f"\nAlte Schneebälle (>1min):   Y = {avg_y_old:.2f}")
    print(f"Junge Schneebälle (<10s):   Y = {avg_y_young:.2f}")
    print(f"Differenz:                 ΔY = {avg_y_young - avg_y_old:.2f}")
    
    if abs(avg_y_young - avg_y_old) < 1.0:
        print("\n🐛 ANOMALIE: Schneebälle fallen nicht korrekt!")
        print("   → Gravity-Bug oder Entity-Freeze")

# Exportiere Ergebnisse
print("\n" + "=" * 80)
print("💾 EXPORTIERE ERGEBNISSE")
print("=" * 80)

timeline_data = {
    'summary': {
        'total_snowballs': len(snowballs),
        'min_age_ticks': min_age,
        'max_age_ticks': max_age,
        'avg_age_ticks': avg_age,
        'timespan_minutes': (max_age - min_age) / 1200,
        'timespan_hours': (max_age - min_age) / 72000,
        'spawn_rate_per_second': spawn_rate if max_age > 0 else 0,
        'stationary_percentage': stationary / len(motions) * 100,
        'avg_motion': avg_motion
    },
    'timeline_5min_intervals': {str(k*5): v for k, v in sorted_groups},
    'anomalies': [{'seconds_ago': s, 'count': c, 'factor': c/avg_bucket} for s, c in spikes] if spikes else [],
    'y_level_stats': {
        'min': min_y,
        'max': max_y,
        'avg': avg_y,
        'range': max_y - min_y
    }
}

with open('snowball_timeline.json', 'w') as f:
    json.dump(timeline_data, f, indent=2)

print("\n✓ Timeline-Daten: snowball_timeline.json")

# Erstelle auch eine lesbare Text-Version
with open('snowball_timeline.txt', 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("SCHNEEBALL TIMELINE ANALYSE\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"Gesamt: {len(snowballs):,} Schneebälle\n\n")
    
    f.write("ZEITLICHE STATISTIKEN:\n")
    f.write("-" * 80 + "\n")
    f.write(f"Ältester Schneeball:  {max_age:,} Ticks = {max_age/1200:.1f} Minuten\n")
    f.write(f"Jüngster Schneeball:  {min_age:,} Ticks = {min_age/1200:.1f} Minuten\n")
    f.write(f"Zeitspanne:           {(max_age-min_age)/72000:.2f} Stunden\n")
    f.write(f"Spawn-Rate:           {spawn_rate:.2f} Schneebälle/Sekunde\n\n")
    
    f.write("TIMELINE (5-Minuten-Intervalle):\n")
    f.write("-" * 80 + "\n")
    for group, count in sorted_groups:
        minutes = group * 5
        f.write(f"{minutes:>4} min vor Save: {count:>6} Schneebälle\n")
    
    if spikes:
        f.write("\n" + "=" * 80 + "\n")
        f.write("ANOMALIEN (Spawn-Spikes):\n")
        f.write("-" * 80 + "\n")
        for seconds_ago, count in sorted(spikes, key=lambda x: x[1], reverse=True):
            f.write(f"{seconds_ago/60:>6.1f} min vor Save: {count:>6} Schneebälle ({count/avg_bucket:.1f}x normal)\n")

print("✓ Timeline-Report:  snowball_timeline.txt")

print("\n" + "=" * 80)
print("✅ ANALYSE ABGESCHLOSSEN!")
print("=" * 80)
