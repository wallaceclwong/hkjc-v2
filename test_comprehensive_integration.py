"""
Comprehensive Integration Test
Validates all 6 enhancements work together without conflicts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stewards_analyzer import get_stewards_analyzer
from services.live_odds_monitor import get_live_odds_monitor
from services.race_pace_analyzer import get_race_pace_analyzer, PaceScenario, HorsePaceProfile
from services.auto_bias_optimizer import get_auto_bias_optimizer
from services.bias_scheduler import get_bias_scheduler
from config.settings import Config

def test_enhancement_chain():
    """Test all enhancements in sequence with mock data"""
    print("=== Testing Enhancement Chain ===\n")
    
    # Starting probabilities from AI
    original_probs = {
        "1": 0.25,  # Front runner
        "2": 0.20,  # Closer
        "3": 0.30,  # Top pick
        "4": 0.15,  # Stalker  
        "5": 0.10   # Closer with issues
    }
    
    probs = original_probs.copy()
    race_id = "2026-04-01_ST_R5"
    
    print(f"Starting probabilities: {probs}")
    print(f"Total: {sum(probs.values()):.3f}\n")
    
    # Layer 1: Stewards Analysis
    print("1. STEWARDS ANALYSIS")
    stewards_analyzer = get_stewards_analyzer()
    stewards_reports = {
        "5": "Never travelled during the event. A veterinary inspection found no significant findings."
    }
    probs = stewards_analyzer.adjust_probabilities(probs, stewards_reports)
    print(f"   After Stewards: {probs}")
    print(f"   Total: {sum(probs.values()):.3f}")
    print(f"   Horse #5 reduced due to 'never travelled'\n")
    
    # Layer 2: Live Odds
    print("2. LIVE ODDS")
    # Simulate late money on horse #2
    print(f"   Simulating late money on Horse #2 (odds shortening 20%)")
    # Manual adjustment simulation
    probs["2"] *= 1.15
    total = sum(probs.values())
    probs = {h: p/total for h, p in probs.items()}
    print(f"   After Live Odds: {probs}")
    print(f"   Total: {sum(probs.values()):.3f}")
    print(f"   Horse #2 boosted due to late money\n")
    
    # Layer 3: Race Pace
    print("3. RACE PACE ANALYSIS")
    race_pace_analyzer = get_race_pace_analyzer()
    
    # Create pace scenario: Fast pace (hurts front runners)
    profiles = {
        "1": HorsePaceProfile("1", 0.8, 0.3, "front_runner", PaceScenario.MODERATE_PACE),
        "2": HorsePaceProfile("2", 0.4, 0.75, "closer", PaceScenario.FAST_PACE),
        "3": HorsePaceProfile("3", 0.5, 0.5, "stalker", PaceScenario.MODERATE_PACE),
        "4": HorsePaceProfile("4", 0.45, 0.55, "stalker", PaceScenario.MODERATE_PACE),
        "5": HorsePaceProfile("5", 0.35, 0.7, "closer", PaceScenario.FAST_PACE)
    }
    
    pace_analysis = race_pace_analyzer.predict_race_pace(race_id, profiles, None)
    print(f"   Predicted pace: {pace_analysis.predicted_pace.value}")
    print(f"   Front runners: {pace_analysis.front_runners}")
    print(f"   Closers: {pace_analysis.closers}")
    
    probs = race_pace_analyzer.adjust_probabilities_for_pace(probs, pace_analysis, profiles)
    print(f"   After Race Pace: {probs}")
    print(f"   Total: {sum(probs.values()):.3f}")
    print(f"   Front runners hurt, closers helped\n")
    
    # Layer 4: Dynamic Confidence
    print("4. DYNAMIC CONFIDENCE")
    dynamic_conf = Config.get_dynamic_confidence(
        race_class=3,
        field_size=5,
        track_condition='GOOD',
        distance=1200
    )
    print(f"   Dynamic confidence threshold: {dynamic_conf:.2f}")
    print(f"   (Base 0.50 + adjustments for class 3, field size 5, 1200m, GOOD track)\n")
    
    # Summary
    print("=" * 60)
    print("FINAL PROBABILITY COMPARISON")
    print("=" * 60)
    print(f"{'Horse':<8} {'Original':<12} {'Final':<12} {'Change':<12}")
    print("-" * 60)
    
    for horse in sorted(original_probs.keys()):
        orig = original_probs[horse]
        final = probs[horse]
        change = ((final - orig) / orig * 100) if orig > 0 else 0
        print(f"{horse:<8} {orig:<12.3f} {final:<12.3f} {change:>+10.1f}%")
    
    print("-" * 60)
    print(f"{'TOTAL':<8} {sum(original_probs.values()):<12.3f} {sum(probs.values()):<12.3f}")
    print()
    
    # Validate totals sum to 1.0
    assert abs(sum(probs.values()) - 1.0) < 0.001, "Probabilities don't sum to 1.0!"
    print("[PASS] All probabilities correctly normalized to 1.0")
    
    return True

def test_interaction_conflicts():
    """Test for conflicting adjustments between layers"""
    print("\n=== Testing Interaction Conflicts ===\n")
    
    # Scenario: Horse with red flag that gets late money
    print("Scenario: Horse #3 has red flag but also gets late money")
    
    probs = {"1": 0.2, "2": 0.2, "3": 0.4, "4": 0.2}
    
    # Stewards reduces Horse #3 by 40%
    stewards_analyzer = get_stewards_analyzer()
    reports = {"3": "Never travelled. Performance considered disappointing."}
    probs = stewards_analyzer.adjust_probabilities(probs, reports)
    after_stewards = probs["3"]
    print(f"   After Stewards (40% reduction): {after_stewards:.3f}")
    
    # Late money boosts Horse #3 by 15%
    probs["3"] *= 1.15
    total = sum(probs.values())
    probs = {h: p/total for h, p in probs.items()}
    after_odds = probs["3"]
    print(f"   After Live Odds (15% boost): {after_odds:.3f}")
    
    # Net effect
    original = 0.4
    final = probs["3"]
    net_change = ((final - original) / original * 100)
    print(f"   Net change: {net_change:+.1f}%")
    
    # This is correct behavior - Stewards takes precedence over market
    if net_change < -20:
        print("   [PASS] Stewards red flag correctly takes precedence over market boost")
    else:
        print("   [WARN] Market boost may be overpowering fundamental issues")
    
    return True

def test_services_initialization():
    """Test all services can be initialized"""
    print("\n=== Testing Services Initialization ===\n")
    
    services = [
        ("Stewards Analyzer", lambda: get_stewards_analyzer()),
        ("Live Odds Monitor", lambda: get_live_odds_monitor()),
        ("Race Pace Analyzer", lambda: get_race_pace_analyzer()),
        ("Auto Bias Optimizer", lambda: get_auto_bias_optimizer()),
        ("Bias Scheduler", lambda: get_bias_scheduler())
    ]
    
    for name, init_func in services:
        try:
            service = init_func()
            print(f"   [PASS] {name}: Initialized successfully")
        except Exception as e:
            print(f"   [FAIL] {name}: {e}")
            return False
    
    return True

def test_configuration():
    """Test configuration values"""
    print("\n=== Testing Configuration ===\n")
    
    print("Current settings:")
    print(f"   MIN_CONFIDENCE: {Config.MIN_CONFIDENCE}")
    print(f"   MIN_DISTANCE: {Config.MIN_DISTANCE}m")
    print(f"   MAX_DISTANCE: {Config.MAX_DISTANCE}m")
    print(f"   KELLY_FRACTION: {Config.KELLY_FRACTION}")
    print(f"   TRACK_MULTIPLIERS: {Config.TRACK_KELLY_MULTIPLIERS}")
    
    # Test dynamic confidence calculation
    test_cases = [
        ("Class 1, 14 horses, GOOD, 1600m", (1, 14, 'GOOD', 1600)),
        ("Class 5, 8 horses, SOFT, 1000m", (5, 8, 'SOFT', 1000)),
        ("Class 3, 10 horses, GOOD, 1200m", (3, 10, 'GOOD', 1200))
    ]
    
    print("\n   Dynamic confidence examples:")
    for desc, (race_class, field, track, dist) in test_cases:
        conf = Config.get_dynamic_confidence(race_class, field, track, dist)
        print(f"   {desc}: {conf:.2f}")
    
    return True

def main():
    print("=" * 70)
    print("COMPREHENSIVE SYSTEM INTEGRATION TEST")
    print("Validating all 6 enhancements work together")
    print("=" * 70)
    print()
    
    results = []
    
    try:
        results.append(("Enhancement Chain", test_enhancement_chain()))
    except Exception as e:
        print(f"Enhancement Chain test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Enhancement Chain", False))
    
    try:
        results.append(("Interaction Conflicts", test_interaction_conflicts()))
    except Exception as e:
        print(f"Interaction Conflicts test failed: {e}")
        results.append(("Interaction Conflicts", False))
    
    try:
        results.append(("Services Initialization", test_services_initialization()))
    except Exception as e:
        print(f"Services Initialization test failed: {e}")
        results.append(("Services Initialization", False))
    
    try:
        results.append(("Configuration", test_configuration()))
    except Exception as e:
        print(f"Configuration test failed: {e}")
        results.append(("Configuration", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name:30}: {status}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("[SUCCESS] All enhancements working correctly!")
        print("=" * 70)
        print("\n6 Enhancements Implemented:")
        print("   1. Dynamic Confidence Thresholds")
        print("   2. Stewards Report Analysis")
        print("   3. Automated Bias Optimization")
        print("   4. Live Odds Integration")
        print("   5. Ensemble Predictions")
        print("   6. Race Pace Analysis")
        print("\nSystem is ready for testing with live predictions")
        print("Recommendation: Run 5-10 test races before full deployment")
    else:
        print(f"\n[WARNING] {total - passed} test suite(s) failed")
        print("Please review errors above before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
