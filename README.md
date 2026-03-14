# HKJC Betting System V2

Professional horse racing prediction engine powered by Gemini AI and Google Cloud.

## 💻 Multi-Machine Setup (3-PC Sync)

To switch between your machines seamlessly, follow this workflow:

### 1. On your current machine (where Antigravity worked):
The code is automatically committed and pushed to GitHub after major milestones.
```bash
git push origin main
```

### 2. On your other machines (to start working):
The first time, clone the repo:
```bash
git clone https://github.com/wallaceclwong/hkjc-v2.git
cd hkjc-v2
pip install -r requirements.txt
cp .env.example .env  # Then add your Gemini API Key
```

Every time you switch **TO** a machine:
```bash
git pull origin main
```

### 3. Shared Resources (Cloud)
- **Database:** All machines connect to the same **Google Firestore** project. Data scraped on PC 1 is instantly available on PC 2.
- **AI:** All machines use the same **Gemini API** key and prompts.

## 🛠 Project Structure
- `services/`: Ingestion and analytical scripts.
- `models/`: Pydantic data schemas.
- `docs/`: Data model and architectural documentation.
- `config/`: Centralized settings and environment loading.
- `data/`: Local cache of JSON results (not synced to Git by design).
