"""WorkoutEngine - Core logic for determining next best action."""

from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple

import yaml
from simpleeval import SimpleEval

from src.models import (
    HistoryEntry,
    ProgramConfig,
    Readiness,
    SessionPlan,
    TrainingHistory,
)


class WorkoutEngine:
    """Engine for determining the next best training session."""

    def __init__(self, config_path: str | Path) -> None:
        """Initialize engine with configuration file.

        Args:
            config_path: Path to program_config.yaml file
        """
        config_path = Path(config_path)
        with config_path.open() as f:
            config_data = yaml.safe_load(f)
        self.config = ProgramConfig(**config_data)

    def determine_state(self, readiness: Readiness) -> str:
        """Determine readiness state based on pain and energy levels.

        Evaluates state conditions in order (RED → ORANGE → GREEN).
        GREEN is the default catch-all if no previous states match.

        Args:
            readiness: User readiness with pain and energy levels

        Returns:
            State name ("RED", "ORANGE", or "GREEN")
        """
        # Create safe evaluator with only readiness fields
        evaluator = SimpleEval(names={"knee_pain": readiness.knee_pain, "energy": readiness.energy})

        # Evaluate states in order (RED → ORANGE → GREEN)
        for state in self.config.states:
            if state.condition.lower() == "default":
                # GREEN is the default catch-all
                return state.name

            try:
                # Normalize logical operators to lowercase for simpleeval
                condition = state.condition.replace(" OR ", " or ").replace(" AND ", " and ")
                result = evaluator.eval(condition)
                if result:
                    return state.name
            except Exception:
                # If evaluation fails, skip to next state
                continue

        # Fallback to GREEN if somehow no state matched
        return "GREEN"

    def calculate_priority(
        self, history: TrainingHistory
    ) -> List[Tuple[str, float]]:
        """Calculate priority scores for each archetype based on training history.

        Priority = days_since_last_session / ideal_frequency_days
        Higher score means more overdue and higher priority.

        Args:
            history: User training history

        Returns:
            Sorted list of (archetype_name, priority_score) tuples, highest first
        """
        today = date.today()
        priorities: List[Tuple[str, float]] = []

        # Group history entries by archetype and find most recent date for each
        archetype_last_dates: dict[str, date] = {}
        for entry in history.entries:
            if entry.archetype not in archetype_last_dates:
                archetype_last_dates[entry.archetype] = entry.date
            elif entry.date > archetype_last_dates[entry.archetype]:
                archetype_last_dates[entry.archetype] = entry.date

        # Calculate priority for each archetype in config
        for archetype in self.config.archetypes:
            if archetype.name in archetype_last_dates:
                last_date = archetype_last_dates[archetype.name]
                days_since_last = (today - last_date).days
            else:
                # No history - prioritize by setting days to ideal + 1
                days_since_last = archetype.ideal_frequency_days + 1

            priority_score = days_since_last / archetype.ideal_frequency_days
            priorities.append((archetype.name, priority_score))

        # Sort by priority score (highest first)
        priorities.sort(key=lambda x: x[1], reverse=True)
        return priorities

    def generate_session(
        self, readiness: Readiness, history: TrainingHistory
    ) -> SessionPlan:
        """Generate the recommended session plan.

        Args:
            readiness: User readiness with pain and energy levels
            history: User training history

        Returns:
            SessionPlan with recommended session details

        Raises:
            ValueError: If no valid session is found
        """
        # Determine current state
        current_state = self.determine_state(readiness)

        # Calculate priorities
        priorities = self.calculate_priority(history)

        if not priorities:
            raise ValueError("No archetypes configured")

        # Get top priority archetype
        top_archetype, top_priority = priorities[0]

        # Find sessions that match: (1) current state in allowed_states,
        # (2) archetype matches top priority
        matching_sessions = [
            session
            for session in self.config.sessions
            if current_state in session.allowed_states
            and session.archetype == top_archetype
        ]

        if not matching_sessions:
            raise ValueError(
                f"No sessions found for archetype '{top_archetype}' "
                f"in state '{current_state}'"
            )

        # Return first matching session (MVP: simple selection)
        session = matching_sessions[0]

        return SessionPlan(
            archetype=session.archetype,
            session_name=session.name,
            exercises=session.exercises,
            priority_score=top_priority,
        )
