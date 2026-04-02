"""
Test script for Dynamic Confidence Thresholds
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config

def test_dynamic_confidence():
    print("=== Testing Dynamic Confidence Thresholds ===\n")
    
    # Test different race conditions
    test_cases = [
        {
            "name": "Standard Race (Class 3, 10 horses, Good track)",
            "race_class": 3,
            "field_size": 10,
            "track_condition": "GOOD",
            "distance": 1200,
            "expected": 0.35  # Base confidence
        },
        {
            "name": "Low Class (Class 5, 12 horses, Good track)",
            "race_class": 5,
            "field_size": 12,
            "track_condition": "GOOD", 
            "distance": 1200,
            "expected": 0.45  # Base + 0.10 for class 5
        },
        {
            "name": "Large Field (Class 3, 14 horses, Good track)",
            "race_class": 3,
            "field_size": 14,
            "track_condition": "GOOD",
            "distance": 1200,
            "expected": 0.40  # Base + 0.05 for large field
        },
        {
            "name": "Wet Track (Class 3, 10 horses, Wet track)",
            "race_class": 3,
            "field_size": 10,
            "track_condition": "WET",
            "distance": 1200,
            "expected": 0.45  # Base + 0.10 for wet track
        },
        {
            "name": "Worst Case (Class 5, 14 horses, Wet track)",
            "race_class": 5,
            "field_size": 14,
            "track_condition": "WET",
            "distance": 1200,
            "expected": 0.60  # Base + 0.10 + 0.05 + 0.10 = 0.60 (max bound)
        },
        {
            "name": "Best Case (Class 1, 7 horses, Good track)",
            "race_class": 1,
            "field_size": 7,
            "track_condition": "GOOD",
            "distance": 1200,
            "expected": 0.30  # Base - 0.05 for small field
        },
        {
            "name": "Short Distance (Class 3, 10 horses, Good track, 800m)",
            "race_class": 3,
            "field_size": 10,
            "track_condition": "GOOD",
            "distance": 800,
            "expected": 0.40  # Base + 0.05 for short distance
        },
        {
            "name": "Long Distance (Class 3, 10 horses, Good track, 2200m)",
            "race_class": 3,
            "field_size": 10,
            "track_condition": "GOOD",
            "distance": 2200,
            "expected": 0.40  # Base + 0.05 for long distance
        }
    ]
    
    for test in test_cases:
        confidence = Config.get_dynamic_confidence(
            race_class=test["race_class"],
            field_size=test["field_size"],
            track_condition=test["track_condition"],
            distance=test["distance"]
        )
        
        status = "PASS" if abs(confidence - test["expected"]) < 0.01 else "FAIL"
        print(f"{status} {test['name']}")
        print(f"   Expected: {test['expected']:.2f}, Got: {confidence:.2f}")
        print()
    
    print("=== Comparison with Fixed Confidence ===")
    print(f"Fixed confidence: {Config.MIN_CONFIDENCE:.2f}")
    print(f"Dynamic range: 0.30 - 0.60")
    print(f"Expected improvement: More bets in favorable conditions, fewer in risky ones")
    
    # Simulate today's races with dynamic confidence
    print("\n=== Today's Races with Dynamic Confidence ===")
    today_races = [
        {"race": "R1", "class": 5, "field": 12, "track": "GOOD", "dist": 1200},
        {"race": "R2", "class": 4, "field": 12, "track": "GOOD", "dist": 1200},
        {"race": "R3", "class": 3, "field": 14, "track": "GOOD", "dist": 1200},
        {"race": "R4", "class": 4, "field": 11, "track": "GOOD", "dist": 1650},
        {"race": "R5", "class": 3, "field": 12, "track": "GOOD", "dist": 1200},
        {"race": "R6", "class": 4, "field": 12, "track": "GOOD", "dist": 1200},
        {"race": "R7", "class": 3, "field": 13, "track": "GOOD", "dist": 1200},
        {"race": "R8", "class": 4, "field": 12, "track": "GOOD", "dist": 1200},
        {"race": "R9", "class": 3, "field": 12, "track": "GOOD", "dist": 1200},
    ]
    
    for race in today_races:
        conf = Config.get_dynamic_confidence(
            race_class=race["class"],
            field_size=race["field"],
            track_condition=race["track"],
            distance=race["dist"]
        )
        vs_fixed = "LOWER" if conf < Config.MIN_CONFIDENCE else "HIGHER"
        print(f"{race['race']}: {conf:.2f} ({vs_fixed} than fixed {Config.MIN_CONFIDENCE:.2f})")

if __name__ == "__main__":
    test_dynamic_confidence()
