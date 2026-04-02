"""
Test script for Automated Bias Optimizer
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auto_bias_optimizer import get_auto_bias_optimizer
from services.bias_scheduler import get_bias_scheduler, ScheduleConfig

async def test_auto_optimizer():
    """Test the auto bias optimizer"""
    print("=== Testing Auto Bias Optimizer ===\n")
    
    optimizer = get_auto_bias_optimizer()
    
    # Test 1: Get recent meetings
    print("1. Testing meeting detection...")
    meetings = await optimizer.get_recent_meetings()
    print(f"   Found {len(meetings)} recent meetings")
    for meeting in meetings[:3]:  # Show first 3
        print(f"   - {meeting.date} {meeting.venue}: {meeting.status} ({meeting.completed_races}/{meeting.total_races} races)")
    
    # Test 2: Manual optimization
    print("\n2. Testing manual optimization...")
    success = await optimizer.optimize_now(days=3)  # Use last 3 days
    print(f"   Optimization {'succeeded' if success else 'failed'}")
    
    # Test 3: Check processed meetings
    print("\n3. Testing meeting tracking...")
    print(f"   Processed meetings: {len(optimizer.processed_meetings)}")
    if optimizer.processed_meetings:
        print(f"   Last processed: {list(optimizer.processed_meetings)[-1]}")
    
    return success

def test_scheduler():
    """Test the bias scheduler"""
    print("\n=== Testing Bias Scheduler ===\n")
    
    # Create custom config for testing
    config = ScheduleConfig(
        enabled=True,
        run_after_meeting=False,  # Disable for testing
        run_daily_at=None,        # Disable for testing
        run_weekly_at=None,       # Disable for testing
        min_races_threshold=1     # Lower threshold for testing
    )
    
    scheduler = get_bias_scheduler()
    scheduler.config = config
    
    # Test 1: Status
    print("1. Testing scheduler status...")
    status = scheduler.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Running: {status['running']}")
    print(f"   Min races threshold: {status['min_races_threshold']}")
    
    # Test 2: Config update
    print("\n2. Testing config update...")
    scheduler.update_config(min_races_threshold=5)
    new_status = scheduler.get_status()
    print(f"   Updated threshold: {new_status['min_races_threshold']}")
    
    # Test 3: Restore original config
    print("\n3. Restoring original config...")
    scheduler.update_config(min_races_threshold=3, run_after_meeting=True)
    restored_status = scheduler.get_status()
    print(f"   Restored threshold: {restored_status['min_races_threshold']}")
    print(f"   Restored meeting monitoring: {restored_status['run_after_meeting']}")
    
    return True

def test_integration():
    """Test integration between optimizer and scheduler"""
    print("\n=== Testing Integration ===\n")
    
    optimizer = get_auto_bias_optimizer()
    scheduler = get_bias_scheduler()
    
    # Test 1: Check if optimizer can access bias data
    print("1. Testing bias data access...")
    try:
        biases = optimizer.rl_optimizer.load_biases()
        print(f"   Bias data loaded successfully")
        print(f"   Total samples: {biases.get('metadata', {}).get('total_samples', 0)}")
        print(f"   Last optimized: {biases.get('metadata', {}).get('last_optimized', 'Never')}")
    except Exception as e:
        print(f"   Error loading bias data: {e}")
        return False
    
    # Test 2: Check if scheduler can be configured
    print("\n2. Testing scheduler configuration...")
    try:
        scheduler.update_config(enabled=True, run_after_meeting=True)
        print("   Scheduler configured successfully")
    except Exception as e:
        print(f"   Error configuring scheduler: {e}")
        return False
    
    # Test 3: Check file paths
    print("\n3. Testing file paths...")
    paths = {
        'predictions_dir': optimizer.predictions_dir,
        'results_dir': optimizer.results_dir,
        'bias_path': optimizer.rl_optimizer.bias_path
    }
    
    for name, path in paths.items():
        exists = path.exists()
        print(f"   {name}: {path} - {'PASS' if exists else 'FAIL'}")
        if not exists and name == 'predictions_dir':
            print(f"     Creating directory...")
            path.mkdir(parents=True, exist_ok=True)
    
    return True

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Automated Bias Optimizer Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    try:
        results.append(("Auto Optimizer", await test_auto_optimizer()))
    except Exception as e:
        print(f"Auto Optimizer test failed: {e}")
        results.append(("Auto Optimizer", False))
    
    try:
        results.append(("Scheduler", test_scheduler()))
    except Exception as e:
        print(f"Scheduler test failed: {e}")
        results.append(("Scheduler", False))
    
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
        print("\nPASS All tests passed! Automated Bias Optimizer is ready.")
        print("\nTo start the scheduler:")
        print("  python scripts/start_bias_scheduler.py")
        print("\nTo run a manual optimization:")
        print("  python services/auto_bias_optimizer.py --optimize --days 7")
    else:
        print(f"\nFAIL {total - passed} tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
