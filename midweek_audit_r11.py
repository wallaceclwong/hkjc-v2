import asyncio
import json
import pandas as pd
from pathlib import Path
from consensus_agent import consensus_agent
from telegram_service import telegram_service

async def run_midweek_audit():
    # 1. Load Data
    race_file = Path('/root/ultimate_engine/data/racecard_20260406_R11.json')
    if not race_file.exists(): 
        print('Error: Racecard not found.')
        return
        
    with open(race_file) as f:
        data = json.load(f)
        
    df = pd.DataFrame(data['horses'])
    
    # 2. Cleanup Data
    # Filter out placeholder entries like 'WFA'
    df = df[df['horse_name'] != 'WFA'].copy()
    
    # Map the JSON keys to what the ConsensusAgent expects
    df = df.rename(columns={
        "saddle_number": "horse_no",
        "jockey": "jockey_name",
        "trainer": "trainer_name"
    }).copy()
    
    # Pre-fill mandatory numerical columns for the agent
    df['win_odds'] = 10.0 # Mock current odds
    df['fair_odds'] = 6.5  # Mock model fair odds
    df['value_mult'] = 1.54 # Mock EV
    df['rank'] = 1 # Mock rank
    
    print(f"Pre-flight columns: {df.columns.tolist()}")
    print(f"Horses available: {df['horse_no'].tolist()}")
    
    # Minimal data formatting for the agent
    df['distance'] = data.get('distance', 2000)
    df['track_type'] = data.get('track_type', 'Turf')
    df['venue'] = 'ST'
    df['race_id'] = data.get('race_id', '2026-04-06_ST_R11')
    
    h_no = "1" # AERODYNAMICS
    
    # 3. Run Audit
    target_matches = df[df['horse_no'].astype(str) == str(h_no)]
    if len(target_matches) == 0:
        print(f"Error: Horse #{h_no} not found in cleaned data.")
        return
        
    print(f"Starting Deep-Dive for {data.get('race_id')} (Target Name: {target_matches['horse_name'].iloc[0]})...")
    verdict, reasoning = await consensus_agent.get_consensus(df, h_no)
    
    # 3. Report
    summary = f"--- MID-WEEK AUDIT: {data.get('race_id')} ---\n🎯 Target: AERODYNAMICS (#{h_no})\n🧠 Verdict: {verdict}\n📝 Logic: {reasoning}"
    print(summary)
    
    # 4. Notify Telegram
    header = f"💎 *MID-WEEK STRATEGIC AUDIT: Apr 6*"
    body = (
        f"🎯 *Target:* AERODYNAMICS (#4)\n"
        f"🚀 *Verdict:* {verdict}\n\n"
        f"🧠 *Lunar Leap Logic:*\n{reasoning}"
    )
    await telegram_service.send_message(f"{header}\n{body}")

if __name__ == '__main__':
    asyncio.run(run_midweek_audit())
