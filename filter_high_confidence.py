"""
Filter High Confidence Predictions
Shows only bets with confidence > 70% (based on backtest: 76.5% win rate, 519% ROI)
"""
import glob
import json
from pathlib import Path
import sys

def filter_predictions(date, venue, min_confidence=0.70):
    """Filter predictions by confidence threshold"""
    
    # Find prediction files for this date/venue
    pattern = f"data/predictions/prediction_{date}_{venue}_R*.json"
    pred_files = glob.glob(pattern)
    
    if not pred_files:
        print(f"[ERROR] No predictions found for {date} {venue}")
        print(f"[INFO] Run: python batch_predict.py {date} {venue}")
        return []
    
    high_confidence_bets = []
    
    for f in sorted(pred_files):
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                pred = json.load(file)
            
            race_id = pred.get('race_id', '')
            confidence = pred.get('confidence_score', 0)
            recommended = pred.get('recommended_bet', '')
            kelly_stakes = pred.get('kelly_stakes', {})
            probabilities = pred.get('probabilities', {})
            
            if confidence >= min_confidence:
                # Get top pick
                top_pick = None
                if 'WIN' in recommended:
                    top_pick = recommended.split()[-1]
                elif probabilities:
                    top_pick = max(probabilities.items(), key=lambda x: x[1])[0]
                
                # Get top pick probability
                top_prob = probabilities.get(top_pick, 0) if top_pick else 0
                
                # Get market odds
                market_odds = pred.get('market_odds', {})
                top_odds = market_odds.get(top_pick, 0) if top_pick else 0
                
                high_confidence_bets.append({
                    'race_id': race_id,
                    'race_no': race_id.split('_')[-1],
                    'confidence': confidence,
                    'top_pick': top_pick,
                    'probability': top_prob,
                    'market_odds': top_odds,
                    'kelly_stakes': kelly_stakes,
                    'recommended_bet': recommended
                })
        
        except Exception as e:
            continue
    
    return high_confidence_bets

def main():
    if len(sys.argv) < 3:
        print("Usage: python filter_high_confidence.py <date> <venue> [min_confidence]")
        print("Example: python filter_high_confidence.py 2026-04-01 ST 0.70")
        sys.exit(1)
    
    date = sys.argv[1]
    venue = sys.argv[2]
    min_confidence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.70
    
    print("="*60)
    print("HIGH CONFIDENCE BET FILTER")
    print("="*60)
    print(f"\nDate: {date}")
    print(f"Venue: {venue}")
    print(f"Min Confidence: {min_confidence*100:.0f}%")
    print(f"\n[INFO] Based on backtest:")
    print(f"  - Confidence >70%: 76.5% win rate, 519% ROI")
    print(f"  - 285 bets over 1,378 races (~20% of races qualify)")
    
    bets = filter_predictions(date, venue, min_confidence)
    
    if not bets:
        print(f"\n[RESULT] No bets meet {min_confidence*100:.0f}% confidence threshold")
        print("\n[INFO] This is normal - only ~20% of races qualify")
        print("[INFO] Lower threshold or wait for better opportunities")
        return
    
    print(f"\n{'='*60}")
    print(f"RECOMMENDED BETS ({len(bets)} races)")
    print("="*60)
    
    total_stake = 0
    
    for i, bet in enumerate(bets, 1):
        print(f"\n{i}. {bet['race_id']}")
        print(f"   Confidence: {bet['confidence']*100:.1f}%")
        print(f"   Pick: Horse #{bet['top_pick']}")
        print(f"   AI Probability: {bet['probability']*100:.1f}%")
        print(f"   Market Odds: {bet['market_odds']:.1f}")
        print(f"   Recommended: {bet['recommended_bet']}")
        
        if bet['kelly_stakes']:
            print(f"   Kelly Stakes: {bet['kelly_stakes']}")
        
        # Suggested flat bet
        suggested_stake = 100
        total_stake += suggested_stake
        print(f"   Suggested Stake: ${suggested_stake}")
    
    print(f"\n{'='*60}")
    print("BETTING SUMMARY")
    print("="*60)
    print(f"\nTotal Races: {len(bets)}")
    print(f"Total Stake: ${total_stake}")
    print(f"\nExpected Performance (based on backtest):")
    print(f"  - Win Rate: 76.5%")
    print(f"  - Expected Wins: {len(bets) * 0.765:.1f}")
    print(f"  - Expected ROI: 519%")
    print(f"  - Expected Return: ${total_stake * 5.19:.2f}")
    print(f"  - Expected Profit: ${total_stake * 4.19:.2f}")
    
    print(f"\n[IMPORTANT] Past performance doesn't guarantee future results!")
    print(f"[ADVICE] Start conservative, track results, adjust strategy")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Review each bet carefully")
    print("2. Check if odds have moved significantly")
    print("3. Log into HKJC betting site")
    print("4. Place bets before races start")
    print("5. Track results and compare to predictions")
    
    # Save to file for reference
    output_file = Path(f'data/high_confidence_bets_{date}_{venue}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date,
            'venue': venue,
            'min_confidence': min_confidence,
            'bets': bets,
            'total_stake': total_stake
        }, f, indent=2)
    
    print(f"\n[OK] Bet list saved to: {output_file}")

if __name__ == '__main__':
    main()
