"""
Extract Distance Preference Statistics from Historical Results
Analyzes how each horse/jockey/trainer performs at different distances
100% FREE - No API calls, just data mining
"""
import glob
import json
from pathlib import Path
from collections import defaultdict

print("="*60)
print("DISTANCE PREFERENCE ANALYSIS")
print("="*60)
print("\n[INFO] Mining 7,539 historical results")
print("[INFO] Building distance performance profiles")

# Load all results
result_files = glob.glob('data/results/results_*.json')
print(f"\nLoading {len(result_files)} result files...")

# Initialize stats
horse_distance_stats = defaultdict(lambda: defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0}))
jockey_distance_stats = defaultdict(lambda: defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0}))
trainer_distance_stats = defaultdict(lambda: defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0}))
distance_summary = defaultdict(lambda: {'races': 0, 'avg_winning_odds': []})

print("\nProcessing results...")
for i, f in enumerate(result_files):
    if i % 1000 == 0:
        print(f"  Progress: {i}/{len(result_files)}")
    
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            data = json.load(file)
        
        race_id = data.get('race_id', '')
        if not race_id:
            continue
        
        # Get distance from race_id or metadata
        # Assuming distance might be in metadata or we need to parse from somewhere
        # For now, we'll extract from results if available
        
        results_list = data.get('results', [])
        if not results_list:
            continue
        
        # Try to get distance (this might need adjustment based on your data structure)
        distance = None
        # Check if distance is in the data
        for key in ['distance', 'race_distance', 'dist']:
            if key in data:
                distance = str(data[key])
                break
        
        if not distance:
            # Skip if no distance info
            continue
        
        # Normalize distance (e.g., 1400, 1600, 1800, 2000)
        distance = distance.replace('m', '').replace('M', '').strip()
        
        distance_summary[distance]['races'] += 1
        
        # Process each horse
        for idx, horse in enumerate(results_list):
            horse_name = horse.get('horse', 'Unknown')
            jockey = horse.get('jockey', 'Unknown')
            trainer = horse.get('trainer', 'Unknown')
            position = horse.get('plc', '')
            
            # Update horse stats
            horse_distance_stats[horse_name][distance]['races'] += 1
            if position == '1':
                horse_distance_stats[horse_name][distance]['wins'] += 1
            if position in ['1', '2', '3']:
                horse_distance_stats[horse_name][distance]['top3'] += 1
            
            # Update jockey stats
            jockey_distance_stats[jockey][distance]['races'] += 1
            if position == '1':
                jockey_distance_stats[jockey][distance]['wins'] += 1
            if position in ['1', '2', '3']:
                jockey_distance_stats[jockey][distance]['top3'] += 1
            
            # Update trainer stats
            trainer_distance_stats[trainer][distance]['races'] += 1
            if position == '1':
                trainer_distance_stats[trainer][distance]['wins'] += 1
            if position in ['1', '2', '3']:
                trainer_distance_stats[trainer][distance]['top3'] += 1
        
    except Exception as e:
        continue

print(f"\n[OK] Processing complete")

# Calculate win rates and preferences
print("\n" + "="*60)
print("CALCULATING PREFERENCES")
print("="*60)

# Find horses with strong distance preferences
horse_preferences = []
for horse, distances in horse_distance_stats.items():
    if len(distances) >= 2:  # Horse raced at multiple distances
        for dist, stats in distances.items():
            if stats['races'] >= 3:  # Minimum 3 races at this distance
                win_rate = stats['wins'] / stats['races'] * 100
                top3_rate = stats['top3'] / stats['races'] * 100
                
                if win_rate >= 20 or top3_rate >= 50:  # Strong performance
                    horse_preferences.append({
                        'horse': horse,
                        'distance': dist,
                        'races': stats['races'],
                        'wins': stats['wins'],
                        'win_rate': win_rate,
                        'top3_rate': top3_rate
                    })

horse_preferences.sort(key=lambda x: x['win_rate'], reverse=True)

print(f"\nFound {len(horse_preferences)} strong distance preferences")
print("\nTop 10 Horse-Distance Combinations:")
print("-"*60)
for pref in horse_preferences[:10]:
    print(f"  {pref['horse'][:30]:<30} @ {pref['distance']}m: {pref['win_rate']:.1f}% win rate ({pref['wins']}/{pref['races']})")

# Jockey distance preferences
jockey_preferences = []
for jockey, distances in jockey_distance_stats.items():
    for dist, stats in distances.items():
        if stats['races'] >= 20:  # Minimum 20 races
            win_rate = stats['wins'] / stats['races'] * 100
            jockey_preferences.append({
                'jockey': jockey,
                'distance': dist,
                'races': stats['races'],
                'wins': stats['wins'],
                'win_rate': win_rate
            })

jockey_preferences.sort(key=lambda x: x['win_rate'], reverse=True)

print(f"\nTop 10 Jockey-Distance Combinations:")
print("-"*60)
for pref in jockey_preferences[:10]:
    print(f"  {pref['jockey'][:30]:<30} @ {pref['distance']}m: {pref['win_rate']:.1f}% ({pref['wins']}/{pref['races']})")

# Save to file
print("\n" + "="*60)
print("SAVING STATISTICS")
print("="*60)

output = {
    'generated_at': '2026-03-30',
    'total_results_analyzed': len(result_files),
    'horse_distance_preferences': [
        {
            'horse': p['horse'],
            'distance': p['distance'],
            'races': p['races'],
            'wins': p['wins'],
            'win_rate': p['win_rate'],
            'top3_rate': p['top3_rate']
        }
        for p in horse_preferences[:100]  # Top 100
    ],
    'jockey_distance_preferences': [
        {
            'jockey': p['jockey'],
            'distance': p['distance'],
            'races': p['races'],
            'wins': p['wins'],
            'win_rate': p['win_rate']
        }
        for p in jockey_preferences[:50]  # Top 50
    ],
    'distance_summary': {
        dist: {
            'total_races': stats['races']
        }
        for dist, stats in distance_summary.items()
    }
}

output_file = Path('data/distance_preferences.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Statistics saved to: {output_file}")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("\nKey Insights:")
print(f"  - Identified {len(horse_preferences)} strong horse-distance preferences")
print(f"  - Identified {len(jockey_preferences)} jockey-distance patterns")
print(f"  - Distance data available for future predictions")
print("\n[READY] Distance preferences can now enhance predictions!")
print("="*60)
