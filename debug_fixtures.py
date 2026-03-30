import json
from datetime import datetime, timedelta

# Load fixtures
with open('c:/Users/ASUS/hkjc/data/fixtures_2026.json', 'r') as f:
    fixtures = json.load(f)

print("All fixtures:")
for f in fixtures:
    print(f"  {f['date']} - {f['venue']}")

# Check upcoming meetings
now = datetime.now().date()
print(f"\nToday: {now}")

print("\nChecking next 7 days:")
for day_offset in range(7):
    d = now + timedelta(days=day_offset)
    d_str = d.strftime("%Y-%m-%d")
    d_fmt = d.strftime("%d/%m/%Y")
    print(f"\n{d.strftime('%A')} {d_str} ({d_fmt})")
    
    # Check if in fixtures
    found = False
    for f in fixtures:
        if f["date"] == d_fmt:
            print(f"  Found: {f['venue']}")
            found = True
            break
    
    if not found:
        print("  Not in fixtures")
