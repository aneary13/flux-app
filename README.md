# FLUX App

## Overview

FLUX app is an application that determines the "Next Best Action" for training sessions based on user readiness and training history, using an agile periodization approach rather than a fixed calendar.

## Project Structure

```
flux-app/
├── backend/
│   ├── src/
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # SQLModel database tables
│   │   │   └── session.py     # Async database session management
│   │   ├── models.py          # Pydantic models for config, input, output
│   │   └── engine.py          # WorkoutEngine class with core logic
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

## Setup

### Prerequisites

- Python 3.13+
- `uv` package manager (by Astral)
- PostgreSQL database (e.g., Supabase)

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

## Usage

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

- **ORM**: SQLModel (async) - Combines Pydantic and SQLAlchemy
- **Database**: PostgreSQL (via asyncpg driver)
- **Migrations**: Alembic with async support
- **Configuration**: python-dotenv for environment variables
