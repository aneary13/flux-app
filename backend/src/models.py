"""Pydantic models for FLUX configuration, input, and output."""

from datetime import date
from typing import Dict, List

from pydantic import BaseModel, Field, computed_field, field_validator


# Configuration Models (for YAML parsing)


class PatternConfig(BaseModel):
    """Configuration for movement patterns."""

    main: List[str] = Field(description="Main movement patterns")
    accessory: List[str] = Field(description="Accessory movement patterns")
    core: List[str] = Field(description="Core movement patterns")


class PowerSelectionConfig(BaseModel):
    """Configuration for power exercise selection by state."""

    GREEN: str = Field(description="Power selection for GREEN state")
    ORANGE: str = Field(description="Power selection for ORANGE state")
    RED: str = Field(description="Power selection for RED state")


class SessionStructureConfig(BaseModel):
    """Configuration for session structure."""

    PREP: List[str] = Field(description="Prep block components")
    POWER: List[str] = Field(description="Power block components")
    STRENGTH: List[str] = Field(description="Strength block components")
    ACCESSORIES: List[str] = Field(description="Accessories block components")


class StateConfig(BaseModel):
    """Configuration for a readiness state."""

    name: str
    condition: str = Field(description="Condition expression or 'default'")


class ProgramConfig(BaseModel):
    """Root configuration model for the program."""

    patterns: PatternConfig
    relationships: Dict[str, List[str]] = Field(
        description="Pattern relationships for accessory selection (format: PATTERN:TIER)"
    )
    library: Dict[str, Dict[str, Dict[str, str] | List[str]]] = Field(
        description="Exercise library: [Pattern][Tier][State] -> exercise name, or [Pattern][Tier] -> list (for RFD)"
    )
    power_selection: PowerSelectionConfig
    session_structure: SessionStructureConfig
    states: List[StateConfig]


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

    impacted_patterns: List[str] = Field(
        description="List of movement patterns impacted by this session"
    )
    date: date


class TrainingHistory(BaseModel):
    """User training history."""

    entries: List[HistoryEntry] = Field(default_factory=list)


# Output Models


class ExerciseBlock(BaseModel):
    """A single exercise block within a session."""

    block_type: str = Field(
        description="Block type: PREP, POWER, MAIN, ACCESSORY_1, ACCESSORY_2"
    )
    exercise_name: str = Field(description="Name of the exercise")
    pattern: str | None = Field(
        default=None, description="Movement pattern for debt tracking"
    )


class SessionPlan(BaseModel):
    """Recommended session plan output."""

    session_type: str = Field(description="Session type: GYM, CONDITIONING, or REST")
    blocks: List[ExerciseBlock] = Field(description="List of exercise blocks")

    @computed_field
    @property
    def exercises(self) -> List[str]:
        """Extract exercise names from blocks for frontend compatibility."""
        return [block.exercise_name for block in self.blocks]

    @computed_field
    @property
    def session_name(self) -> str:
        """Generate session name from main lift for frontend compatibility."""
        main_block = next((b for b in self.blocks if b.block_type == "MAIN"), None)
        if main_block:
            return f"{self.session_type}: {main_block.exercise_name}"
        return f"{self.session_type}: General"

    @computed_field
    @property
    def archetype(self) -> str:
        """Map session_type to archetype for backward compatibility."""
        return self.session_type

    priority_score: float = Field(
        default=0.0, description="Calculated priority score (for backward compatibility)"
    )
