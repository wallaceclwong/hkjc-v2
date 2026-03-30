"""
Test WeatherNext Integration - Direct Path
"""
import sys
from pathlib import Path

print("="*60)
print("WEATHERNEXT DIRECT TEST")
print("="*60)

# Direct path to WeatherNext
wn_path = Path("c:/Users/ASUS/weathernext_pro/src")

print(f"\nChecking: {wn_path}")

if wn_path.exists():
    print("[OK] WeatherNext directory exists")
    
    # List files
    files = list(wn_path.glob("*.py"))
    print(f"\nPython files found: {len(files)}")
    for f in files[:5]:
        print(f"  - {f.name}")
    
    # Check for v2_engine
    v2_engine = wn_path / "v2_engine.py"
    if v2_engine.exists():
        print(f"\n[OK] v2_engine.py exists ({v2_engine.stat().st_size} bytes)")
        
        # Try to import
        print("\n[INFO] Attempting import...")
        sys.path.insert(0, str(wn_path))
        
        try:
            from v2_engine import get_track_forecast
            print("[OK] Successfully imported get_track_forecast")
            
            # Test the function
            print("\n[INFO] Testing forecast for Sha Tin...")
            try:
                result = get_track_forecast("ST")
                
                if result:
                    print(f"[OK] Forecast returned")
                    print(f"Type: {type(result)}")
                    
                    if isinstance(result, dict):
                        print(f"Keys: {list(result.keys())[:5]}")
                    elif isinstance(result, str):
                        print(f"Content preview: {result[:200]}")
                else:
                    print("[WARN] Function returned None")
                    
            except Exception as e:
                print(f"[ERROR] Function call failed: {e}")
                
        except ImportError as e:
            print(f"[FAIL] Import error: {e}")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print("[FAIL] v2_engine.py not found")
        print("\nAvailable files:")
        for f in wn_path.glob("*.py"):
            print(f"  - {f.name}")
else:
    print("[FAIL] WeatherNext directory does not exist")
    print(f"\nChecked path: {wn_path.absolute()}")

print("\n" + "="*60)
print("INTEGRATION STATUS")
print("="*60)

# Check if prediction engine uses it
pred_engine = Path("services/prediction_engine.py")
if pred_engine.exists():
    with open(pred_engine, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_weather = "weather" in content.lower()
    has_forecast = "forecast" in content.lower()
    
    print(f"\nPrediction Engine:")
    print(f"  References 'weather': {has_weather}")
    print(f"  References 'forecast': {has_forecast}")
    
    if has_weather or has_forecast:
        print("  [OK] Weather integration present")
    else:
        print("  [WARN] Weather integration not found")

print("\n" + "="*60)
