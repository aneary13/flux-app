# FLUX App

Phase 1: Logic Core Implementation

## Overview

FLUX app is an application that determines the "Next Best Action" for training sessions based on user readiness and training history, using an agile periodization approach rather than a fixed calendar.

## Project Structure

```
flux-app/
├── backend/
│   ├── src/
│   │   ├── models.py      # Pydantic models for config, input, output
│   │   └── engine.py       # WorkoutEngine class with core logic
│   ├── tests/
│   │   ├── test_models.py  # Test Pydantic validation
│   │   └── test_engine.py  # Test logic engine
│   ├── config/
│   │   └── program_config.yaml  # Configuration with archetypes, states, sessions
│   ├── pyproject.toml      # uv project config with dependencies
│   └── ruff.toml           # Ruff linting/formatting config
└── README.md
```

## Features

- **State Determination**: Evaluates user readiness (pain 0-10, energy 0-10) to determine state (RED/ORANGE/GREEN)
- **Priority Calculation**: Calculates priority scores for each training archetype based on how long ago it was last performed vs. ideal frequency
- **Session Generation**: Recommends the optimal training session based on state and priority

## Setup

### Prerequisites

- Python 3.13+
- `uv` package manager (by Astral)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
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

## Code Quality

This project uses:
- **Ruff** for linting and formatting (Google style guide + PEP 8)
- **Pydantic** for strict schema validation
- **pytest** for testing

Run linting:
```bash
cd backend
ruff check .
ruff format .
```
