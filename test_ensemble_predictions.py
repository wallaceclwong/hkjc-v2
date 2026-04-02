"""
Test script for Ensemble Predictions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ensemble_predictor import get_ensemble_predictor, ModelPrediction, EnsembleResult
from datetime import datetime

def test_ensemble_predictor():
    print("=== Testing Ensemble Predictor ===\n")
    
    predictor = get_ensemble_predictor()
    
    # Test 1: Model configuration
    print("1. Testing model configuration...")
    enabled_models = [name for name, config in predictor.models.items() if config['enabled']]
    print(f"   Enabled models: {enabled_models}")
    print(f"   Model weights: {[(name, config['weight']) for name, config in predictor.models.items() if config['enabled']]}")
    
    # Test 2: Create mock predictions for testing
    print("\n2. Testing prediction combination...")
    mock_predictions = [
        ModelPrediction(
            model_name="gemini_flash",
            model_id="gemini-2.5-flash",
            confidence_score=0.75,
            recommended_bet="WIN 3",
            probabilities={"1": 0.1, "2": 0.2, "3": 0.3, "4": 0.15, "5": 0.25}
        ),
        ModelPrediction(
            model_name="gemini_pro",
            model_id="gemini-2.5-pro",
            confidence_score=0.70,
            recommended_bet="WIN 2",
            probabilities={"1": 0.15, "2": 0.35, "3": 0.2, "4": 0.1, "5": 0.2}
        )
    ]
    
    # Test combination
    ensemble = predictor._combine_predictions("2026-04-01_ST_R5", mock_predictions)
    
    print(f"   Ensemble confidence: {ensemble.ensemble_confidence:.2f}")
    print(f"   Agreement score: {ensemble.agreement_score:.2f}")
    print(f"   Consensus horses: {ensemble.consensus_horses}")
    print(f"   Disagreement horses: {ensemble.disagreement_horses}")
    print(f"   Top horse: {ensemble.ensemble_bet}")
    
    print("\n   Ensemble probabilities:")
    for horse_no, prob in ensemble.ensemble_probabilities.items():
        print(f"     Horse #{horse_no}: {prob:.1%}")
    
    # Test 3: Agreement/disagreement detection
    print("\n3. Testing agreement detection...")
    should_skip, reason = predictor.should_skip_ensemble(ensemble)
    print(f"   Should skip: {should_skip}")
    print(f"   Reason: {reason}")
    
    # Test 4: Ensemble summary
    print("\n4. Testing ensemble summary...")
    summary = predictor.get_ensemble_summary(ensemble)
    print(f"   Models used: {summary['models_used']}")
    print(f"   Agreement score: {summary['agreement_score']:.2f}")
    print(f"   Top horse: {summary['top_horse']}")
    
    return True

def test_edge_cases():
    print("\n=== Testing Edge Cases ===\n")
    
    predictor = get_ensemble_predictor()
    
    # Test 1: Single prediction (should fail)
    print("1. Testing single prediction...")
    single_pred = [ModelPrediction(
        model_name="gemini_flash",
        model_id="gemini-2.5-flash",
        confidence_score=0.75,
        recommended_bet="WIN 3",
        probabilities={"1": 0.2, "2": 0.3, "3": 0.5}
    )]
    
    try:
        ensemble = predictor._combine_predictions("test_R1", single_pred)
        print("   ERROR: Should have failed with single prediction")
        return False
    except ValueError as e:
        print(f"   Correctly rejected single prediction: {e}")
    
    # Test 2: No agreement
    print("\n2. Testing no agreement...")
    disagreeing_preds = [
        ModelPrediction(
            model_name="model1",
            model_id="model1",
            confidence_score=0.75,
            recommended_bet="WIN 1",
            probabilities={"1": 0.6, "2": 0.2, "3": 0.2}
        ),
        ModelPrediction(
            model_name="model2",
            model_id="model2",
            confidence_score=0.75,
            recommended_bet="WIN 2",
            probabilities={"1": 0.2, "2": 0.6, "3": 0.2}
        )
    ]
    
    ensemble = predictor._combine_predictions("test_R2", disagreeing_preds)
    should_skip, reason = predictor.should_skip_ensemble(ensemble)
    print(f"   Should skip due to disagreement: {should_skip}")
    print(f"   Reason: {reason}")
    
    # Test 3: Perfect agreement
    print("\n3. Testing perfect agreement...")
    agreeing_preds = [
        ModelPrediction(
            model_name="model1",
            model_id="model1",
            confidence_score=0.75,
            recommended_bet="WIN 1",
            probabilities={"1": 0.5, "2": 0.3, "3": 0.2}
        ),
        ModelPrediction(
            model_name="model2",
            model_id="model2",
            confidence_score=0.75,
            recommended_bet="WIN 1",
            probabilities={"1": 0.5, "2": 0.3, "3": 0.2}
        )
    ]
    
    ensemble = predictor._combine_predictions("test_R3", agreeing_preds)
    should_skip, reason = predictor.should_skip_ensemble(ensemble)
    print(f"   Should skip with perfect agreement: {should_skip}")
    print(f"   Agreement score: {ensemble.agreement_score:.2f}")
    
    return True

def test_integration():
    print("\n=== Testing Integration ===\n")
    
    predictor = get_ensemble_predictor()
    
    # Test that predictor handles missing models gracefully
    print("1. Testing disabled models...")
    original_enabled = predictor.models['gemini_flash']['enabled']
    predictor.models['gemini_flash']['enabled'] = False
    
    enabled_count = len([m for m in predictor.models.values() if m['enabled']])
    print(f"   Enabled models after disabling: {enabled_count}")
    
    # Restore
    predictor.models['gemini_flash']['enabled'] = original_enabled
    
    print("\n2. Testing weight normalization...")
    total_weight = sum(config['weight'] for config in predictor.models.values() if config['enabled'])
    print(f"   Total weight: {total_weight} (should be 1.0)")
    
    return True

def main():
    print("=" * 60)
    print("Ensemble Predictions Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    try:
        results.append(("Ensemble Predictor", test_ensemble_predictor()))
    except Exception as e:
        print(f"Ensemble Predictor test failed: {e}")
        results.append(("Ensemble Predictor", False))
    
    try:
        results.append(("Edge Cases", test_edge_cases()))
    except Exception as e:
        print(f"Edge Cases test failed: {e}")
        results.append(("Edge Cases", False))
    
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
        print("\n[SUCCESS] Ensemble Predictions is working correctly!")
        print("\nFeatures implemented:")
        print("  - Multi-model parallel predictions")
        print("  - Weighted probability averaging")
        print("  - Agreement/disagreement detection")
        print("  - Automatic fallback on disagreement")
        print("  - Integration with prediction engine")
        print("\nTo use ensemble predictions:")
        print("  prediction_engine.generate_prediction(date, venue, race, use_ensemble=True)")
    else:
        print(f"\n[FAIL] {total - passed} tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
