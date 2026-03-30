# Expert Guide: AI Conscience & Prediction Logic

This document serves as the "Instructional Core" for any AI assistant managing the HKJC Prediction System. It outlines the strategic reasoning, model hierarchy, and the "Ethical Guardrails" of our betting logic.

## 1. The 3-Layer Consensus Architecture
We do NOT trust a single AI model. Our system uses a multi-layered verification process:
1. **Primary Intelligence (Gemini 2.5 Pro)**: High-reasoning, deep analysis of sectional data.
2. **Consensus Layer (Gemini 2.0 Flash)**: A fast, "Second Opinion" model. 
    - **Rule**: If Gemini 2.0 Flash disagrees with Gemini 2.5 Pro on the "Top Pick" by more than **10% probability**, the bet is CANCELLED.
3. **Deep-Dive Specialist (Agentic)**: Triggers only for **High-Stake Bets (>$150)** or **High Confidence (>0.85)**.
    - **Goal**: Extreme parsing of Pedigree and Steward incidents to confirm the "Logic Case" for the bet.

## 2. Model Selection Reasoning
- **Gemini 2.5 Pro**: Chosen for its superior context window and ability to parse 11.5k lines of messy sectional JSON.
- **Gemini 2.0 Flash**: Acts as the "Heuristic" check—it's cheap, fast, and great at catching obvious statistical outliers.

## 3. "The Forgiveness Principle"
The AI must focus on **Contextual Form**, not just "Win/Loss" rows.
- **Always Forgive**: A loss where the horse was blocked, raced wide, or had a slow start (see Steward Reports).
- **Prioritize**: "Flying Finishers" (Horses that gained significant ground in the final section, even if they finished 4th or 5th).

## 4. Cost Efficiency "Ethos"
- Accuracy over Volume. We would rather run 10 high-quality, high-cost ($0.02) predictions than 1,000 low-quality ones.
- Maintain a **Monthly Budget CAP of $10.00 USD**.

---
> [!IMPORTANT]
> If a future AI assistant suggests a "Single-Model" bet, it is violating the core conscience of this system. ALWAYS enforce the **Consensus Rule**.
