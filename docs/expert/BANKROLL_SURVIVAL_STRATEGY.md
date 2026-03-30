# Expert Guide: Bankroll Survival & Strategy

This document outlines the "Financial Guardrails" of the HKJC system, designed to protect the user's capital from "Black Swan" events and biased AI.

## 1. The Tenth-Kelly Criterion (Fractional Strategy)
We use a **1/10th Fractional Kelly** (`Config.KELLY_FRACTION = 0.10`).
- **Why?**: Pure Kelly is mathematically optimal but emotionally volatile. A 10% fraction provides near-optimal growth with **90% less risk of ruin**.
- **Safe Mode**: 1/10th Kelly is the default. Only increase to 1/5th (0.20) if the Brier score remains below 0.100 for 5 consecutive meetings.

## 2. Hard Betting Thresholds
- **Confidence**: `MIN_CONFIDENCE = 0.65`.
- **Edge (Advantage)**: `MIN_EDGE = 0.05`.
- **Stake Cap**: Never exceed **5% of total bankroll** on a single race.
- **Odds Limit**: If the "Market Odds" have moved by more than **30%** in the 5 minutes before the race, the bet is automatically cancelled as the "Value" has evaporated.

## 3. Consensus Blocking (The "Second Opinion")
- If the **Primary Model** (Pro) suggests a $1,000 bet, but the **Shadow Model** (Flash) is unsure, the system MUST clear the stakes.
- **Goal**: One "Hallucinated" winner is not worth the risk of a $1,000 loss based on false AI logic.

## 4. Track Bias Adjustments
- **Sha Tin (ST)**: Baseline multipliers (1.0).
- **Happy Valley (HV)**: 0.85 Multiplier (Higher variance due to tighter turns).
- **Wet Track (Rain)**: 0.70 Multiplier (The most unpredictable condition).

---
> [!IMPORTANT]
> A future AI assistant must never "Override" these safeguards to chase losses. The system is designed for **Sustainable Compounding**, not "Gambling."
