# Expert Guide: System Operations Manual

This document provides the technical "SOP" (Standard Operating Procedure) for running the HKJC Betting Automation pipeline.

## 1. The Automation Pipeline (The "Wheel")
The system follows a strict 4-step sequence:
1. **Fetcher (`auto_fetch_racecards.py`)**: Checks HKJC for new racecards for the upcoming meeting.
2. **Predictor (`batch_predict.py`)**: Runs the Gemini AI on the fetched data to generate `prediction_*.json` files.
3. **Trigger (`filter_high_confidence.py`)**: Identifies the "Certified" bets that meet Kelly and Consensus thresholds ($150+ or 0.85+).
4. **Learner (`auto_fetch_and_learn.py`)**: Runs *after* the meeting settles to update `bias_correction.json`.

## 2. Critical Commands & Shortcuts
For a quick system check, always run these in order:
- `python test_local_system.py`: Checks if all data directories exist.
- `python check_firestore_results.py`: Verifies cloud synchronization.
- `python scripts/audit_ai.py`: Health check for Vertex AI endpoints.

## 3. Automation Scheduling (Task Scheduler)
- **Time 10:00 AM**: Primary Fetch & Predict (Wait until later for final odds).
- **Time 12:00 PM**: Final Strategy Filter (Generate the final "High Confidence" bet list).
- **Time 23:30 (Post-Race)**: Auto-Learning (Ingest dividends and results).

## 4. Key Performance Indicators (KPIs)
A healthy system should maintain:
- **Accuracy**: > 85%
- **Brier Score**: < 0.150
- **Cloud Sync Delay**: < 5 minutes

---
> [!NOTE]
> If a future AI is asked to "Start the Meeting," it must first confirm that `weather_intel` is updated, as Gemini's reasoning relies heavily on track-condition forecasting.
