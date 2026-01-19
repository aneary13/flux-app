"""Pydantic models for FLUX configuration, input, and output."""

from datetime import date
from typing import List

from pydantic import BaseModel, Field, field_validator


# Configuration Models (for YAML parsing)


class ArchetypeConfig(BaseModel):
    """Configuration for a training archetype."""

    name: str
    ideal_frequency_days: int = Field(gt=0, description="Ideal days between sessions")


class StateConfig(BaseModel):
    """Configuration for a readiness state."""

    name: str
    condition: str = Field(description="Condition expression or 'default'")


class SessionConfig(BaseModel):
    """Configuration for a training session."""

    archetype: str = Field(description="Archetype this session belongs to")
    name: str
    allowed_states: List[str] = Field(description="States this session is allowed in")
    exercises: List[str] = Field(description="List of exercises in this session")


class ProgramConfig(BaseModel):
    """Root configuration model for the program."""

    archetypes: List[ArchetypeConfig]
    states: List[StateConfig]
    sessions: List[SessionConfig]


# Input Models


class Readiness(BaseModel):
    """User readiness input with pain and energy levels."""

    knee_pain: int = Field(ge=0, le=10, description="Knee pain level 0-10")
    energy: int = Field(ge=0, le=10, description="Energy level 0-10")

    @field_validator("knee_pain", "energy")
    @classmethod
    def validate_range(cls, v: int) -> int:
        """Validate that values are in the 0-10 range."""
        if not 0 <= v <= 10:
            raise ValueError("Value must be between 0 and 10")
        return v


class HistoryEntry(BaseModel):
    """A single training history entry."""

    archetype: str
    date: date


class TrainingHistory(BaseModel):
    """User training history."""

    entries: List[HistoryEntry] = Field(default_factory=list)


# Output Models


class SessionPlan(BaseModel):
    """Recommended session plan output."""

    archetype: str
    session_name: str
    exercises: List[str]
    priority_score: float = Field(description="Calculated priority score")

