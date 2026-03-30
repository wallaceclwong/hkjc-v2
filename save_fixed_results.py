import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.results_ingest import ResultsIngest

async def save_fixed_results():
    ingest = ResultsIngest()
    result = await ingest.fetch_results('2026-03-29', 'ST', 1)
    
    # Save with dividends
    filename = 'c:/Users/ASUS/hkjc/data/results/results_2026-03-29_ST_R1_fixed.json'
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    
    win_dividends = result.get('dividends', {}).get('WIN', [])
    print(f"Saved with {len(win_dividends)} WIN dividends")
    
    if win_dividends:
        print(f"WIN dividend: {win_dividends[0]}")

if __name__ == "__main__":
    asyncio.run(save_fixed_results())
