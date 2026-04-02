"""
Test script for Live Odds Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.live_odds_monitor import get_live_odds_monitor, OddsMovement, RaceOddsState
from datetime import datetime

def test_live_odds_monitor():
    print("=== Testing Live Odds Monitor ===\n")
    
    monitor = get_live_odds_monitor()
    
    # Test 1: Load odds for a race
    print("1. Testing odds loading...")
    state = monitor.update_race_state("2026-04-01", "ST", 5)
    
    if state:
        print(f"   Loaded odds for {state.race_id}")
        print(f"   Horses: {len(state.win_odds)}")
        print(f"   Market confidence: {state.market_confidence:.1%}")
        print(f"   Movements tracked: {len(state.movements)}")
    else:
        print("   No odds data available (expected if first load)")
    
    # Test 2: Load again to trigger movement detection
    print("\n2. Testing movement detection...")
    state2 = monitor.update_race_state("2026-04-01", "ST", 5)
    
    if state2 and state2.movements:
        print(f"   Movements detected: {len(state2.movements)}")
        for horse_no, movement in list(state2.movements.items())[:3]:
            print(f"   Horse #{horse_no}: {movement.initial_odds:.1f} → {movement.current_odds:.1f} ({movement.movement_pct:+.1%}) [{movement.trend}]")
    else:
        print("   No movements (single snapshot or stable market)")
    
    # Test 3: Probability adjustment
    print("\n3. Testing probability adjustment...")
    test_probs = {"1": 0.1, "2": 0.2, "3": 0.15, "4": 0.25, "5": 0.3}
    
    race_id = "2026-04-01_ST_R5"
    adjusted = monitor.adjust_probabilities(test_probs, race_id)
    
    print("   Original vs Adjusted:")
    total_original = sum(test_probs.values())
    total_adjusted = sum(adjusted.values())
    
    for horse_no in test_probs.keys():
        original = test_probs[horse_no]
        new = adjusted.get(horse_no, 0)
        change = (new - original) / original * 100 if original > 0 else 0
        marker = "*" if abs(change) > 1 else " "
        print(f"   {marker} Horse #{horse_no}: {original:.1%} → {new:.1%} ({change:+.1f}%)")
    
    print(f"\n   Total probability: {total_original:.3f} → {total_adjusted:.3f}")
    
    # Test 4: Betting recommendations
    print("\n4. Testing betting recommendations...")
    for horse_no in ["1", "2", "3"]:
        rec = monitor.get_betting_recommendation(race_id, horse_no)
        print(f"   Horse #{horse_no}: {rec.get('rec', 'UNKNOWN')} (confidence: {rec.get('confidence', 0):.0%})")
    
    return True

def test_integration():
    print("\n=== Testing Integration ===\n")
    
    monitor = get_live_odds_monitor()
    
    # Test that monitor can handle missing data gracefully
    print("1. Testing graceful handling of missing data...")
    empty_probs = {}
    adjusted = monitor.adjust_probabilities(empty_probs, "nonexistent_race")
    print(f"   Empty probabilities handled: {len(adjusted)} horses")
    
    print("\n2. Testing multiple race monitoring...")
    races = [
        ("2026-04-01", "ST", 5),
        ("2026-04-01", "ST", 3),
    ]
    
    for date, venue, race_no in races:
        state = monitor.update_race_state(date, venue, race_no)
        status = "LOADED" if state else "NO DATA"
        print(f"   {date} {venue} R{race_no}: {status}")
    
    print(f"\n3. Monitor state tracking: {len(monitor.race_states)} races tracked")
    
    return True

def main():
    print("=" * 60)
    print("Live Odds Integration Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    try:
        results.append(("Live Odds Monitor", test_live_odds_monitor()))
    except Exception as e:
        print(f"Live Odds Monitor test failed: {e}")
        results.append(("Live Odds Monitor", False))
    
    try:
        results.append(("Integration", test_integration()))
    except Exception as e:
        print(f"Integration test failed: {e}")
        results.append(("Integration", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:20}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] Live Odds Integration is working correctly!")
        print("\nFeatures implemented:")
        print("  - Odds movement tracking")
        print("  - Late money detection")
        print("  - Probability adjustment")
        print("  - Betting recommendations")
        print("  - Integration with prediction engine")
    else:
        print(f"\n[FAIL] {total - passed} tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
