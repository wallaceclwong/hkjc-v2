"""
Test script for Stewards Report Analyzer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stewards_analyzer import get_stewards_analyzer

def test_stewards_analyzer():
    print("=== Testing Stewards Report Analyzer ===\n")
    
    analyzer = get_stewards_analyzer()
    
    # Test cases with different red flag scenarios
    test_cases = [
        {
            "horse_no": "3",
            "report": "Z Purton reported that after his mount was slow to begin it never travelled at any stage during the event. A veterinary inspection immediately following the race did not show any significant findings. The performance of ONLY U was considered disappointing as compared to its previous race starts.",
            "expected_reduction": 0.6,  # Performance issues (40%) + Starting issues (20%)
            "expected_critical": []  # Neither is critical severity
        },
        {
            "horse_no": "7",
            "report": "A veterinary inspection immediately following the race found that horse to have bled from both nostrils. Before being allowed to race again, RACINGRACE will be required to perform satisfactorily in a barrier trial and be subjected to an official veterinary examination.",
            "expected_reduction": 0.8,  # Physical problems (60%) + Future restrictions (50%) capped at 80%
            "expected_critical": ["physical_problems"]  # Only physical_problems is critical
        },
        {
            "horse_no": "5",
            "report": "Began only fairly. Raced very wide and without cover for the majority of the event.",
            "expected_reduction": 0.3,  # Starting issues (20%) + Interference issues (10%)
            "expected_critical": []
        },
        {
            "horse_no": "12",
            "report": "No report.",
            "expected_reduction": 0.0,
            "expected_critical": []
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        print(f"Testing Horse #{test['horse_no']}:")
        print(f"  Report: {test['report'][:80]}...")
        
        result = analyzer.analyze_horse_report(test['horse_no'], test['report'])
        
        # Check confidence reduction
        actual_reduction = result['total_confidence_reduction']
        expected_reduction = test['expected_reduction']
        
        if abs(actual_reduction - expected_reduction) < 0.05:
            print(f"  PASS Confidence reduction: {actual_reduction:.1%} (expected {expected_reduction:.1%})")
        else:
            print(f"  FAIL Confidence reduction: {actual_reduction:.1%} (expected {expected_reduction:.1%})")
            all_passed = False
        
        # Check critical flags
        actual_critical = set(result['critical_flags'])
        expected_critical = set(test['expected_critical'])
        
        if actual_critical == expected_critical:
            print(f"  PASS Critical flags: {actual_critical}")
        else:
            print(f"  FAIL Critical flags: {actual_critical} (expected {expected_critical})")
            all_passed = False
        
        print(f"  Recommendation: {result['recommendation']}")
        print()
    
    # Test probability adjustment
    print("=== Testing Probability Adjustment ===")
    test_probs = {"1": 0.3, "2": 0.25, "3": 0.2, "4": 0.15, "5": 0.1}
    test_reports = {
        "1": "No report.",
        "2": "Began only fairly.",
        "3": "Never travelled during the event.",
        "4": "A veterinary inspection found the horse to have bled from both nostrils.",
        "5": "Raced wide without cover."
    }
    
    adjusted_probs = analyzer.adjust_probabilities(test_probs, test_reports)
    
    print("Original probabilities:")
    for horse, prob in test_probs.items():
        print(f"  Horse #{horse}: {prob:.1%}")
    
    print("\nAdjusted probabilities:")
    for horse, prob in adjusted_probs.items():
        original = test_probs[horse]
        if prob < original:
            reduction = (original - prob) / original
            print(f"  Horse #{horse}: {prob:.1%} ({reduction:.1%} reduction)")
        else:
            print(f"  Horse #{horse}: {prob:.1%} (no change)")
    
    # Verify total still sums to 1.0
    total = sum(adjusted_probs.values())
    print(f"\nTotal probability: {total:.3f} (should be 1.000)")
    
    if abs(total - 1.0) < 0.001:
        print("PASS Probabilities correctly renormalized")
    else:
        print("FAIL Probabilities not properly renormalized")
        all_passed = False
    
    print("\n=== Test Summary ===")
    if all_passed:
        print("PASS All tests passed!")
        print("Stewards Report Analyzer is working correctly.")
    else:
        print("FAIL Some tests failed.")
        print("Please check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    test_stewards_analyzer()
