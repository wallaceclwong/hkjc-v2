import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.results_ingest import ResultsIngest

async def test_dividends():
    ingest = ResultsIngest()
    result = await ingest.fetch_results('2026-03-29', 'ST', 1)
    
    print("=== Dividends for Race 1 ===")
    dividends = result.get('dividends', {})
    for pool, items in dividends.items():
        print(f"\n{pool}:")
        for item in items:
            print(f"  {item.get('combination')}: ${item.get('dividend')}")
    
    # Also check winner
    results = result.get('results', [])
    if results:
        winner = results[0].get('horse_no')
        print(f"\nWinner: Horse {winner}")

if __name__ == "__main__":
    asyncio.run(test_dividends())
