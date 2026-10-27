# IntelliChurn

IntelliChurn is a customer churn analytics starter with a React/Vite and Tailwind dashboard, Recharts visualizations, a FastAPI API, PostgreSQL persistence, a CatBoost/SMOTE training pipeline, SHAP explanations, and optional Gemini retention advice.

## Requirements

- Python 3.11+
- Node.js 20+
- A Telco churn CSV in the project `data/` directory (the dataset is not bundled)
- Docker Compose for the containerized option

## Run locally

1. Start PostgreSQL, or use SQLite for local development (the default).
2. Configure backend environment variables. Copy `backend/.env.example` to `backend/.env` and set a Gemini key if you want AI retention suggestions. Keep credentials out of source control.
3. Install backend dependencies and start the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. In another terminal, install and start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

5. Open <http://localhost:5173>. Use **Import data** to load a CSV, then train a model as described below.

## Dataset and model

Place the Telco Customer Churn CSV at `data/WA_Fn-UseC_-Telco-Customer-Churn.csv`. The training script expects the original Telco dataset column names, including `customerID`, `SeniorCitizen`, `MonthlyCharges`, `TotalCharges`, and `Churn`, and normalizes them before fitting. The dashboard importer accepts either those source headers or normalized snake_case headers.

The dashboard CSV importer accepts normalized snake_case columns (`customer_id`, `senior_citizen`, `monthly_charges`, etc.) or the original Telco dataset headers, and an optional `churn` column. Boolean values may be `true`/`false`, `yes`/`no`, or `1`/`0`.

Train and save the CatBoost classifier and SHAP explainer:

```powershell
python backend/ml_pipeline/train_model.py
```

Or specify dataset and output paths:

```powershell
python backend/ml_pipeline/train_model.py --data path\to\dataset.csv --output path\to\churn_bundle.joblib
```

The training process uses one-hot encoding, SMOTE on the training data, and CatBoost. Do not commit the generated model artifact. Prediction endpoints report an explicit service error until a trained model is available.

## Docker Compose

Set a URL-safe `POSTGRES_PASSWORD` and optionally `GEMINI_API_KEY` in PowerShell, then run:

```powershell
$env:POSTGRES_PASSWORD = "ChooseAURLSafePassword"
$env:GEMINI_API_KEY = "your-gemini-api-key"
docker compose up --build
```

Omit the Gemini key if you only need churn analysis; AI retention suggestions will report that they are not configured.

The API is at <http://localhost:8000> and the interactive API docs are at <http://localhost:8000/docs>. The compose backend mounts `backend/ml_pipeline/saved_models`; train the model before making predictions. The database and prediction records persist in the `postgres_data` volume.

## API overview

- `GET /api/health` — API liveness
- `GET /api/dashboard` — customer and prediction metrics
- `GET /api/customers` — imported customers
- `POST /api/customers/import` — import a CSV as multipart field `file`
- `POST /api/customers/{customer_id}/predict` — persist a churn probability and SHAP factors
- `GET /api/customers/{customer_id}/predictions` — customer prediction history
- `POST /api/retention-strategy` — generate a Gemini retention playbook

Gemini requests use a 25-second timeout, low thinking, and a short response limit. If
the configured model reaches a provider deadline, the API tries the faster
`gemini-3.5-flash-lite` fallback once. If both models time out, it returns a clear
gateway-timeout error instead of leaving the browser request running until its timeout.

Gemini suggestions require `GEMINI_API_KEY`. The dataset and model are deliberately not silently fabricated; the UI and API indicate when setup is incomplete.
