"""
Test WeatherNext Integration
"""
import sys
import os
from pathlib import Path

print("="*60)
print("WEATHERNEXT INTEGRATION TEST")
print("="*60)

# Check if WeatherNext exists
wn_path = os.getenv("WEATHERNEXT_PATH")
if not wn_path:
    sibling_wn = Path("c:/Users/ASUS/weathernext_pro/src")
    if sibling_wn.exists():
        wn_path = str(sibling_wn)

print(f"\nWeatherNext Path: {wn_path}")

if wn_path and Path(wn_path).exists():
    print("[OK] WeatherNext directory found")
    
    # Check for key files
    v2_engine = Path(wn_path) / "v2_engine.py"
    if v2_engine.exists():
        print("[OK] v2_engine.py exists")
    else:
        print("[FAIL] v2_engine.py not found")
    
    # Try to import
    print("\n[INFO] Attempting to import WeatherNext...")
    try:
        sys.path.append(wn_path)
        from v2_engine import get_track_forecast
        
        print("[OK] Successfully imported get_track_forecast")
        
        # Try to get a forecast
        print("\n[INFO] Testing forecast function...")
        try:
            # Test with Sha Tin
            forecast = get_track_forecast("ST")
            
            if forecast:
                print(f"[OK] Forecast returned: {type(forecast)}")
                print(f"\nForecast data:")
                if isinstance(forecast, dict):
                    for key, value in list(forecast.items())[:5]:
                        print(f"  {key}: {value}")
                else:
                    print(f"  {str(forecast)[:200]}")
            else:
                print("[WARN] Forecast returned None/empty")
                
        except Exception as e:
            print(f"[ERROR] Forecast function failed: {e}")
            
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        
else:
    print("[FAIL] WeatherNext directory not found")
    print("\nExpected locations:")
    print("  1. Environment variable: WEATHERNEXT_PATH")
    print("  2. Sibling directory: c:/Users/ASUS/weathernext_pro/src")

print("\n" + "="*60)
print("Integration Status:")

# Check if it's used in prediction engine
pred_engine = Path("c:/Users/ASUS/hkjc/services/prediction_engine.py")
if pred_engine.exists():
    with open(pred_engine, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "weathernext" in content.lower() or "get_track_forecast" in content:
        print("  [OK] WeatherNext referenced in prediction_engine.py")
    else:
        print("  [WARN] WeatherNext not used in prediction_engine.py")

print("="*60)
