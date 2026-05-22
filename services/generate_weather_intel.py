"""
WeatherAnalyzer — DEPRECATED
=============================
This service previously used Google Vertex AI (Gemini) for weather intelligence.
Vertex AI has been fully removed from this project.

This file is kept as a tombstone to avoid import errors in any legacy code paths.
Do NOT re-enable without explicit approval.
"""
import sys
import os

class WeatherAnalyzer:
    """DEPRECATED: Vertex AI weather analyzer. Raises on init."""
    def __init__(self):
        raise NotImplementedError(
            "[WeatherAnalyzer] DISABLED — Vertex AI has been removed."
        )

    async def analyze(self, *args, **kwargs):
        raise NotImplementedError("WeatherAnalyzer is disabled.")
