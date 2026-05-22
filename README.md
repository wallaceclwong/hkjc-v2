# HKJC Betting System V2

Professional horse racing prediction engine powered by DeepSeek AI and Google Cloud.

> [!IMPORTANT]
> **AI EXPERT KNOWLEDGE BASE**: If you are an AI assistant helping with this project, you MUST read the [Expert Knowledge Base](file:///c:/Users/ASUS/hkjc/docs/expert/) before making any code changes. This ensures you understand the core strategy, safety buffers, and 3-layer consensus logic.

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
cp .env.example .env  # Then add your DeepSeek API Key
```

Every time you switch **TO** a machine:
```bash
git pull origin main
```

### 3. Shared Resources (Cloud)
- **Database:** All machines connect to the same **Google Firestore** project. Data scraped on PC 1 is instantly available on PC 2.
- **AI:** All machines use the same **DeepSeek API** key and prompts.

## 🚀 Cloud Run Deployment

To run this autonomously 24/7 in the cloud:

1.  **Build & Push**:
    ```bash
    gcloud builds submit --tag gcr.io/hkjc-v2/hkjc-predictor
    ```
2.  **Deploy**:
    ```bash
    gcloud run deploy hkjc-predictor --image gcr.io/hkjc-v2/hkjc-predictor --platform managed --region us-central1 --set-env-vars="USE_DEEPSEEK=True,GCP_LOCATION=us-central1"
    ```
3.  **Scheduler**: Set a Cloud Scheduler job to `POST` to your Cloud Run URL 15 minutes before the first race.

## 🛠 Project Structure
- `services/`: Ingestion and analytical scripts.
- `models/`: Pydantic data schemas.
- `docs/`: Data model and architectural documentation.
- `docs/expert/`: The "Brain" and "Expert Rules" for AI assistants.
- `config/`: Centralized settings and environment loading.
- `data/`: Local cache of JSON results (not synced to Git by design).
- `Dockerfile`: Production container config.
