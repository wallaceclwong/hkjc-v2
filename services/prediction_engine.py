import json
import os
import sys
from google import genai
from google.genai import types
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path to allow imports from config and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from models.schemas import Prediction
from services.firestore_service import FirestoreService
# Stubs for missing services (Temporary for verification)
class SynergyService:
    def get_synergy(self, j, t): return {}
class StewardAnalyser:
    def get_hidden_form(self, b): return []
class PedigreeService:
    async def get_enriched_pedigree(self, h): return {}
class KellyCriterion:
    def __init__(self, bankroll: float = 10000.0, fractional_kelly: float = 0.1):
        self.bankroll = bankroll
        self.fractional_kelly = fractional_kelly

    def calculate_race_stakes(self, probabilities: Dict[str, float], market_odds: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates recommended stakes for each horse in a race.
        Kelly Formula: f* = (p*o - 1) / (o - 1)
        where:
        - p is the probability of winning
        - o is the decimal odds
        """
        stakes = {}
        if not market_odds:
            return stakes

        for horse_no, p in probabilities.items():
            # Ensure horse_no is a string for lookup
            h_id = str(horse_no)
            o = market_odds.get(h_id)
            
            if not o or o <= 1.0:
                continue

            # f_star = (p * o - 1) / (o - 1)
            f_star = (p * o - 1) / (o - 1)
            
            if f_star > 0:
                # Apply fractional Kelly and Multiply by bankroll
                stake = self.bankroll * self.fractional_kelly * f_star
                
                # Round to nearest dollar
                if stake >= 1.0:
                    stakes[h_id] = round(float(stake), 0)
        
        return stakes
class WeatherNextClient:
    pass

from services.notification_service import NotificationService
from services.bigquery_service import BigQueryService
from services.storage_service import StorageService

class PredictionEngine:
    def __init__(self):
        if Config.USE_VERTEX_AI:
            print(f"[INFO] Initializing Vertex AI Client in {Config.GCP_LOCATION}...")
            self.client = genai.Client(
                vertexai=True,
                project=Config.MODEL_PROJECT_ID,
                location=Config.GCP_LOCATION
            )
        else:
            print("[INFO] Initializing Standard Gemini Client...")
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            
        self.cache_id = None # Can be set after initialization if using Vertex AI
        self.model_id = Config.GEMINI_MODEL
        self.base_dir = Path(__file__).resolve().parent.parent
        self.data_dir = self.base_dir / "data"
        self.predictions_dir = self.data_dir / "predictions"
        self.predictions_dir.mkdir(parents=True, exist_ok=True)
        self.firestore = FirestoreService()
        self.synergy = SynergyService()
        self.steward = StewardAnalyser()
        self.weathernext = WeatherNextClient()
        self.pedigree = PedigreeService()
        self.kelly = KellyCriterion(
            bankroll=Config.INITIAL_BANKROLL, 
            fractional_kelly=Config.KELLY_FRACTION
        )
        self.notifications = NotificationService()
        self.bigquery = BigQueryService()
        self.storage = StorageService()
        
        # Load RL Bias Correction with contextual awareness
        from services.rl_optimizer import RLOptimizer
        self.optimizer = RLOptimizer()


    async def load_race_data(self, date_str: str, venue: str, race_no: int) -> Dict[str, Any]:
        """Loads all available data for a single race."""
        # Note: Racecard filename uses slightly different format in current data
        # data/racecard_20260315_R1.json vs results_2026-03-15_ST_R1.json
        date_racecard = date_str.replace("-", "")
        
        racecard_path = self.data_dir / f"racecard_{date_racecard}_R{race_no}.json"
        results_path = self.data_dir / "results" / f"results_{date_str}_{venue}_R{race_no}.json"
        analytical_path = self.data_dir / "analytical" / f"analytical_{date_str}_{venue}_R{race_no}.json"
        
        # Look for the latest odds snapshot for this specific date and race
        odds_dir = self.data_dir / "odds"
        odds_data = {}
        if odds_dir.exists():
            # First: try to find a snapshot that matches date AND race number exactly
            date_compact = date_str.replace("-", "")
            exact_snapshots = list(odds_dir.glob(f"snapshot_{date_str}_R{race_no}_*.json"))
            if not exact_snapshots:
                # Also try compact date format (snapshot_20260318_R1_...)
                exact_snapshots = list(odds_dir.glob(f"snapshot_{date_compact}_R{race_no}_*.json"))
            
            if exact_snapshots:
                # Filter for valid snapshots (not empty win_odds)
                valid_snapshots = []
                for p in sorted(exact_snapshots, key=lambda x: x.stat().st_mtime, reverse=True):
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            temp_data = json.load(f)
                            if temp_data.get("win_odds"):
                                valid_snapshots.append((p, temp_data))
                                break # Found the latest valid one
                    except Exception:
                        continue
                
                if valid_snapshots:
                    latest_snapshot, odds_data = valid_snapshots[0]
                    print(f"[INFO] Loaded valid odds snapshot: {latest_snapshot.name}")
                else:
                    print(f"[WARNING] No valid date-specific odds snapshots found for {date_str} R{race_no}.")

            if not odds_data:
                # Fallback: use most recent snapshot for this race number (any date)
                all_snapshots = list(odds_dir.glob(f"snapshot_*_R{race_no}_*.json"))
                if all_snapshots:
                    # Sort by modification time and find first valid one
                    for p in sorted(all_snapshots, key=lambda x: x.stat().st_mtime, reverse=True):
                        try:
                            with open(p, "r", encoding="utf-8") as f:
                                temp_data = json.load(f)
                                if temp_data.get("win_odds"):
                                    odds_data = temp_data
                                    print(f"[INFO] Using latest valid matching race snapshot: {p.name}")
                                    break
                        except Exception:
                            continue

        data = {
            "racecard": {},
            "results": {},
            "analytical": {},
            "odds": odds_data
        }

        if not racecard_path.exists() and results_path.exists():
            print(f"[INFO] Racecard missing for {date_str} R{race_no}. Reconstructing from results...")
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
            
            # Reconstruct a skeleton racecard
            skeleton_horses = []
            for r in res_data.get("results", []):
                skeleton_horses.append({
                    "saddle_number": int(r["horse_no"]) if r["horse_no"].isdigit() else 0,
                    "horse_name": r.get("brand_id", ""),  # Using brand_id as a hint
                    "jockey": r.get("jockey", ""),
                    "trainer": r.get("trainer", ""),
                    "weight": 133, # Dummy weight if missing
                    "last_6_runs": []
                })
            
            data["racecard"] = {
                "id": f"{date_str}_R{race_no}",
                "distance": 1200, # Defaulting or could extract from results if available
                "horses": skeleton_horses
            }
        elif racecard_path.exists():
            with open(racecard_path, "r", encoding="utf-8") as f:
                data["racecard"] = json.load(f)
        
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                data["results"] = json.load(f)
                
        if analytical_path.exists():
            with open(analytical_path, "r", encoding="utf-8") as f:
                data["analytical"] = json.load(f)

        # 5. Load Synergy Data
        synergy_data = {}
        for h in data["racecard"].get("horses", []):
            jockey = h.get("jockey")
            trainer = h.get("trainer")
            if jockey and trainer:
                stats = self.synergy.get_synergy(jockey, trainer)
                if stats:
                    synergy_key = f"{jockey} + {trainer}"
                    synergy_data[synergy_key] = stats
        
        data["synergy"] = synergy_data

        # 2. Pedigree Intelligence
        pedigree_intel = {}
        for horse_data in data["racecard"].get("horses", []):
            horse_id = horse_data.get("horse_id") # Assuming horse_id is available in racecard horse data
            if horse_id:
                try:
                    # We do this sequentially for now, could be parallelized
                    intel = await self.pedigree.get_enriched_pedigree(horse_id)
                    if intel:
                        pedigree_intel[horse_id] = intel
                except Exception as e:
                    print(f"Warning: Could not get pedigree for horse {horse_id}: {e}")
                    continue
        data["pedigree_intel"] = pedigree_intel

        # 3. Load Hidden Form Tags
        hidden_form_data = {}
        for h in data["racecard"].get("horses", []):
            brand_id = h.get("brand_id")
            if brand_id:
                tags = self.steward.get_hidden_form(brand_id)
                if tags:
                    hidden_form_data[brand_id] = tags
        
        data["hidden_form"] = hidden_form_data

        # 7. Load Weather Intelligence
        weather_intel = {}
        intel_path = Path(f"data/weather/intel_{venue}_{date_str}.json")
        if intel_path.exists():
            with open(intel_path, "r", encoding="utf-8") as f:
                weather_intel = json.load(f)
        data["weather_intel"] = weather_intel

        return data

    async def generate_prediction(self, date_str: str, venue: str, race_no: int) -> Optional[Prediction]:
        """Generates a prediction using Gemini based on loaded race data."""
        data = await self.load_race_data(date_str, venue, race_no)
        
        if not data["racecard"]:
            print(f"Warning: No racecard found for {date_str} R{race_no}. Prediction may be incomplete.")
            if not data["results"] and not data["analytical"]:
                print(f"Error: Insufficient data for {date_str} R{race_no}.")
                return None

        # Retrieve contextual weights for this specific meeting
        self.bias_correction = self.optimizer.get_weights(date_str, venue)
        print(f"[INFO] Using contextual biases for {date_str} {venue}: {self.bias_correction}")

        # Construct the prompt
        prompt = self._construct_prompt(data)

        
        print(f"Generating prediction for {date_str} {venue} R{race_no}...")
        try:
            # Define dynamic probability properties for the schema
            racecard = data.get("racecard", {})
            horses = racecard.get("horses", [])
            prob_props = {
                str(h.get("saddle_number") or h.get("horse_no")): {"type": "number"}
                for h in horses
            }

            response_schema = {
                "type": "object",
                "properties": {
                    "confidence_score": {"type": "number"},
                    "is_best_bet": {"type": "boolean"},
                    "recommended_bet": {"type": "string"},
                    "probabilities": {
                        "type": "object",
                        "properties": prob_props,
                        "required": list(prob_props.keys())
                    },
                    "analysis_markdown": {"type": "string"}
                },
                "required": ["confidence_score", "is_best_bet", "recommended_bet", "probabilities", "analysis_markdown"]
            }

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    cached_content=self.cache_id
                )
            )
            
            prediction_dict = json.loads(response.text)
            
            # Calculate Kelly Stakes
            win_odds = data.get("odds", {}).get("win_odds", {})
            probs = prediction_dict.get("probabilities", {})
            
            # Apply RL Bias Correction to probabilities before Kelly calculation
            # If the AI is overconfident, we scale down the probabilities to be more conservative
            conf_bias = self.bias_correction.get("confidence_bias", 0.0)
            if conf_bias > 0:
                # Simple linear de-biasing
                probs = {h: p * (1 - conf_bias) for h, p in probs.items()}
            
            prediction_dict["kelly_stakes"] = self.kelly.calculate_race_stakes(
                probs, 
                win_odds
            )
            prediction_dict["market_odds"] = win_odds
            
            # Create Prediction object
            prediction = Prediction(
                race_id=f"{date_str}_{venue}_R{race_no}",
                gemini_model=Config.GEMINI_MODEL,
                **prediction_dict
            )
            
            self._save_prediction(prediction)
            
            # Send Push Notification for High Confidence / High EV bets
            has_stakes = any(v > 0 for v in prediction.kelly_stakes.values())
            if prediction.confidence_score >= 0.8 or has_stakes:
                # Identify the top horse ID
                top_horse_id = "Multiple"
                if prediction.kelly_stakes:
                    top_horse_id = max(prediction.kelly_stakes, key=prediction.kelly_stakes.get)
                
                # We don't have EV stored in the simple dict, so we use the stake as a proxy for 'value' here
                max_stake = max(prediction.kelly_stakes.values()) if prediction.kelly_stakes else 0.0
                
                self.notifications.send_bet_alert(
                    race_id=prediction.race_id,
                    horse_name=f"Horse {top_horse_id}",
                    confidence=prediction.confidence_score,
                    ev=max_stake # Using stake as a proxy since EV isn't in this schema
                )

            return prediction
            
        except Exception as e:
            print(f"Error generating prediction: {e}")
            return None

    def _construct_prompt(self, data: Dict[str, Any]) -> str:
        racecard = data.get("racecard", {})
        results = data.get("results", {})
        analytical = data.get("analytical", {})
        odds = data.get("odds", {})
        
        racecard_horses = racecard.get('horses', [])
        horse_nos = [str(h.get('saddle_number', '')) for h in racecard_horses if h.get('saddle_number')]
        if not horse_nos and racecard_horses:
            # Fallback for different data structures
            horse_nos = [str(h.get('horse_no', '')) for h in racecard_horses if h.get('horse_no')]
        
        horse_nos_str = ", ".join(horse_nos)

        prompt = f"""
Act as a professional Hong Kong horse racing analyst. Your task is to analyze race data and provide a winning prediction.

### RACE CONTEXT
Race ID: {racecard.get('id', 'N/A')}
Distance: {racecard.get('distance', 'N/A')}m
Track: {racecard.get('track_type', 'N/A')}
Class: {racecard.get('race_class', 'N/A')}

### HORSE ENTRIES (Race Card)
{json.dumps(racecard.get('horses', []), indent=2)}

### ANALYTICAL DATA (Sectional Times & Positions)
{json.dumps(analytical, indent=2)}

### MARKET ODDS
{json.dumps(odds, indent=2)}

### STEWARDS' REPORTS & INCIDENTS (Human Context)
{json.dumps(results.get('incidents', []), indent=2)}
Overall Report: {results.get('stewards_report', 'None available')}

### BARRIER TRIALS (Pre-race Fitness)
{json.dumps(analytical.get('trials', []), indent=2)}

### HORSE NUMBERS TO PREDICT
{horse_nos_str}

### JOCKEY-TRAINER SYNERGY STATS (Historical Combo Performance)
{json.dumps(data.get('synergy', {}), indent=2)}

### HIDDEN FORM & FORGIVENESS TAGS (Qualitative Excuses for Past Runs)
{json.dumps(data.get('hidden_form', {}), indent=2)}

### WEATHER INTELLIGENCE (Probabilistic Forecasting)
{json.dumps(data.get('weather_intel', {}), indent=2)}

### PEDIGREE INTELLIGENCE (Heritage & Track Suitability)
{json.dumps(data.get('pedigree_intel', {}), indent=2)}

AI Instruction: 
1. Correlate rainfall probability with track condition stability and heat stress probability with horse weight/fitness performance.
2. Cross-reference Weather Intelligence with Pedigree Intelligence. If P(Rain) is high, prioritize horses with 'wet_track_index' > 0.75.

### SYSTEM BIASES (Historical Error Correction)
Your past performance shows specific biases. Adjust your reasoning accordingly:
- Sectional Weighting: Multiply your perceived importance of sectional times by {self.bias_correction.get('sectional_weight_multiplier', 1.0)}.
- Synergy Weighting: Multiply your perceived importance of Jockey-Trainer synergy by {self.bias_correction.get('synergy_weight_multiplier', 1.0)}.
- Confidence Adjustment: { "Decrease" if self.bias_correction.get('confidence_bias', 0) > 0.2 else "Maintain" } your confidence score as you have shown a tendency to be over-confident.

### HISTORICAL CONTEXT (Past Performance Analysis)
Analyze the horses' recent forms (last_6_runs), their sectional positions (sectional_pos) in this race (if available as a recap), and how they handled weights (act_weight).

Detected Patterns: 
1. 'Flying Finishers': Horses that gained significant ground in the final sectional.
2. 'Pace Victims': Horses that led but faded due to fast early pace.
3. 'Forgiveable Losses': Use Stewards' Reports to identify horses that were hampered, raced wide, or had legitimate excuses for losing.
4. 'Trial Stars': Use Barrier Trial data to identify horses showing peak fitness in recent trials.

### OUTPUT REQUIREMENTS
Provide a JSON object following this structure:
{{
  "confidence_score": (float between 0.0 and 1.0),
  "is_best_bet": (boolean),
  "recommended_bet": (string, MUST include horse number, e.g., "WIN 5", "PLACE 2", "QUINELLA 1-4"),
  "probabilities": {{
    "1": 0.15,
    "2": 0.05,
    ...
  }},
  "analysis_markdown": (A detailed markdown analysis justifying your choice)
}}

CRITICAL: You MUST provide a win probability for EACH of these horse numbers: {horse_nos_str}. The sum of all probabilities MUST be 1.0.
"""
        return prompt

    def _save_prediction(self, prediction: Prediction):
        filename = self.predictions_dir / f"prediction_{prediction.race_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(prediction.model_dump_json(indent=2))
        print(f"Prediction saved to {filename}")
        
        # Cloud Sync (GCS Vault)
        try:
            self.storage.upload_prediction(prediction.race_id, str(filename))
        except Exception as e:
            print(f"[WARNING] GCS sync failed: {e}")

        # Cloud Sync (Firestore)
        self.firestore.upsert(Config.COL_PREDICTIONS, prediction.race_id, prediction)
        
        # Cloud Sync (BigQuery)
        try:
            # Extract basic metrics for BQ analytics
            bq_data = {
                "race_id": prediction.race_id,
                "date": prediction.race_id.split("_")[0],
                "confidence_score": float(prediction.confidence_score),
                "recommended_bet": str(prediction.recommended_bet),
                "is_best_bet": bool(prediction.is_best_bet),
                "created_at": datetime.now().isoformat()
            }
            self.bigquery.upsert_prediction(bq_data)
        except Exception as e:
            print(f"[WARNING] BigQuery sync failed: {e}")

    # Removed legacy internal Kelly logic in favor of services.kelly_criterion

if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="HKJC Prediction Engine")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Date in YYYY-MM-DD format")
    parser.add_argument("--venue", type=str, default="ST", help="Venue (ST or HV)")
    parser.add_argument("--race", type=int, default=1, help="Race number")
    args = parser.parse_args()

    engine = PredictionEngine()
    asyncio.run(engine.generate_prediction(args.date, args.venue, args.race))
