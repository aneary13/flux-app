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
│   │   │       └── workouts.py   # Workout recommendation endpoints
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # SQLModel database tables
│   │   │   └── session.py     # Async database session management
│   │   ├── models.py          # Pydantic models for config, input, output
│   │   ├── engine.py          # WorkoutEngine class with core logic
│   │   └── main.py            # FastAPI application entry point
│   ├── alembic/
│   │   ├── versions/          # Database migration files
│   │   ├── env.py             # Alembic configuration for async SQLModel
│   │   ├── script.py.mako     # Migration template
│   │   └── alembic.ini        # Alembic configuration
│   ├── tests/
│   │   ├── test_models.py      # Test Pydantic validation
│   │   └── test_engine.py     # Test logic engine
│   ├── config/
│   │   └── program_config.yaml  # Program config: patterns, library, session_structure, states
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

### Phase 1: Logic Core
- **State Determination**: Evaluates user readiness (pain 0-10, energy 0-10) to determine state (RED/ORANGE/GREEN).
- **Session Generation**: Recommends the optimal training session based on state and history.

### Phase 6: Agile Training Logic (v2.0)
- **Pattern Debt Tracking**: Calculates days since last performance for each movement pattern; supports legacy data (handles `None`/empty `impacted_patterns`).
- **Session Type Selection**: Chooses REST, GYM, or CONDITIONING based on energy and pattern debt (Level 1 logic).
- **Block-by-Block Composition**: Builds GYM sessions from PREP (PATELLAR_ISO, CORE), POWER (RFD), STRENGTH (main lift), and ACCESSORIES (relationship-based).
- **Configurable Program**: YAML-driven library (patterns, tiers, states), `session_structure`, `power_selection`, and configurable **PATELLAR_ISO** (e.g. first exercise such as "SL Wall Sit").
- **Backward Compatibility**: SessionPlan exposes `exercises`, `session_name`, and `archetype` as computed fields for the frontend.

### Phase 2: Data Layer
- **Database Models**: SQLModel tables for exercises, daily readiness logs, workout sessions, and workout sets.
- **Async Database Operations**: High-performance async database connections using asyncpg.
- **Database Migrations**: Alembic integration for schema versioning and migrations.
- **Relationships**: SQLModel relationships for easy data access (e.g., `WorkoutSession.sets`).

### Phase 3: API Layer
- **FastAPI Application**: RESTful API exposing WorkoutEngine logic and database operations.
- **Dependency Injection**: Clean separation of concerns with reusable dependencies.
- **Readiness Endpoints**: Record daily readiness check-ins with upsert support.
- **Exercise Management**: List and seed exercises from configuration.
- **Workout Recommendations**: Generate personalized workout plans based on readiness and history.
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration.
- **User Identification**: Header-based user ID extraction (ready for authentication upgrade).

### Phase 4: Frontend Application
- **React Native Expo App**: Cross-platform mobile application with TypeScript.
- **Expo Router**: File-based routing for navigation.
- **NativeWind v4**: Tailwind CSS styling for React Native.
- **TanStack Query**: Data fetching, caching, and state management.
- **User ID Persistence**: Automatic UUID generation and storage per device.
- **Daily Readiness Check-In**: Interactive UI for pain and energy level input.
- **Workout Plan Display**: Beautiful card-based UI showing recommended workouts.
- **Error Handling**: Graceful handling of 404 (Rest Day) and other API errors.
- **Platform Detection**: Automatic base URL configuration for Android/iOS simulators.

### Phase 5: Deployment
- **Backend Deployment**: Production-ready deployment configuration for Render.com.
- **Requirements File**: Standardized `requirements.txt` generated from `pyproject.toml` (excluding dev dependencies and local project references).
- **Production Start Script**: Automated migration and server startup script (`start.sh`).
- **Environment Variables**: Frontend support for production API URL via `EXPO_PUBLIC_API_URL`.
- **Deployment Documentation**: Comprehensive deployment guide (`DEPLOY.md`).
- **Automatic Migrations**: Database migrations run automatically on each deployment.

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

The backend uses `backend/config/program_config.yaml` to define:

- **patterns**: Main (SQUAT, HINGE, PUSH, PULL), accessory (e.g. LUNGE), and core (CORE).
- **relationships**: Which accessory patterns follow each main pattern (format: `PATTERN:TIER`, e.g. `PULL:ACCESSORY_HORIZONTAL`).
- **library**: Exercise matrix by pattern, tier, and state (GREEN/ORANGE/RED). Includes **PATELLAR_ISO** (configurable first exercise, e.g. "SL Wall Sit"), CORE (TRANSVERSE, SAGITTAL, FRONTAL), RFD (HIGH/LOW/UPPER), and all main/accessory exercises.
- **power_selection**: Which RFD type to use per state.
- **session_structure**: Order of PREP (WARM_UP, PATELLAR_ISO, CORE), POWER (RFD), STRENGTH, ACCESSORIES.
- **states**: Readiness state conditions (e.g. RED when `knee_pain >= 6`).

Edit the YAML to change exercises, progressions, or session structure without code changes.

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
