"""
Post-Meeting Review Script
Automatically generates a review report after each race meeting
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def load_predictions(date, venue):
    """Load all predictions for a meeting"""
    pattern = f"data/predictions/prediction_{date}_{venue}_R*.json"
    import glob
    files = glob.glob(pattern)
    
    predictions = []
    for f in sorted(files):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                pred = json.load(file)
                predictions.append(pred)
        except:
            continue
    
    return predictions

def load_results(date, venue):
    """Load all results for a meeting"""
    pattern = f"data/results/results_{date}_{venue}_R*.json"
    import glob
    files = glob.glob(pattern)
    
    results = []
    for f in sorted(files):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                result = json.load(file)
                results.append(result)
        except:
            continue
    
    return results

def load_bet_list(date, venue):
    """Load high confidence bet list"""
    bet_file = Path(f"data/high_confidence_bets_{date}_{venue}.json")
    if bet_file.exists():
        with open(bet_file, 'r') as f:
            return json.load(f)
    return None

def analyze_meeting(date, venue):
    """Analyze meeting performance"""
    
    print("="*60)
    print(f"POST-RACE REVIEW: {date} {venue}")
    print("="*60)
    
    # Load data
    predictions = load_predictions(date, venue)
    results = load_results(date, venue)
    bet_list = load_bet_list(date, venue)
    
    if not predictions:
        print("\n[ERROR] No predictions found")
        return
    
    if not results:
        print("\n[ERROR] No results found")
        print("[INFO] Run: python auto_fetch_and_learn.py", date, venue)
        return
    
    print(f"\nTotal races: {len(predictions)}")
    print(f"Results available: {len(results)}")
    
    # Analyze high confidence bets
    if bet_list and 'bets' in bet_list:
        bets = bet_list['bets']
        print(f"\n{'='*60}")
        print("HIGH CONFIDENCE BETS PERFORMANCE")
        print('='*60)
        
        total_stake = 0
        total_return = 0
        wins = 0
        
        print(f"\nBets placed: {len(bets)}")
        print("\nDetailed Results:")
        print("-"*60)
        
        for bet in bets:
            race_id = bet['race_id']
            pick = bet['top_pick']
            confidence = bet['confidence']
            odds = bet['market_odds']
            stake = 100  # Assumed flat stake
            
            # Find result
            winner = None
            winner_dividend = 0
            
            for result in results:
                if result.get('race_id') == race_id:
                    dividends = result.get('dividends', {}).get('WIN', [])
                    if dividends:
                        winner = dividends[0].get('combination')
                        try:
                            winner_dividend = float(dividends[0].get('dividend', 0))
                        except:
                            winner_dividend = 0
                    break
            
            # Calculate result
            if winner == pick:
                payout = (winner_dividend / 10.0) * stake
                profit = payout - stake
                wins += 1
                result_str = "WIN"
            else:
                payout = 0
                profit = -stake
                result_str = "LOSS"
            
            total_stake += stake
            total_return += payout
            
            print(f"{race_id}: Horse #{pick}")
            print(f"  Confidence: {confidence*100:.1f}%")
            print(f"  Odds: {odds:.1f}")
            print(f"  Stake: ${stake}")
            print(f"  Result: {result_str}")
            if result_str == "WIN":
                print(f"  Return: ${payout:.2f}")
                print(f"  Profit: +${profit:.2f}")
            else:
                print(f"  Loss: -${stake}")
            print()
        
        # Summary
        total_profit = total_return - total_stake
        win_rate = (wins / len(bets) * 100) if len(bets) > 0 else 0
        roi = ((total_return - total_stake) / total_stake * 100) if total_stake > 0 else 0
        
        print('='*60)
        print("SUMMARY")
        print('='*60)
        print(f"\nTotal Bets: {len(bets)}")
        print(f"Wins: {wins}")
        print(f"Losses: {len(bets) - wins}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"\nTotal Stake: ${total_stake:.2f}")
        print(f"Total Return: ${total_return:.2f}")
        print(f"Total Profit: ${total_profit:.2f}")
        print(f"ROI: {roi:.1f}%")
        
        # Compare to backtest
        print(f"\n{'='*60}")
        print("COMPARISON TO BACKTEST")
        print('='*60)
        print(f"\n{'Metric':<20} {'Today':<15} {'Backtest':<15} {'Variance'}")
        print("-"*60)
        print(f"{'Win Rate':<20} {win_rate:>6.1f}% {76.5:>13.1f}% {win_rate-76.5:>12.1f}%")
        print(f"{'ROI':<20} {roi:>6.1f}% {519.1:>13.1f}% {roi-519.1:>12.1f}%")
        print(f"{'Qualifying Races':<20} {len(bets):>6} {3:>13} {len(bets)-3:>12}")
        
        # Red flags
        print(f"\n{'='*60}")
        print("RED FLAGS CHECK")
        print('='*60)
        
        red_flags = []
        if win_rate < 60:
            red_flags.append(f"Win rate ({win_rate:.1f}%) below 60% (expected 76.5%)")
        if roi < 250:
            red_flags.append(f"ROI ({roi:.1f}%) below 250% (expected 519%)")
        
        if red_flags:
            print("\n[WARNING] Issues detected:")
            for flag in red_flags:
                print(f"  - {flag}")
        else:
            print("\n[OK] Performance within expected range")
        
        # Save review
        review_data = {
            'date': date,
            'venue': venue,
            'total_bets': len(bets),
            'wins': wins,
            'win_rate': win_rate,
            'total_stake': total_stake,
            'total_return': total_return,
            'total_profit': total_profit,
            'roi': roi,
            'red_flags': red_flags
        }
        
        review_file = Path(f'data/reviews/review_{date}_{venue}.json')
        review_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(review_file, 'w') as f:
            json.dump(review_data, f, indent=2)
        
        print(f"\n[OK] Review saved to: {review_file}")
    
    else:
        print("\n[INFO] No high confidence bets were placed")
        print("[INFO] This is normal - only ~20% of meetings qualify")
    
    print("\n" + "="*60)
    print("REVIEW COMPLETE")
    print("="*60)

def main():
    if len(sys.argv) < 3:
        print("Usage: python review_after_meeting.py <date> <venue>")
        print("Example: python review_after_meeting.py 2026-04-01 ST")
        sys.exit(1)
    
    date = sys.argv[1]
    venue = sys.argv[2]
    
    analyze_meeting(date, venue)

if __name__ == '__main__':
    main()
