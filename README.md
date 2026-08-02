# ClarifAI

AI-planned, Pandas-executed data cleaning. Upload a messy Excel sheet, describe how you want it
cleaned (or pick a use case), and get back a fully cleaned, normalized `.xlsx` — no further changes
needed.

**Architecture in one line:** Claude decides *what* to clean (a structured JSON plan); Pandas
*executes* that plan deterministically. The AI never touches your data directly or runs arbitrary
code, which keeps cleaning auditable and safe.

```
backend/    FastAPI + Pandas + Claude API + SQLite/Postgres
frontend/   React (Vite) UI
sample_data/messy_sample.xlsx   a synthetic dirty sheet for testing
```

## 1. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `ANTHROPIC_API_KEY` — get one from https://console.anthropic.com. Without it, ClarifAI still
  runs, but falls back to a generic dtype-based cleaning plan instead of understanding your
  plain-English instructions.
- `DATABASE_URL` — defaults to local SQLite (`clarifai.db`). For production, point this at
  Postgres, e.g. `postgresql://clarifai:password@localhost:5432/clarifai`.

Run it:

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API docs (Swagger UI).

### Run the automated end-to-end test

This exercises signup → upload → AI/predefined plan → execute → download → save template, using
the bundled `sample_data/messy_sample.xlsx`, without needing a real API key:

```bash
cd backend
python3 tests/test_end_to_end.py
```

## 2. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env      # points VITE_API_BASE at your backend
npm run dev
```

Visit `http://localhost:5173`.

## 3. Using Postgres instead of SQLite

```bash
sudo apt-get install postgresql
sudo -u postgres createdb clarifai
sudo -u postgres createuser clarifai --pwprompt
```

Then set in `backend/.env`:
```
DATABASE_URL=postgresql://clarifai:<password>@localhost:5432/clarifai
```
No code changes needed — SQLAlchemy handles the switch.

## How the pieces fit together

1. **Upload** (`POST /files/upload`) — reads the sheet with Pandas, returns a schema/preview summary.
2. **Plan** (`POST /clean/plan`) — resolves a `CleaningPlan` from one of three sources:
   - a **predefined template** (Sales, HR, Survey, Financial — see `app/predefined_templates.py`)
   - a **plain-English description**, routed through Claude via forced tool-use so the response is
     always a valid, schema-constrained JSON plan (`app/ai_planner.py`)
   - a **saved template** the user created earlier
3. **Execute** (`POST /clean/execute`) — `app/cleaning_engine.py` deterministically applies the plan
   with Pandas: dedup, null handling, dtype coercion, trimming, case normalization, outlier
   handling, column renaming. Returns a before/after quality report.
4. **Download** (`GET /clean/download/{file_token}`) — the cleaned `.xlsx`.
5. **Save template** (`POST /templates/save`) — persists a plan (with a name/description) tied to
   the logged-in user for reuse next time.

## Notes for the resume / interview

The one thing worth explaining well: the AI layer only ever picks values for a fixed schema
(`CleaningPlan` in `app/schemas.py`) via Claude's tool-use, and a separate deterministic engine
executes it. This bounds what the AI can affect, keeps every run auditable, and avoids the risk of
letting a model generate/execute arbitrary code against someone's data.
