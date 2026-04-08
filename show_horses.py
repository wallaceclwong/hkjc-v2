import json

with open('c:/Users/ASUS/hkjc/data/racecard_20260406_R5.json', 'r') as f:
    data = json.load(f)

print('RACE 5 - Monday, April 6, 2026 - Sha Tin')
print('=' * 50)
print(f'Distance: {data["distance"]}m - {data["race_class"]} - {data["track_type"]}')
print(f'Course: {data["course"]} - Predicted Pace: {data["predicted_pace"]}')
print()

# Check the first entry for raw data
if data['horses'] and len(data['horses']) > 0:
    first_entry = data['horses'][0]
    if 'last_6_runs' in first_entry and first_entry['last_6_runs']:
        print("Raw data from first entry:")
        print("-" * 50)
        for i, line in enumerate(first_entry['last_6_runs'][:5]):
            print(f"{i}: {line}")
        print()

horses = data['horses']
print(f'Total Horses: {len(horses)}')
print()

# Extract detailed horse information
print(f'{"No.":>3} {"Horse":<25} {"Weight":>7} {"Jockey":<20} {"Trainer":<20} {"Draw":>5}')
print('-' * 90)

for horse in horses:
    saddle_num = horse.get('saddle_number', '')
    horse_name = horse.get('horse_name', 'Unknown')
    weight = horse.get('weight', 0)
    jockey = horse.get('jockey', '')
    trainer = horse.get('trainer', '')
    draw = horse.get('draw', '')
    
    # Skip placeholder entries
    if horse_name in ['WFA', 'N/A', ''] or saddle_num == '':
        continue
        
    print(f'{saddle_num:>3} {horse_name[:24]:<25} {weight:>7} {jockey[:19]:<20} {trainer[:19]:<20} {draw:>5}')

print()
print('Note: Draw information now available')
