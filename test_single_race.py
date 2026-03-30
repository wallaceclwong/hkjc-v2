import json

# Load the fixed result
with open('c:/Users/ASUS/hkjc/data/results/results_2026-03-29_ST_R1.json', 'r') as f:
    result = json.load(f)

# Load the prediction
with open('c:/Users/ASUS/hkjc/data/predictions/prediction_2026-03-29_ST_R1.json', 'r') as f:
    pred = json.load(f)

print("=== RESULTS ===")
print(f"Winner: {result['results'][0]['horse_no']}")
print(f"WIN dividends: {result.get('dividends', {}).get('WIN', [])}")

print("\n=== PREDICTION ===")
print(f"Recommended bet: {pred.get('recommended_bet')}")
print(f"Kelly stakes: {pred.get('kelly_stakes', {})}")

# Calculate actual ROI
kelly_stakes = pred.get('kelly_stakes', {})
total_stake = sum(kelly_stakes.values())
total_return = 0

winner = result['results'][0]['horse_no']
if winner in kelly_stakes:
    # Find dividend
    for div in result.get('dividends', {}).get('WIN', []):
        if div.get('combination') == winner:
            dividend = float(div['dividend'])
            stake = kelly_stakes[winner]
            total_return = (dividend / 10.0) * stake
            print(f"\nWIN! Stake: ${stake}, Dividend: ${dividend}, Return: ${total_return}")
            break

roi = ((total_return - total_stake) / total_stake * 100) if total_stake > 0 else -100
print(f"\nTotal stake: ${total_stake}")
print(f"Total return: ${total_return}")
print(f"ROI: {roi:.1f}%")
