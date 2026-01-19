"""Tests for WorkoutEngine logic."""

from datetime import date, timedelta

import pytest

from src.engine import WorkoutEngine
from src.models import HistoryEntry, Readiness, TrainingHistory


@pytest.fixture
def config_path(tmp_path):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "program_config.yaml"
    config_file.write_text(
        """
archetypes:
  - name: "Strength_Type_A"
    ideal_frequency_days: 3
  - name: "Cardio_Type_B"
    ideal_frequency_days: 2

states:
  - name: "RED"
    condition: "knee_pain >= 6"
  - name: "ORANGE"
    condition: "(knee_pain >= 3) OR (energy <= 3)"
  - name: "GREEN"
    condition: "default"

sessions:
  - archetype: "Strength_Type_A"
    name: "Upper Body Strength"
    allowed_states: ["GREEN", "ORANGE"]
    exercises:
      - "Bench Press"
      - "Rows"
  - archetype: "Cardio_Type_B"
    name: "High Impact Cardio"
    allowed_states: ["GREEN"]
    exercises:
      - "Running"
      - "Jumping"
  - archetype: "Strength_Type_A"
    name: "Lower Body Strength"
    allowed_states: ["GREEN"]
    exercises:
      - "Squats"
      - "Deadlifts"
"""
    )
    return str(config_file)


@pytest.fixture
def engine(config_path):
    """Create a WorkoutEngine instance for testing."""
    return WorkoutEngine(config_path)


class TestStateDetermination:
    """Tests for determine_state method."""

    def test_red_state(self, engine: WorkoutEngine) -> None:
        """Test RED state determination (knee_pain >= 6)."""
        readiness = Readiness(knee_pain=6, energy=5)
        assert engine.determine_state(readiness) == "RED"

        readiness = Readiness(knee_pain=10, energy=10)
        assert engine.determine_state(readiness) == "RED"

    def test_orange_state_pain(self, engine: WorkoutEngine) -> None:
        """Test ORANGE state from pain condition (knee_pain >= 3)."""
        readiness = Readiness(knee_pain=3, energy=5)
        assert engine.determine_state(readiness) == "ORANGE"

        readiness = Readiness(knee_pain=5, energy=7)
        assert engine.determine_state(readiness) == "ORANGE"

    def test_orange_state_energy(self, engine: WorkoutEngine) -> None:
        """Test ORANGE state from energy condition (energy <= 3)."""
        readiness = Readiness(knee_pain=2, energy=3)
        assert engine.determine_state(readiness) == "ORANGE"

        readiness = Readiness(knee_pain=1, energy=0)
        assert engine.determine_state(readiness) == "ORANGE"

    def test_orange_state_both_conditions(self, engine: WorkoutEngine) -> None:
        """Test ORANGE state when both conditions are true."""
        readiness = Readiness(knee_pain=4, energy=2)
        assert engine.determine_state(readiness) == "ORANGE"

    def test_green_state(self, engine: WorkoutEngine) -> None:
        """Test GREEN state (default, low pain and decent energy)."""
        readiness = Readiness(knee_pain=2, energy=5)
        assert engine.determine_state(readiness) == "GREEN"

        readiness = Readiness(knee_pain=0, energy=10)
        assert engine.determine_state(readiness) == "GREEN"


class TestPriorityCalculation:
    """Tests for calculate_priority method."""

    def test_priority_with_history(self, engine: WorkoutEngine) -> None:
        """Test priority calculation with training history.

        Strength done 5 days ago (ideal=3) → priority = 5/3 = 1.67
        Cardio done 1 day ago (ideal=2) → priority = 1/2 = 0.5
        Strength should be recommended (higher priority).
        """
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    archetype="Strength_Type_A", date=today - timedelta(days=5)
                ),
                HistoryEntry(
                    archetype="Cardio_Type_B", date=today - timedelta(days=1)
                ),
            ]
        )

        priorities = engine.calculate_priority(history)
        assert len(priorities) == 2

        # Check that Strength has higher priority
        strength_priority = next(p for p in priorities if p[0] == "Strength_Type_A")
        cardio_priority = next(p for p in priorities if p[0] == "Cardio_Type_B")

        assert strength_priority[1] == pytest.approx(5.0 / 3.0, rel=1e-2)
        assert cardio_priority[1] == pytest.approx(1.0 / 2.0, rel=1e-2)
        assert strength_priority[1] > cardio_priority[1]

        # Check sorting (highest first)
        assert priorities[0][0] == "Strength_Type_A"

    def test_priority_no_history(self, engine: WorkoutEngine) -> None:
        """Test priority calculation with no history."""
        history = TrainingHistory()

        priorities = engine.calculate_priority(history)
        assert len(priorities) == 2

        # Both should be prioritized (ideal_frequency_days + 1)
        strength_priority = next(p for p in priorities if p[0] == "Strength_Type_A")
        cardio_priority = next(p for p in priorities if p[0] == "Cardio_Type_B")

        assert strength_priority[1] == pytest.approx(4.0 / 3.0, rel=1e-2)  # (3+1)/3
        assert cardio_priority[1] == pytest.approx(3.0 / 2.0, rel=1e-2)  # (2+1)/2

    def test_priority_multiple_entries_same_archetype(
        self, engine: WorkoutEngine
    ) -> None:
        """Test priority uses most recent date when multiple entries exist."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    archetype="Strength_Type_A", date=today - timedelta(days=10)
                ),
                HistoryEntry(
                    archetype="Strength_Type_A", date=today - timedelta(days=2)
                ),  # More recent
            ]
        )

        priorities = engine.calculate_priority(history)
        strength_priority = next(p for p in priorities if p[0] == "Strength_Type_A")

        # Should use most recent (2 days ago)
        assert strength_priority[1] == pytest.approx(2.0 / 3.0, rel=1e-2)


class TestSessionGeneration:
    """Tests for generate_session method."""

    def test_generate_session_priority_based(self, engine: WorkoutEngine) -> None:
        """Test that highest priority archetype is selected.

        Strength done 5 days ago (ideal=3), Cardio 1 day ago (ideal=2).
        Strength should be recommended.
        """
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    archetype="Strength_Type_A", date=today - timedelta(days=5)
                ),
                HistoryEntry(
                    archetype="Cardio_Type_B", date=today - timedelta(days=1)
                ),
            ]
        )
        readiness = Readiness(knee_pain=2, energy=7)  # GREEN state

        plan = engine.generate_session(readiness, history)

        assert plan.archetype == "Strength_Type_A"
        assert plan.priority_score == pytest.approx(5.0 / 3.0, rel=1e-2)

    def test_generate_session_state_filtering(self, engine: WorkoutEngine) -> None:
        """Test that RED state excludes High Impact sessions."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    archetype="Cardio_Type_B", date=today - timedelta(days=5)
                ),  # High priority
            ]
        )
        readiness = Readiness(knee_pain=7, energy=5)  # RED state

        # Cardio is high priority but not allowed in RED state
        # Cardio sessions are only allowed in GREEN, not RED
        # So no sessions should match and it should raise an error
        with pytest.raises(ValueError, match="No sessions found"):
            engine.generate_session(readiness, history)

    def test_generate_session_first_match_selected(
        self, engine: WorkoutEngine
    ) -> None:
        """Test that first matching session is selected when multiple match."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    archetype="Strength_Type_A", date=today - timedelta(days=5)
                ),
            ]
        )
        readiness = Readiness(knee_pain=2, energy=7)  # GREEN state

        plan = engine.generate_session(readiness, history)

        # Both "Upper Body Strength" and "Lower Body Strength" match
        # Should return first one from config ("Upper Body Strength")
        assert plan.archetype == "Strength_Type_A"
        assert plan.session_name == "Upper Body Strength"
        assert "Bench Press" in plan.exercises

    def test_generate_session_no_valid_session(self, engine: WorkoutEngine) -> None:
        """Test error when no valid session is found."""
        history = TrainingHistory()
        readiness = Readiness(knee_pain=8, energy=2)  # RED state

        # No sessions are allowed in RED state in our config
        with pytest.raises(ValueError, match="No sessions found"):
            engine.generate_session(readiness, history)

    def test_generate_session_green_state_allows_all(self, engine: WorkoutEngine) -> None:
        """Test that GREEN state allows all sessions."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    archetype="Cardio_Type_B", date=today - timedelta(days=5)
                ),
            ]
        )
        readiness = Readiness(knee_pain=1, energy=8)  # GREEN state

        plan = engine.generate_session(readiness, history)

        assert plan.archetype == "Cardio_Type_B"
        assert plan.session_name == "High Impact Cardio"
