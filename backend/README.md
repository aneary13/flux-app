# FLUX Engine (Backend)

The FLUX Engine is a Python-based FastAPI backend that serves as the biological decision engine for the FLUX React Native mobile app. It translates biological inputs (pain, energy, pattern debt) into auto-regulated, structured training sessions.

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Framework** | FastAPI (Python 3.13+) |
| **Package Manager** | `uv` |
| **Database** | Supabase (PostgreSQL) |
| **Validation** | Pydantic V2 |
| **Deployment** | Render (Web Service) |

## System Architecture: "The Brain"

The core logic of FLUX lives in `core/resolver.py`. It operates on three main biological concepts:

1. **Readiness State (Green / Orange / Red):**
   * Calculated from user inputs (`knee_pain`, `energy`).
   * Dictates the session *Archetype* (Performance vs. Recovery).
   * Dictates exercise selection (e.g., `GREEN` = Back Squat, `ORANGE` = Box Squat).
2. **Pattern Debt:**
   * Tracks sessions since a movement pattern was last trained (`SQUAT`, `HINGE`, `PUSH`, `PULL`).
   * The highest debt becomes the `anchor_pattern` for the generated session.
3. **Conditioning Progression:**
   * Tracks linear progression levels for protocols (`HIIT`, `SIT`, `SS`).
   * Handles dynamic wattage calculations based on user benchmarks.

### Database Schema Notes

We use a hybrid relational/NoSQL approach to keep tables clean. The `workout_sets` table contains standard relational columns (`weight`, `reps`, `seconds`) alongside a powerful `metadata` (JSONB) column to store protocol-specific conditioning data (e.g., `avg_watts`, `peak_hr`, `protocol_level`) without polluting the table with sparse columns.

## Directory Structure

```text
backend/
├── config/              # YAML files defining the rules, relationships, and exercises
├── core/
│   ├── models.py        # Pydantic schemas for API validation
│   └── resolver.py      # The FLUX Engine logic
├── scripts/
│   └── seed_db.py       # Pushes YAML configs & exercises to Supabase
├── tests/
├── main.py              # FastAPI application and route definitions
├── pyproject.toml       # uv dependency definitions
├── uv.lock              # Deterministic build lockfile
└── requirements.txt     # Exported for Render deployment
```

Local Development & Setup

This project uses `uv` for lightning-fast dependency management and virtual environments.

### 1. Installation

Ensure `uv` is installed on your machine, then run:

```bash
uv sync
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_or_service_role_key
```

### 3. Running the Server Locally

To boot the FastAPI server on port 8000 with hot-reloading:

```bash
uv run uvicorn main:app --reload
```

## Database Management Workflow

### Migrations

We manage Supabase migrations via the Supabase CLI.

* Generate a new migration: `supabase migration new <name>`
* Push to production: `supabase db push`

### Seeding the Database

If you wipe the database or update the YAML files in `/config`, you must push the new "Brain" to Supabase. **Ensure your `.env` points to the correct database before running!**

```bash
uv run scripts/seed_db.py
```

## Deployment (Render)

The application is deployed on Render. Because Render does not natively run `uv` during the build step, we must export a locked `requirements.txt` file before pushing to GitHub.

### Pre-Commit Checklist

If you added or updated any dependencies, you MUST run this command before committing:

```bash
uv export --format requirements-txt > requirements.txt
```

### Render Settings

* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
* **Env Vars**: Ensure `SUPABASE_URL`, `SUPABASE_KEY`, and `PYTHON_VERSION` (e.g., `3.13.7`) are set in the Render dashboard.

## Current Technical Debt / Future Work

* **Authentication:** The app currently relies on a hardcoded `DUMMY_USER_ID`. Future updates need to integrate Supabase Auth, passing JWTs from the React Native frontend to the FastAPI backend to securely resolve isolated user state documents.
* **Set Verification:** The `/sessions/{session_id}/complete` endpoint currently blindly trusts the frontend payload to progress levels. It needs an update to actively query the `workout_sets` table to verify the user actually logged the required sets before granting a progression level-up.
