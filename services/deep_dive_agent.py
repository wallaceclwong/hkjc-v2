import os
import sys
import json
from google import genai
from google.genai import types
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from services.firestore_service import FirestoreService

class DeepDiveAgent:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=Config.MODEL_PROJECT_ID,
            location=Config.GCP_LOCATION
        )
        self.model_id = "gemini-2.5-pro" # Always use Pro for deep dives
        self.firestore = FirestoreService()
        self.base_dir = Path(__file__).resolve().parent.parent
        self.reports_dir = self.base_dir / "data" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_top_horse_history(self, race_id: str, horse_no: str, data: dict):
        """
        Performs an 'Extreme Reasoning' deep dive on a single horse.
        Focuses on qualitative form, pedigree suitability, and steward history.
        """
        logger.info(f"🔍 DEEP DIVE AGENT: Starting analysis for {race_id} Horse #{horse_no}")
        
        # Construct a specialized deep-dive prompt
        prompt = self._construct_deep_dive_prompt(race_id, horse_no, data)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2, # Lower temperature for analytical precision
                    max_output_tokens=2048 # Allow for long-form reasoning
                )
            )
            
            report_text = response.text
            
            # Save the report
            report_data = {
                "race_id": race_id,
                "horse_no": horse_no,
                "model": self.model_id,
                "analysis": report_text,
                "timestamp": os.path.getmtime(self.base_dir / "data" / "predictions" / f"prediction_{race_id}.json")
            }
            
            # Save locally
            report_path = self.reports_dir / f"deep_dive_{race_id}_H{horse_no}.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"# Deep Dive Analysis: {race_id} Horse #{horse_no}\n\n")
                f.write(report_text)
            
            # Sync to Firestore
            self.firestore.upsert("deep_dive_reports", f"{race_id}_H{horse_no}", report_data)
            
            logger.info(f"✅ DEEP DIVE COMPLETE: Report saved to {report_path}")
            return report_text
            
        except Exception as e:
            logger.error(f"❌ DEEP DIVE FAILED: {e}")
            return None

    def _construct_deep_dive_prompt(self, race_id: str, horse_no: str, data: dict) -> str:
        racecard = data.get("racecard", {})
        results = data.get("results", {})
        
        # Find the specific horse data
        horse_data = next((h for h in racecard.get("horses", []) if str(h.get("saddle_number") or h.get("horse_no")) == str(horse_no)), {})
        
        prompt = f"""
Act as a Senior Hong Kong Staging Analyst. Your task is to perform an EXTREME REASONING deep dive into one specific horse (# {horse_no}) in Race {race_id}.

### THE HORSE: {horse_data.get('horse_name', 'Unknown')} (# {horse_no})
- Jockey: {horse_data.get('jockey', 'N/A')}
- Trainer: {horse_data.get('trainer', 'N/A')}
- Barrier: {horse_data.get('draw', 'N/A')}
- Weight: {horse_data.get('weight', 'N/A')}

### RACE CONTEXT
- Distance: {racecard.get('distance', 'N/A')}m
- Track: {racecard.get('track_type', 'N/A')}
- Class: {racecard.get('race_class', 'N/A')}

### HISTORICAL REASONING TASK
1. **Analyze Past 6 Runs**: Look for 'Sectional Flashes'. Did this horse gain 5+ lengths in the final 400m in any recent run?
2. **Scrutinize Stewards' Reports**: Search for 'Hampered', 'Blocked', 'Raced Wide', or 'Heat Stress' incidents in this horse's history.
3. **Pedigree Check**: Is this specific distance and track type (ST/HV) mathematically supported by its heritage?
4. **Jockey Strategy**: Does the current jockey specialize in 'Lead and Hold' or 'Back-marker Swoop'? How does that fit the current barrier draw?

### OUTPUT FORMAT:
Provide a 5-paragraph Senior Staging Report. 
1. **Historical Forgiveness**: List any past runs that the AI should 'ignore' due to bad luck.
2. **Hidden Form**: Identify any 'sectional strengths' not visible in the plain numbers.
3. **Risk Factors**: Identify the #1 reason this horse might LOSE today.
4. **Strategy Verdict**: Final tactical assessment (Primary Pick, Save, or Avoid).
5. **Final Confidence**: 0-100%

CRITICAL: DO NOT use placeholders. Analyze the provided data strictly.
"""
        return prompt
