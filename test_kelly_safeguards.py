#!/usr/bin/env python3
"""
Test script to demonstrate Kelly safeguards
"""
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.market_watchdog import MarketWatchdog
from config.settings import Config
from datetime import datetime

# Load today's prediction
with open("data/predictions/prediction_2026-03-29_ST_R1.json", "r") as f:
    pred = json.load(f)

# Mock odds (same as in file)
mock_odds = {
    "2": 8.5, "3": 7.8, "4": 40.0, "5": 44.0, "6": 29.0,
    "7": 8.8, "8": 14.0, "9": 8.4, "10": 30.0, "11": 22.0, "12": 49.0
}

print("=== KELLY SAFEGUARDS DEMO ===")
print(f"Bankroll: ${Config.INITIAL_BANKROLL}")
print(f"Kelly Fraction: {Config.KELLY_FRACTION}")
print(f"Max Exposure: ${Config.INITIAL_BANKROLL * 0.05}")
print()

# Calculate with new safeguards
probabilities = pred.get("probabilities", {})
kelly_stakes = {}
edges = {}

# Calculate edges for all horses first
for horse_no, prob in probabilities.items():
    odds = mock_odds.get(str(horse_no))
    if odds and odds > 1 and prob > 0:
        edge = (prob * odds - 1) / (odds - 1)
        edges[str(horse_no)] = edge

# Sort by edge (highest first) and apply safeguards
sorted_horses = sorted(edges.items(), key=lambda x: x[1], reverse=True)
total_exposure = 0
max_exposure = Config.INITIAL_BANKROLL * 0.05

print("=== EDGE CALCULATIONS ===")
for horse_no, edge in sorted_horses:
    if edge < 0.05:
        print(f"Horse {horse_no}: Edge {edge:.3f} → BELOW 5% THRESHOLD")
        continue
    
    if len(kelly_stakes) >= 2:
        print(f"Horse {horse_no}: Edge {edge:.3f} → MAX 2 HORSES REACHED")
        continue
    
    stake = Config.INITIAL_BANKROLL * Config.KELLY_FRACTION * edge
    
    if total_exposure + stake > max_exposure:
        remaining = max_exposure - total_exposure
        if remaining > 0:
            stake = remaining
        else:
            print(f"Horse {horse_no}: Edge {edge:.3f} → EXPOSURE CAP REACHED")
            break
    
    # Round to nearest $10 multiple
    stake = max(10, int(round(stake / 10) * 10))
    
    kelly_stakes[horse_no] = stake
    total_exposure += stake
    
    print(f"Horse {horse_no}: Edge {edge:.3f} → Stake ${stake} (Total: ${total_exposure})")

print()
print("=== COMPARISON ===")
print("OLD Kelly stakes:")
for h, stake in pred["kelly_stakes"].items():
    print(f"  Horse {h}: ${stake}")

print("NEW Kelly stakes (with safeguards):")
for h, stake in kelly_stakes.items():
    print(f"  Horse {h}: ${stake}")

print()
print(f"OLD total exposure: ${sum(pred['kelly_stakes'].values())}")
print(f"NEW total exposure: ${total_exposure}")
print(f"OLD horses: {len(pred['kelly_stakes'])}")
print(f"NEW horses: {len(kelly_stakes)}")
