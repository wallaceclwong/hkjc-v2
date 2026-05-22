"""
PredictionEngine — DEPRECATED
==============================
This service previously used Google Vertex AI (Gemini) for race predictions.
Vertex AI has been fully removed from this project.

This file is kept as a tombstone to avoid import errors in any legacy code paths.
Do NOT re-enable without explicit approval.
"""
import sys
import os

class PredictionEngine:
    """DEPRECATED: Vertex AI prediction engine. Raises on init."""
    def __init__(self):
        raise NotImplementedError(
            "[PredictionEngine] DISABLED — Vertex AI has been removed."
        )

    async def load_race_data(self, *args, **kwargs):
        raise NotImplementedError("PredictionEngine is disabled.")

    async def generate_prediction(self, *args, **kwargs):
        raise NotImplementedError("PredictionEngine is disabled.")
