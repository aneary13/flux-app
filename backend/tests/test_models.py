"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.models import (
    ArchetypeConfig,
    HistoryEntry,
    ProgramConfig,
    Readiness,
    SessionConfig,
    SessionPlan,
    StateConfig,
    TrainingHistory,
)


class TestReadiness:
    """Tests for Readiness model."""

    def test_valid_readiness(self) -> None:
        """Test valid readiness values."""
        readiness = Readiness(knee_pain=5, energy=7)
        assert readiness.knee_pain == 5
        assert readiness.energy == 7

    def test_readiness_boundary_values(self) -> None:
        """Test boundary values (0 and 10)."""
        readiness_min = Readiness(knee_pain=0, energy=0)
        assert readiness_min.knee_pain == 0
        assert readiness_min.energy == 0

        readiness_max = Readiness(knee_pain=10, energy=10)
        assert readiness_max.knee_pain == 10
        assert readiness_max.energy == 10

    def test_readiness_invalid_range(self) -> None:
        """Test invalid range values."""
        with pytest.raises(ValidationError):
            Readiness(knee_pain=11, energy=5)

        with pytest.raises(ValidationError):
            Readiness(knee_pain=5, energy=-1)

    def test_readiness_missing_fields(self) -> None:
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            Readiness(knee_pain=5)  # type: ignore


class TestTrainingHistory:
    """Tests for TrainingHistory model."""

    def test_empty_history(self) -> None:
        """Test empty training history."""
        history = TrainingHistory()
        assert history.entries == []

    def test_history_with_entries(self) -> None:
        """Test history with entries."""
        from datetime import date

        entry1 = HistoryEntry(archetype="Strength_Type_A", date=date(2024, 1, 1))
        entry2 = HistoryEntry(archetype="Cardio_Type_B", date=date(2024, 1, 3))
        history = TrainingHistory(entries=[entry1, entry2])
        assert len(history.entries) == 2


class TestConfigModels:
    """Tests for configuration models."""

    def test_archetype_config(self) -> None:
        """Test ArchetypeConfig validation."""
        archetype = ArchetypeConfig(name="Strength_Type_A", ideal_frequency_days=3)
        assert archetype.name == "Strength_Type_A"
        assert archetype.ideal_frequency_days == 3

    def test_archetype_invalid_frequency(self) -> None:
        """Test invalid frequency (must be > 0)."""
        with pytest.raises(ValidationError):
            ArchetypeConfig(name="Test", ideal_frequency_days=0)

        with pytest.raises(ValidationError):
            ArchetypeConfig(name="Test", ideal_frequency_days=-1)

    def test_state_config(self) -> None:
        """Test StateConfig validation."""
        state = StateConfig(name="RED", condition="knee_pain >= 6")
        assert state.name == "RED"
        assert state.condition == "knee_pain >= 6"

    def test_session_config(self) -> None:
        """Test SessionConfig validation."""
        session = SessionConfig(
            archetype="Strength_Type_A",
            name="Upper Body",
            allowed_states=["GREEN", "ORANGE"],
            exercises=["Bench Press", "Rows"],
        )
        assert session.archetype == "Strength_Type_A"
        assert session.name == "Upper Body"
        assert len(session.allowed_states) == 2
        assert len(session.exercises) == 2

    def test_program_config(self) -> None:
        """Test ProgramConfig with all components."""
        archetype = ArchetypeConfig(name="Strength_Type_A", ideal_frequency_days=3)
        state = StateConfig(name="RED", condition="knee_pain >= 6")
        session = SessionConfig(
            archetype="Strength_Type_A",
            name="Upper Body",
            allowed_states=["GREEN"],
            exercises=["Bench Press"],
        )

        config = ProgramConfig(
            archetypes=[archetype], states=[state], sessions=[session]
        )
        assert len(config.archetypes) == 1
        assert len(config.states) == 1
        assert len(config.sessions) == 1


class TestSessionPlan:
    """Tests for SessionPlan output model."""

    def test_session_plan(self) -> None:
        """Test SessionPlan creation."""
        plan = SessionPlan(
            archetype="Strength_Type_A",
            session_name="Upper Body",
            exercises=["Bench Press", "Rows"],
            priority_score=1.67,
        )
        assert plan.archetype == "Strength_Type_A"
        assert plan.session_name == "Upper Body"
        assert len(plan.exercises) == 2
        assert plan.priority_score == 1.67
