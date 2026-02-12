# FLUX App

## Overview

FLUX app is an application that determines the "Next Best Action" for training sessions based on user readiness and training history, using an agile periodization approach rather than a fixed calendar.

## Project Structure

```
flux-app/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py         # Dependency injection (DB, engine, user ID)
│   │   │   ├── main.py         # API router collection
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── readiness.py  # Readiness check-in endpoints
│   │   │       ├── exercises.py  # Exercise management endpoints
│   │   │       └── workouts.py   # Workout recommendation and completion endpoints
│   │   ├── schemas.py           # Pydantic request/response schemas (workouts, etc.)
│   │   ├── config.py            # Modular config loader (library, logic, sessions, selections, conditioning)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # SQLModel database tables
│   │   │   ├── seeds.py       # Conditioning protocols seed + runner
│   │   │   └── session.py     # Async database session management
│   │   ├── models.py          # Pydantic models for input/output (config in config.py)
│   │   ├── engine.py          # WorkoutEngine class with core logic
│   │   ├── services/
│   │   │   └── workout.py     # Workout completion service (log session, update pattern inventory)
│   │   └── main.py            # FastAPI application entry point
│   ├── alembic/
│   │   ├── versions/          # Database migration files
│   │   ├── env.py             # Alembic configuration for async SQLModel
│   │   ├── script.py.mako     # Migration template
│   │   └── alembic.ini        # Alembic configuration
│   ├── tests/
│   │   ├── test_models.py      # Test Pydantic validation
│   │   └── test_engine.py     # Test logic engine
│   ├── config/                   # Modular YAML config (loaded by src.config.load_config)
│   │   ├── library.yaml          # Exercise catalog and metadata
│   │   ├── logic.yaml            # Thresholds, pattern_priority, power_selection, relationships
│   │   ├── sessions.yaml         # GYM and RECOVERY (Red Day) session structures
│   │   ├── selections.yaml       # Exercise mappings by pattern/tier/state
│   │   └── conditioning.yaml     # Conditioning protocols and equipment
│   ├── .env.example           # Environment variables template
│   ├── pyproject.toml         # uv project config with dependencies
│   ├── requirements.txt       # Production dependencies (generated)
│   ├── start.sh              # Production start script (migrations + server)
│   └── ruff.toml              # Ruff linting/formatting config
├── frontend/
│   ├── app/                    # Expo Router file-based routes
│   │   ├── _layout.tsx        # Root layout with providers
│   │   ├── index.tsx          # Home screen
│   │   ├── check-in.tsx       # Daily readiness check-in screen
│   │   └── workout-plan.tsx   # Workout recommendation display
│   ├── components/
│   │   └── NumberSelector.tsx # Reusable number selector component
│   ├── src/
│   │   └── api/
│   │       └── client.tsx     # Axios instance & QueryClient setup
│   ├── .env                   # Environment variables (EXPO_PUBLIC_API_URL)
│   ├── global.css             # Tailwind CSS directives
│   ├── tailwind.config.js     # Tailwind configuration
│   ├── metro.config.js        # Metro bundler config with NativeWind
│   ├── babel.config.js        # Babel config with NativeWind plugin
│   └── package.json           # npm dependencies
├── DEPLOY.md                  # Deployment guide for Render.com
└── README.md
```

## Features

### Training logic
- **Readiness states**: Evaluates pain (0–10) and energy (0–10) to determine state (RED / ORANGE / GREEN).
- **Pattern debt**: Tracks days since each movement pattern was last performed; history comes from `PatternInventory`, updated when users complete workouts.
- **Session type**: Chooses REST, GYM, or CONDITIONING from energy and pattern debt.
- **Session composition**: Builds GYM sessions as PREP (PATELLAR_ISO, CORE), POWER (RFD), STRENGTH (main lift), and ACCESSORIES from config relationships. When state is RED, returns a **Red Day (Recovery)** session: mobility flow, repair isometrics, 1 Push + 1 Pull (opposite planes), and Zone 2 conditioning.
- **Pattern priority**: When main-pattern debts are tied, uses `pattern_priority` (e.g. SQUAT → PUSH → HINGE → PULL) for an Upper/Lower rotation.
- **Modular config**: Five YAML files in `backend/config/` (library, logic, sessions, selections, conditioning) loaded by `src.config.load_config`. SessionPlan exposes `exercises`, `session_name`, and `archetype` for the frontend.

### Data and API
- **Database**: SQLModel tables for exercises, daily readiness, `PatternInventory`, `WorkoutSession` (UUID, started_at/completed_at, readiness_score, notes), and `WorkoutSet` (exercise_name, weight_kg, reps, RPE). Timestamps are timezone-aware (TIMESTAMPTZ). Async PostgreSQL via asyncpg; Alembic migrations.
- **Endpoints**: Readiness check-in (upsert), exercise list/seed, workout recommendation (from pattern-inventory history), and complete workout (`POST /api/v1/workouts` to log sessions and update pattern inventory). CORS and `X-User-Id` header for user identification.

### Frontend
- **Mobile app**: React Native (Expo) with TypeScript, Expo Router, NativeWind (Tailwind), TanStack Query. Persistent user ID per device; base URL for Android/iOS.
- **Screens**: Daily readiness check-in (pain/energy), workout plan display. Handles Rest Day (404) and other errors.

### Deployment
- **Backend**: Render.com config, `requirements.txt` from `pyproject.toml`, `start.sh` (migrations + uvicorn). Frontend uses `EXPO_PUBLIC_API_URL` for production. See [DEPLOY.md](DEPLOY.md).

## Setup

### Prerequisites

**Backend:**
- Python 3.13+
- `uv` package manager (by Astral)
- PostgreSQL database (e.g., Supabase)

**Frontend:**
- Node.js 18+ and npm/yarn
- Expo CLI (install globally: `npm install -g expo-cli` or use `npx`)
- iOS Simulator (for macOS) or Android Emulator
- Expo Go app (for physical devices)

### Backend Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Create a `.env` file with your database connection string:
   ```bash
   cp .env.example .env
   ```
   **Crucial Supabase Setup:**
   - Use the **Session Pooler** connection string (usually Port `6543`), NOT the Direct connection (`5432`).
   - Ensure the protocol is `postgresql+asyncpg://`.
   - If your password has special characters (e.g., `@`), it must be URL encoded (e.g., `%40`).

4. Run database migrations:
   ```bash
   uv run alembic upgrade head
   ```

### Frontend Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```
   *Note: If you encounter missing asset errors later, run `npx expo install expo-asset`.*

3. (Optional) Configure production API URL:
   ```bash
   # Edit frontend/.env and set EXPO_PUBLIC_API_URL to your Render.com backend URL
   # Example: EXPO_PUBLIC_API_URL=https://your-service.onrender.com
   ```

## Usage

### Running the Application

**1. Start the Backend API Server:**

```bash
cd backend
uv run uvicorn src.main:app --reload
```
The API will be available at `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

**2. Start the Frontend Mobile App:**

**For Physical Devices (Recommended):**
To run on your actual phone (iPhone/Android), you must use the tunnel command to bypass local network restrictions.
```bash
cd frontend
npx expo start --tunnel -c
```
Then scan the QR code with the **Expo Go** app.

**For Simulators (Local Development):**
```bash
cd frontend
npm start
```
Press `i` for iOS simulator or `a` for Android emulator.

**Note on Networking:** The frontend automatically detects the environment:
- **Production**: Uses `EXPO_PUBLIC_API_URL` from `.env` file if set.
- **Development**: Falls back to platform-specific localhost (`http://localhost:8000` for iOS, `http://10.0.2.2:8000` for Android).

### API Endpoints

#### Health Check
```http
GET /
```
Returns: `{"status": "ok", "version": "flux-api-v1"}`

#### Readiness Check-in
```http
POST /api/v1/readiness/check-in
Headers:
  X-User-Id: <uuid>
Body:
  {
    "knee_pain": 2,
    "energy": 7
  }
```
Returns: `{"state": "GREEN"}` (or "RED", "ORANGE")

#### Get Workout Recommendation
```http
POST /api/v1/workouts/recommend
Headers:
  X-User-Id: <uuid>
Body:
  {
    "knee_pain": 2,
    "energy": 7
  }
```
Returns: SessionPlan with recommended workout details

#### Complete Workout
```http
POST /api/v1/workouts
Headers:
  X-User-Id: <uuid>
Body:
  {
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T11:00:00Z",
    "readiness_score": 7,
    "notes": "Optional notes",
    "sets": [
      { "exercise_name": "Back Squat", "weight_kg": 100, "reps": 5, "rpe": 8, "set_order": 0 }
    ]
  }
```
Returns: 201 with saved WorkoutSession (id, user_id, timestamps, sets). Send datetimes in UTC (e.g. ISO 8601 with `Z`).

## Troubleshooting

### Backend / Database
- **`[Errno 8] nodename nor servname provided`**: This usually means your `DATABASE_URL` is incorrect or you are trying to connect to an IPv6 Supabase address on an IPv4 network. Switch to the Supabase **Session Pooler** URL (Port 6543).
- **Render Build Fails**: Ensure `requirements.txt` does not contain a reference to the local `backend` file. Use the `--no-emit-project` flag when exporting dependencies.
- **Render Cold Starts**: If the app gives a "Network Error" after 15 minutes of inactivity, the Render free tier server is likely sleeping. Open the API URL in a browser to wake it up, then reload the app.

### Frontend
- **"Network Error" on Physical Device**: Ensure you are running `npx expo start --tunnel`. Localhost (`127.0.0.1`) cannot be accessed by your phone over WiFi without tunneling.
- **Styles missing**: If NativeWind styles aren't applying, run `npx expo start -c` to clear the Metro cache.

## Deployment

See [DEPLOY.md](DEPLOY.md) for detailed instructions on deploying the backend to Render.com.

## Configuration

The backend uses a **modular config** in `backend/config/` (loaded by `src.config.load_config`). Five YAML files define:

| File | Purpose |
|------|---------|
| **library.yaml** | Exercise catalog: name, category, optional settings (unit, unilateral, load). Source of truth for exercise seed. |
| **logic.yaml** | `patterns` (main, accessory, core), `pattern_priority`, `thresholds` (energy/knee_pain bands), `power_selection`, `relationships` (PATTERN:TIER). |
| **sessions.yaml** | **GYM** structure (PREP, POWER, STRENGTH, ACCESSORIES, CONDITIONING) and **RECOVERY** (Red Day): `mobility_flow`, `repair_isometrics`, accessories, steady-state conditioning. |
| **selections.yaml** | Exercise mappings by pattern, tier, and state (GREEN/ORANGE/RED); used by the engine for session composition. |
| **conditioning.yaml** | Conditioning protocols (SIT, HIIT, SS) and equipment. Seeded into DB via `src.db.seeds`. |

Readiness state is derived from `logic.thresholds` (energy and knee_pain bands). When state is **RED**, the recommend endpoint returns a Red Day session (mobility, isometrics, balanced push/pull, Zone 2); no separate conditioning block is appended. Edit the YAML files to change exercises, progressions, or session structure without code changes.

## Database Migrations

### Creating a new migration
```bash
cd backend
uv run alembic revision --autogenerate -m "Description of changes"
```

### Applying migrations
```bash
uv run alembic upgrade head
```

## Code Quality

This project uses:
- **Ruff** for linting and formatting (Google style guide + PEP 8)
- **Pydantic** for strict schema validation
- **SQLModel** for database models
- **pytest** for testing

## Technology Stack

**Backend:** FastAPI, Uvicorn, SQLModel (Async), PostgreSQL, Alembic
**Frontend:** React Native (Expo), TypeScript, NativeWind v4, TanStack Query, AsyncStorage
