import json
import re

# Read the racecard
with open('c:/Users/ASUS/hkjc/data/racecard_20260406_R5.json', 'r') as f:
    data = json.load(f)

# Raw data from last_6_runs showing correct info
# MR INCREDIBLE: 135, K Teetan, 4, B Crawford
# EVERSTAR: 134, Y L Chung (-2), 9, Y S Tsui
# THOUSAND SPIRIT: 134, L Ferraris, 8, M Newnham
# GOLDENTRONICMIGHTY: 133, M L Yeung, 13, J Richards
# HEALTHY PONY: 128, M Chadwick, 6, C W Chang
# LUCRATIVE EIGHT: 128, H Y Yuen (-10), 3, P F Yiu
# SUPERB SPIRIT: 128, Z Purton, 10, K W Lui
# CALL ME SUCCESS: 127, A Atzeni, 7, D Eustace
# DRAGON HALL: 126, J Orman, 11, D J Hall
# LITTLE MONSTER: 125, K C Leung, 14, W K Mo
# SUNNY Q: 121, H Bentley, 12, W Y So
# COME FAST FAY FAY: 120, R Kingscote, 5, K H Ting
# MONEY TYCOON: 119, C Y Ho, 1, F C Lor
# RIDING HIGH: 119, A Badel, 2, D J Whyte

# Correct horse data
correct_data = {
    'MR INCREDIBLE': {'jockey': 'K Teetan', 'draw': 4, 'trainer': 'B Crawford', 'weight': 135},
    'EVERSTAR': {'jockey': 'Y L Chung', 'draw': 9, 'trainer': 'Y S Tsui', 'weight': 134},
    'THOUSAND SPIRIT': {'jockey': 'L Ferraris', 'draw': 8, 'trainer': 'M Newnham', 'weight': 134},
    'GOLDENTRONICMIGHTY': {'jockey': 'M L Yeung', 'draw': 13, 'trainer': 'J Richards', 'weight': 133},
    'HEALTHY PONY': {'jockey': 'M Chadwick', 'draw': 6, 'trainer': 'C W Chang', 'weight': 128},
    'LUCRATIVE EIGHT': {'jockey': 'H Y Yuen', 'draw': 3, 'trainer': 'P F Yiu', 'weight': 128},
    'SUPERB SPIRIT': {'jockey': 'Z Purton', 'draw': 10, 'trainer': 'K W Lui', 'weight': 128},
    'CALL ME SUCCESS': {'jockey': 'A Atzeni', 'draw': 7, 'trainer': 'D Eustace', 'weight': 127},
    'DRAGON HALL': {'jockey': 'J Orman', 'draw': 11, 'trainer': 'D J Hall', 'weight': 126},
    'LITTLE MONSTER': {'jockey': 'K C Leung', 'draw': 14, 'trainer': 'W K Mo', 'weight': 125},
    'SUNNY Q': {'jockey': 'H Bentley', 'draw': 12, 'trainer': 'W Y So', 'weight': 121},
    'COME FAST FAY FAY': {'jockey': 'R Kingscote', 'draw': 5, 'trainer': 'K H Ting', 'weight': 120},
    'MONEY TYCOON': {'jockey': 'C Y Ho', 'draw': 1, 'trainer': 'F C Lor', 'weight': 119},
    'RIDING HIGH': {'jockey': 'A Badel', 'draw': 2, 'trainer': 'D J Whyte', 'weight': 119}
}

# Fix the horses
fixed_horses = []
for horse in data['horses']:
    name = horse['horse_name']
    if name in correct_data:
        horse['jockey'] = correct_data[name]['jockey']
        horse['draw'] = correct_data[name]['draw']
        horse['trainer'] = correct_data[name]['trainer']
        horse['weight'] = correct_data[name]['weight']
        fixed_horses.append(horse)

# Update data
data['horses'] = fixed_horses

# Save
with open('c:/Users/ASUS/hkjc/data/racecard_20260406_R5.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Fixed racecard with {len(fixed_horses)} horses")
