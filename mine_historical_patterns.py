"""
Mine Historical Results for Statistical Patterns
Analyzes 7,506 race results to extract winning patterns
100% FREE - No API calls, just data analysis
"""
import glob
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

print("="*60)
print("HISTORICAL PATTERN MINING")
print("="*60)
print("\n[INFO] Analyzing 7,506 race results")
print("[INFO] Extracting statistical patterns")

# Load all results
result_files = glob.glob('data/results/results_*.json')
print(f"\nLoading {len(result_files)} result files...")

results_data = []
for i, f in enumerate(result_files):
    if i % 1000 == 0:
        print(f"  Progress: {i}/{len(result_files)}")
    
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            data = json.load(file)
            results_data.append(data)
    except:
        continue

print(f"\n[OK] Loaded {len(results_data)} results")

# Initialize stats
jockey_stats = defaultdict(lambda: {'wins': 0, 'races': 0, 'total_odds': 0})
trainer_stats = defaultdict(lambda: {'wins': 0, 'races': 0})
track_stats = defaultdict(lambda: {'races': 0, 'inside_wins': 0, 'outside_wins': 0})
distance_stats = defaultdict(lambda: {'races': 0, 'winners': []})
class_stats = defaultdict(lambda: {'races': 0, 'avg_winning_odds': []})
venue_stats = defaultdict(lambda: {'races': 0, 'wins_by_draw': defaultdict(int)})

print("\n" + "="*60)
print("ANALYZING PATTERNS")
print("="*60)

for i, result in enumerate(results_data):
    if i % 1000 == 0:
        print(f"  Progress: {i}/{len(results_data)}")
    
    race_id = result.get('race_id', '')
    if not race_id:
        continue
    
    parts = race_id.split('_')
    if len(parts) < 2:
        continue
    
    venue = parts[1] if len(parts) > 1 else 'Unknown'
    
    # Get race info
    results_list = result.get('results', [])
    if not results_list:
        continue
    
    # Winner info
    winner = results_list[0]
    winner_draw = int(winner.get('draw', 0)) if winner.get('draw') else 0
    winner_jockey = winner.get('jockey', 'Unknown')
    winner_trainer = winner.get('trainer', 'Unknown')
    
    # Handle odds safely
    try:
        winner_odds = float(winner.get('win_odds', 0) or 0)
    except (ValueError, TypeError):
        winner_odds = 0
    
    # Track stats
    track_stats[venue]['races'] += 1
    
    # Draw position analysis
    total_runners = len(results_list)
    if total_runners > 0:
        if winner_draw <= total_runners / 2:
            track_stats[venue]['inside_wins'] += 1
        else:
            track_stats[venue]['outside_wins'] += 1
        
        venue_stats[venue]['races'] += 1
        venue_stats[venue]['wins_by_draw'][winner_draw] += 1
    
    # Jockey stats
    for horse in results_list:
        jockey = horse.get('jockey', 'Unknown')
        jockey_stats[jockey]['races'] += 1
        
        if horse.get('plc') == '1':
            jockey_stats[jockey]['wins'] += 1
            jockey_stats[jockey]['total_odds'] += winner_odds
    
    # Trainer stats
    for horse in results_list:
        trainer = horse.get('trainer', 'Unknown')
        trainer_stats[trainer]['races'] += 1
        
        if horse.get('plc') == '1':
            trainer_stats[trainer]['wins'] += 1

print("\n" + "="*60)
print("PATTERN ANALYSIS RESULTS")
print("="*60)

# Track Bias Analysis
print("\n1. TRACK BIAS (Draw Position)")
print("-"*40)
for venue in ['ST', 'HV']:
    if venue in track_stats:
        stats = track_stats[venue]
        total = stats['races']
        inside = stats['inside_wins']
        outside = stats['outside_wins']
        
        if total > 0:
            inside_pct = inside / total * 100
            outside_pct = outside / total * 100
            
            print(f"\n{venue}:")
            print(f"  Total races: {total}")
            print(f"  Inside draws win: {inside_pct:.1f}%")
            print(f"  Outside draws win: {outside_pct:.1f}%")
            
            if inside_pct > 55:
                print(f"  [BIAS] Inside draws favored!")
            elif outside_pct > 55:
                print(f"  [BIAS] Outside draws favored!")
            else:
                print(f"  [NEUTRAL] No significant bias")

# Top Jockeys
print("\n2. TOP JOCKEYS (Win Rate)")
print("-"*40)
jockey_win_rates = []
for jockey, stats in jockey_stats.items():
    if stats['races'] >= 50:  # Minimum 50 races
        win_rate = stats['wins'] / stats['races'] * 100
        jockey_win_rates.append((jockey, win_rate, stats['wins'], stats['races']))

jockey_win_rates.sort(key=lambda x: x[1], reverse=True)
for jockey, win_rate, wins, races in jockey_win_rates[:10]:
    print(f"  {jockey}: {win_rate:.1f}% ({wins}/{races})")

# Top Trainers
print("\n3. TOP TRAINERS (Win Rate)")
print("-"*40)
trainer_win_rates = []
for trainer, stats in trainer_stats.items():
    if stats['races'] >= 50:  # Minimum 50 races
        win_rate = stats['wins'] / stats['races'] * 100
        trainer_win_rates.append((trainer, win_rate, stats['wins'], stats['races']))

trainer_win_rates.sort(key=lambda x: x[1], reverse=True)
for trainer, win_rate, wins, races in trainer_win_rates[:10]:
    print(f"  {trainer}: {win_rate:.1f}% ({wins}/{races})")

# Save statistics to file
print("\n" + "="*60)
print("SAVING STATISTICS")
print("="*60)

stats_output = {
    'generated_at': datetime.now().isoformat(),
    'total_races_analyzed': len(results_data),
    'track_bias': {
        venue: {
            'races': stats['races'],
            'inside_win_pct': stats['inside_wins'] / stats['races'] * 100 if stats['races'] > 0 else 0,
            'outside_win_pct': stats['outside_wins'] / stats['races'] * 100 if stats['races'] > 0 else 0
        }
        for venue, stats in track_stats.items()
    },
    'top_jockeys': [
        {
            'jockey': jockey,
            'win_rate': win_rate,
            'wins': wins,
            'races': races
        }
        for jockey, win_rate, wins, races in jockey_win_rates[:20]
    ],
    'top_trainers': [
        {
            'trainer': trainer,
            'win_rate': win_rate,
            'wins': wins,
            'races': races
        }
        for trainer, win_rate, wins, races in trainer_win_rates[:20]
    ],
    'venue_draw_stats': {
        venue: dict(stats['wins_by_draw'])
        for venue, stats in venue_stats.items()
    }
}

output_file = Path('data/historical_statistics.json')
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(stats_output, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Statistics saved to: {output_file}")

print("\n" + "="*60)
print("PATTERN MINING COMPLETE")
print("="*60)
print("\nKey Insights:")
print(f"  - Analyzed {len(results_data)} races")
print(f"  - Identified {len([j for j in jockey_win_rates if j[1] > 15])} elite jockeys (>15% win rate)")
print(f"  - Identified {len([t for t in trainer_win_rates if t[1] > 15])} elite trainers (>15% win rate)")
print(f"  - Track bias patterns documented")
print("\n[READY] Statistical features available for predictions!")
print("="*60)
