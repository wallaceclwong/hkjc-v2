import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def construct_training_prompt(data):
    """
    Replicates the prompt structure from PredictionEngine._construct_prompt 
    but for training data generation.
    """
    racecard = data.get('racecard', {})
    results = data.get('results', {})
    analytical = data.get('analytical', {})
    odds = data.get('odds', {})
    synergy = data.get('synergy', {})
    hidden_form = data.get('hidden_form', {})
    weather_intel = data.get('weather_intel', {})
    pedigree_intel = data.get('pedigree_intel', {})
    
    racecard_horses = racecard.get('horses', [])
    horse_nos = [str(h.get('saddle_number') or h.get('horse_no') or '') for h in racecard_horses]
    horse_nos = [n for n in horse_nos if n]
    horse_nos_str = ", ".join(horse_nos)

    prompt = f"""
Act as a professional Hong Kong horse racing analyst. Your task is to analyze race data and provide a winning prediction.

### RACE CONTEXT
Race ID: {racecard.get('id', 'N/A')}
Distance: {racecard.get('distance', 'N/A')}m
Track: {racecard.get('track_type', 'N/A')}
Class: {racecard.get('race_class', 'N/A')}

### HORSE ENTRIES (Race Card)
{json.dumps(racecard_horses, indent=2)}

### ANALYTICAL DATA (Sectional Times & Positions)
{json.dumps(analytical, indent=2)}

### MARKET ODDS
{json.dumps(odds, indent=2)}

### STEWARDS' REPORTS & INCIDENTS (Human Context)
{json.dumps(results.get('incidents', []), indent=2)}

### BARRIER TRIALS (Pre-race Fitness)
{json.dumps(analytical.get('trials', []), indent=2)}

### HORSE NUMBERS TO PREDICT
{horse_nos_str}

### JOCKEY-TRAINER SYNERGY STATS
{json.dumps(synergy, indent=2)}

### HIDDEN FORM & FORGIVENESS TAGS
{json.dumps(hidden_form, indent=2)}

### WEATHER INTELLIGENCE
{json.dumps(weather_intel, indent=2)}

### PEDIGREE INTELLIGENCE
{json.dumps(pedigree_intel, indent=2)}
"""
    return prompt.strip()

def construct_target_response(data):
    """
    Creates the 'ideal' model response based on actual race results.
    """
    results = data.get('results', {}).get('results', [])
    incidents = data.get('results', {}).get('incidents', [])
    stewards_report = data.get('results', {}).get('stewards_report', 'None')
    
    # 1. Determine the winner
    winner_no = ""
    winner_name = ""
    for r in results:
        placing = str(r.get('plc') or r.get('placing') or '')
        if placing == "1":
            winner_no = str(r.get('horse_no'))
            winner_name = r.get('horse_name', 'Winner')
            break
            
    # 2. Build probabilities (1.0 for winner, 0.0 for others for strict SFT)
    probabilities = {}
    racecard_horses = data.get('racecard', {}).get('horses', [])
    for h in racecard_horses:
        h_no = str(h.get('saddle_number') or h.get('horse_no') or '')
        if h_no:
            probabilities[h_no] = 1.0 if h_no == winner_no else 0.0

    # 3. Build Analysis Markdown
    analysis = f"The race was won by **{winner_name}** (No. {winner_no}).\n\n"
    if stewards_report:
        analysis += f"### Stewards' Observations:\n{stewards_report}\n\n"
    
    target = {
        "confidence_score": 0.95,
        "is_best_bet": True if winner_no else False,
        "recommended_bet": f"WIN {winner_no}" if winner_no else "NO BET",
        "probabilities": probabilities,
        "analysis_markdown": analysis
    }
    return json.dumps(target, indent=2)

def prepare_tuning_data(limit=50, output_file="data/tuning_canary_50.jsonl"):
    base_dir = Path("c:/Users/ASUS/hkjc")
    results_dir = base_dir / "data/results"
    data_dir = base_dir / "data"
    
    result_files = sorted(list(results_dir.glob("results_*.json")), reverse=True)
    
    samples = []
    count = 0
    
    print(f"Sampling {limit} races for tuning...")
    
    for rf in result_files:
        if count >= limit: break
        
        try:
            # Extract ID components: results_2026-03-22_ST_R1.json
            parts = rf.stem.split("_")
            date_str = parts[1]
            venue = parts[2]
            race_no = parts[3]
            
            # Load all parts
            with open(rf, 'r', encoding='utf-8') as f:
                res_data = json.load(f)
            
            # Find racecard
            date_compact = date_str.replace("-", "")
            rc_file = data_dir / f"racecard_{date_compact}_{race_no}.json"
            
            if rc_file.exists():
                with open(rc_file, 'r', encoding='utf-8') as f:
                    rc_data = json.load(f)
            else:
                # Reconstruct skeleton from results (matches PredictionEngine logic)
                skeleton_horses = []
                for r in res_data.get("results", []):
                    skeleton_horses.append({
                        "saddle_number": int(r["horse_no"]) if r["horse_no"].isdigit() else 0,
                        "horse_name": r.get("brand_id", ""), 
                        "jockey": r.get("jockey", ""),
                        "trainer": r.get("trainer", ""),
                        "weight": 133,
                    })
                rc_data = {
                    "id": f"{date_str}_{race_no}",
                    "distance": 1200, 
                    "horses": skeleton_horses
                }
                
            # Find analytical
            ana_file = data_dir / "analytical" / f"analytical_{date_str}_{venue}_{race_no}.json"
            with open(ana_file, 'r', encoding='utf-8') as f:
                ana_data = json.load(f)
                
            data = {
                "racecard": rc_data,
                "results": res_data,
                "analytical": ana_data,
                "odds": {}, # Placeholder
                "synergy": {},
                "hidden_form": {},
                "weather_intel": {},
                "pedigree_intel": {}
            }
            
            # Construct JSONL Entry
            entry = {
                "systemInstruction": {
                    "role": "system",
                    "parts": [{"text": "Act as a professional Hong Kong horse racing analyst. Analyze race data and provide a winning prediction."}]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": construct_training_prompt(data)}]
                    },
                    {
                        "role": "model",
                        "parts": [{"text": construct_target_response(data)}]
                    }
                ]
            }
            
            samples.append(entry)
            count += 1
            if count % 10 == 0: print(f"Processed {count}/{limit} samples...")
            
        except Exception as e:
            # print(f"Error processing {rf.name}: {e}")
            continue

    with open(output_file, 'w', encoding='utf-8') as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
            
    print(f"Success! Created {output_file} with {len(samples)} examples.")

if __name__ == "__main__":
    prepare_tuning_data(limit=10000, output_file="data/tuning_full_8year.jsonl")
