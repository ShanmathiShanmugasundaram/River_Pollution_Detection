# Ganga River Water Quality Forecasting & Early Warning System

A React + Flask research dashboard around the existing processed Ganga River forecasting outputs. The frontend does not retrain, replace, or modify the iTransformer model. The Flask API reads the supplied `Processed_Data` exports directly for a zero-configuration demo, while the included MySQL schema and importer provide the production persistence path.

## Run locally

From `website/`:

```powershell
npm install
npm run dev
```

In a second terminal, from `website/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\app.py
```

Open `http://localhost:5173`.

## MySQL deployment

1. Create the schema with `backend/schema.sql`.
2. Copy `.env.example` to `.env` and set credentials. Never commit `.env`.
3. Run `python backend/import_mysql.py` to import the existing CSV exports. This script only loads processed outputs and never invokes model training.

The landing page Login and Sign up actions use the MySQL `users` table and a Flask HttpOnly session cookie. Apply `backend/schema.sql`, set `MYSQL_*` and `FLASK_SECRET_KEY`, then restart Flask. Explore Dashboard and Explore River require an authenticated session; successful login returns the user to the requested destination.

The UI explicitly distinguishes historical observations, model-generated 2026 predictions, project-defined WQI classes, CPCB reference criteria, project forecast hotspot levels, and complementary biological observations.
