# HKJC V2 Data Model Design (Firestore)

This document defines the NoSQL structure for our horse racing system. We prioritize flexibility for AI analysis (Gemini) while maintaining efficient query paths for the odds monitor.

## Collections Overview

### 1. `fixtures` (Monthly Schedule)
Used to schedule ingestion jobs.
- **ID:** `YYYY-MM-DD` (e.g., `2026-03-22`)
- **Fields:**
  - `date`: Timestamp
  - `venue`: String ("ST", "HV")
  - `venue_full`: String ("Sha Tin", "Happy Valley")
  - `day_night`: String ("D", "N")
  - `type`: String ("Local", "Simulcast")
  - `status`: String ("Scheduled", "Ingested", "Completed")

### 2. `racecards` (Daily Entries)
The core "snapshot" of a race day.
- **ID:** `YYYY-MM-DD_RACE_XX` (e.g., `2026-03-22_R1`)
- **Fields:**
  - `race_date`: Timestamp
  - `race_number`: Integer
  - `distance`: Integer (e.g., 1200)
  - `track_type`: String ("Turf", "All Weather")
  - `course_name`: String (e.g., "A Course")
  - `class`: String (e.g., "Class 3")
  - `sectional_times_target`: Map (Horse ID -> Array of Floats) (Calculated from last run)
  - `predicted_pace`: String ("FAST", "EVEN", "SLOW")
  - `horses`: Array of Maps:
    - `horse_id`: String
    - `horse_name`: String
    - `owner`: String
    - `sire`: String (For pedigree analysis)
    - `dam`: String
    - `training_location`: String ("HK", "CTC")
    - `stable_change_flag`: Boolean
    - `current_weight`: Float
    - `optimal_weight_range`: Array of Floats [Min, Max]
    - `jockey_trainer_synergy`: Float (Strike rate %)
    - `trial_comments`: String (Latest qualitative trial notes)
    - `saddle_number`: Integer
    - `draw`: Integer
    - `jockey`: String
    - `trainer`: String
    - `weight_declared`: Float
    - `last_6_runs`: Array of Strings (e.g., ["1", "4", "2"])

### 3. `odds` (Real-time Snapshots)
Timed snapshots for Kelly Criterion and "Smart Money" detection.
- **ID:** `YYYY-MM-DD_RACE_XX_TMIN` (e.g., `2026-03-22_R1_T10`)
- **Fields:**
  - `race_id`: Reference to racecard
  - `timestamp`: Timestamp
  - `interval`: Integer (Minutes before jump: 60, 30, 10, 1)
  - `win_odds`: Map (Horse ID -> Float)
  - `place_odds`: Map (Horse ID -> Array of Floats [Min, Max])

### 4. `predictions` (Gemini Analysis)
- **Fields:**
  - `race_id`: Reference
  - `gemini_version`: String
  - `win_probabilities`: Map (Horse ID -> Float)
  - `confidence_score`: Float (0.0 to 1.0)
  - `is_daily_best_bet`: Boolean (Determined by highest score of the day)
  - `recommended_bet_type`: String ("WIN", "PLACE", "QUINELLA", etc.)
  - `kelly_bet_size`: Map (Horse ID -> Float)
  - `raw_analysis`: String (Markdown)

### 5. `results` (The Learning Bridge)
Stores actual outcomes to validate and "teach" the model.
- **Fields:**
  - `race_id`: Reference
  - `winners`: Array of Horse IDs (usually 1, unless dead heat)
  - `placed_horses`: Array of Horse IDs
  - `dividend_win`: Float
  - `dividend_place`: Array of Floats
  - `is_backtested`: Boolean (set to True after "Learning" script runs)

### 6. `weather` (Hyper-local Conditions)
Data from HKO and HKJC track officials.
- **ID:** `YYYY-MM-DD_VENUE_HH` (e.g., `2026-03-22_ST_14`)
- **Fields:**
  - `venue`: String ("ST", "HV")
  - `temperature`: Float
  - `humidity`: Integer
  - `rainfall_2h`: Float (mm)
  - `track_condition`: String ("Firm", "Good", "Yielding", "Soft")
  - `wind_speed`: Float

### 7. `soft_data` (Qualitative Insights)
- **Sub-collection: `veterinary`**
  - `horse_id`: String
  - `incident_date`: Timestamp
  - `details`: String (Qualitative diagnosis)
  - `clearance_date`: Timestamp
- **Sub-collection: `trackwork`**
  - `horse_id`: String
  - `date`: Timestamp
  - `location`: String (ST, Conghua, HV)
  - `workout_type`: String (Gallop, Swim, Trial)
  - `speed_figures`: String (e.g. "28.9 24.6")
  - `gear_used`: String
- **Sub-collection: `incidents`**
  - `race_id`: Reference
  - `horse_id`: String
  - `incident_report`: String (e.g. "Jumped awkwardly", "Eased when crowded")

## Sub-collections (Optional)
- `horses/{horse_id}/form`: Historical performance records (for deep AI training).
