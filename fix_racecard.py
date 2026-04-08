#!/usr/bin/env python3
"""
Fix racecard data by parsing raw tab-separated data from last_6_runs
"""

import json
import re

# Read the racecard
with open('c:/Users/ASUS/hkjc/data/racecard_20260406_R5.json', 'r') as f:
    data = json.load(f)

# Find the entry with all the raw data (the WFA entry)
raw_data = None
for horse in data['horses']:
    if horse['horse_name'] == 'WFA' and horse.get('last_6_runs'):
        raw_data = horse['last_6_runs']
        break

if not raw_data:
    print("No raw data found!")
    exit(1)

# Parse the raw tab-separated data
horse_lookup = {}

# Combine all lines and split by newlines
raw_text = "\n".join(raw_data)
lines = raw_text.split('\n')

for line in lines:
    # Skip empty lines and headers
    if not line.strip() or 'Horse No.' in line or 'Horse Wt.' in line:
        continue
    
    # Split by tabs
    parts = line.split('\t')
    
    # Find horse name (all uppercase with spaces)
    for i, part in enumerate(parts):
        if re.match(r'^[A-Z][A-Z\s]+$', part.strip()) and len(part.strip()) > 3:
            horse_name = part.strip()
            
            # The format is: saddle | last6runs | color | HORSE | weight | jockey | draw | trainer | rating | rating+
            # So we need to look at positions relative to horse name
            if i + 3 < len(parts):
                jockey_raw = parts[i + 1].strip() if i + 1 < len(parts) else ""
                draw_raw = parts[i + 2].strip() if i + 2 < len(parts) else ""
                trainer_raw = parts[i + 3].strip() if i + 3 < len(parts) else ""
                
                # Clean jockey (remove allowance like (-2))
                jockey = re.sub(r'\s*\(-?\d+\)', '', jockey_raw).strip()
                
                # Parse draw
                try:
                    draw = int(draw_raw)
                except:
                    draw = 0
                
                # Clean trainer
                trainer = trainer_raw.strip()
                
                # Only store if we got valid data
                if jockey and trainer and draw > 0:
                    horse_lookup[horse_name] = {
                        'jockey': jockey,
                        'draw': draw,
                        'trainer': trainer
                    }
                    print(f"Parsed: {horse_name} -> Jockey: {jockey}, Draw: {draw}, Trainer: {trainer}")

print(f"\nTotal horses parsed: {len(horse_lookup)}")

# Now update the horse entries
fixed_horses = []
seen = set()

for horse in data['horses']:
    name = horse['horse_name']
    
    # Skip placeholders and duplicates
    if name in ['WFA', 'N/A', ''] or name in seen:
        continue
    seen.add(name)
    
    # Update with correct data if available
    if name in horse_lookup:
        horse['jockey'] = horse_lookup[name]['jockey']
        horse['draw'] = horse_lookup[name]['draw']
        horse['trainer'] = horse_lookup[name]['trainer']
    
    fixed_horses.append(horse)

# Update the data
data['horses'] = fixed_horses

# Save the fixed racecard
with open('c:/Users/ASUS/hkjc/data/racecard_20260406_R5.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nFixed racecard saved with {len(fixed_horses)} horses")
