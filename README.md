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
│   │   └── program_config.yaml  # Configuration with archetypes, states, sessions
│   ├── .env.example           # Environment variables template
│   ├── pyproject.toml         # uv project config with dependencies
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
│   ├── global.css             # Tailwind CSS directives
│   ├── tailwind.config.js     # Tailwind configuration
│   ├── metro.config.js        # Metro bundler config with NativeWind
│   ├── babel.config.js        # Babel config with NativeWind plugin
│   └── package.json           # npm dependencies
└── README.md
```

## Features

### Phase 1: Logic Core
- **State Determination**: Evaluates user readiness (pain 0-10, energy 0-10) to determine state (RED/ORANGE/GREEN)
- **Priority Calculation**: Calculates priority scores for each training archetype based on how long ago it was last performed vs. ideal frequency
- **Session Generation**: Recommends the optimal training session based on state and priority

### Phase 2: Data Layer
- **Database Models**: SQLModel tables for exercises, daily readiness logs, workout sessions, and workout sets
- **Async Database Operations**: High-performance async database connections using asyncpg
- **Database Migrations**: Alembic integration for schema versioning and migrations
- **Relationships**: SQLModel relationships for easy data access (e.g., `WorkoutSession.sets`)

### Phase 3: API Layer
- **FastAPI Application**: RESTful API exposing WorkoutEngine logic and database operations
- **Dependency Injection**: Clean separation of concerns with reusable dependencies
- **Readiness Endpoints**: Record daily readiness check-ins with upsert support
- **Exercise Management**: List and seed exercises from configuration
- **Workout Recommendations**: Generate personalized workout plans based on readiness and history
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration
- **User Identification**: Header-based user ID extraction (ready for authentication upgrade)

### Phase 4: Frontend Application
- **React Native Expo App**: Cross-platform mobile application with TypeScript
- **Expo Router**: File-based routing for navigation
- **NativeWind v4**: Tailwind CSS styling for React Native
- **TanStack Query**: Data fetching, caching, and state management
- **User ID Persistence**: Automatic UUID generation and storage per device
- **Daily Readiness Check-In**: Interactive UI for pain and energy level input
- **Workout Plan Display**: Beautiful card-based UI showing recommended workouts
- **Error Handling**: Graceful handling of 404 (Rest Day) and other API errors
- **Platform Detection**: Automatic base URL configuration for Android/iOS simulators

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

### Installation

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
   # Edit .env and add your DATABASE_URL
   # Format: DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   ```

4. Run database migrations:
   ```bash
   uv run alembic upgrade head
   ```

5. Activate the virtual environment (optional):
   ```bash
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Start the Expo development server:
   ```bash
   npm start
   # or
   yarn start
   ```

4. Run on iOS simulator:
   ```bash
   npm run ios
   ```

5. Run on Android emulator:
   ```bash
   npm run android
   ```

## Usage

### Running the Application

**Start the Backend API Server:**

Start the FastAPI server:

```bash
cd backend
uv run uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`
Alternative docs (ReDoc): `http://localhost:8000/redoc`

**Start the Frontend Mobile App:**

In a separate terminal, navigate to the frontend directory and start Expo:

```bash
cd frontend
npm start
```

Then press `i` for iOS simulator or `a` for Android emulator, or scan the QR code with the Expo Go app on your physical device.

**Note:** The frontend automatically detects the platform and uses:
- `http://localhost:8000` for iOS Simulator
- `http://10.0.2.2:8000` for Android Emulator

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

#### List Exercises
```http
GET /api/v1/exercises/
```
Returns: List of all exercises in the database

#### Seed Exercises
```http
POST /api/v1/exercises/seed
```
Populates the database with exercises from `program_config.yaml`

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

### Programmatic Usage (Direct Engine)

You can also use the engine directly in Python:

```python
from src.engine import WorkoutEngine
from src.models import Readiness, TrainingHistory, HistoryEntry
from datetime import date, timedelta

# Initialize engine with config
engine = WorkoutEngine("config/program_config.yaml")

# Create readiness input
readiness = Readiness(knee_pain=2, energy=7)

# Create training history
today = date.today()
history = TrainingHistory(
    entries=[
        HistoryEntry(archetype="Strength_Type_A", date=today - timedelta(days=5)),
    ]
)

# Generate session plan
plan = engine.generate_session(readiness, history)
print(f"Recommended: {plan.session_name}")
print(f"Exercises: {plan.exercises}")
print(f"Priority Score: {plan.priority_score}")
```

## Testing

Run tests with pytest:

```bash
cd backend
pytest
```

## Configuration

Edit `backend/config/program_config.yaml` to customize:

- **Archetypes**: Training types with ideal frequency (days between sessions)
- **States**: Readiness states (RED/ORANGE/GREEN) with condition expressions
- **Sessions**: Training sessions with allowed states and exercises

## Database Migrations

### Creating a new migration

After modifying database models in `src/db/models.py`:

```bash
cd backend
uv run alembic revision --autogenerate -m "Description of changes"
```

### Applying migrations

```bash
uv run alembic upgrade head
```

### Rolling back migrations

```bash
uv run alembic downgrade -1  # Roll back one migration
```

## Code Quality

This project uses:
- **Ruff** for linting and formatting (Google style guide + PEP 8)
- **Pydantic** for strict schema validation (Phase 1: business logic)
- **SQLModel** for database models (Phase 2: persistence)
- **pytest** for testing

Run linting:
```bash
cd backend
ruff check .
ruff format .
```

## Technology Stack

**Backend:**
- **API Framework**: FastAPI - Modern, fast web framework for building APIs
- **ASGI Server**: Uvicorn - Lightning-fast ASGI server
- **ORM**: SQLModel (async) - Combines Pydantic and SQLAlchemy
- **Database**: PostgreSQL (via asyncpg driver)
- **Migrations**: Alembic with async support
- **Configuration**: python-dotenv for environment variables

**Frontend:**
- **Framework**: React Native with Expo (Managed workflow)
- **Language**: TypeScript
- **Routing**: Expo Router (File-based routing)
- **Styling**: NativeWind v4 (Tailwind CSS for React Native)
- **Data Fetching**: TanStack Query (React Query) + Axios
- **State Management**: TanStack Query for server state
- **Storage**: AsyncStorage for user ID persistence
