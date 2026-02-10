"""SQLModel database models for FLUX application."""

from datetime import date, datetime
from typing import List
from uuid import UUID

from sqlalchemy import Column, JSON, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Exercise(SQLModel, table=True):
    """Reference table for exercises."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=255)
    category: str = Field(max_length=100, description="e.g., 'Upper', 'Lower', 'Full Body'")
    modality: str = Field(max_length=100, description="e.g., 'Barbell', 'Dumbbell', 'Bodyweight'")

    # Relationships
    workout_sets: list["WorkoutSet"] = Relationship(back_populates="exercise")


class DailyReadiness(SQLModel, table=True):
    """Log table for daily user readiness assessments."""

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_readiness_user_date"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    date: date
    knee_pain: int = Field(ge=0, le=10, description="Knee pain level 0-10")
    energy_level: int = Field(ge=0, le=10, description="Energy level 0-10")
    computed_state: str = Field(max_length=50, description="e.g., 'RED', 'ORANGE', 'GREEN'")


class WorkoutSession(SQLModel, table=True):
    """Log table for workout sessions."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(index=True)
    date: datetime
    session_type: str | None = Field(
        default=None,
        max_length=50,
        description="Session type: GYM, CONDITIONING, or REST",
        sa_column=Column(String(50), nullable=True),
    )
    impacted_patterns: List[str] | None = Field(
        default=None,
        description="List of movement patterns impacted by this session",
        sa_column=Column(JSON, nullable=True),
    )
    duration_minutes: int | None = Field(default=None, nullable=True)

    # Relationships
    sets: list["WorkoutSet"] = Relationship(back_populates="workout")


class WorkoutSet(SQLModel, table=True):
    """Granular data table for individual workout sets."""

    id: int | None = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workoutsession.id")
    exercise_id: int = Field(foreign_key="exercise.id")
    set_order: int = Field(description="Order within workout")
    weight_kg: float | None = Field(default=None, nullable=True)
    reps: int | None = Field(default=None, nullable=True)
    rpe: int | None = Field(
        default=None, nullable=True, description="Rate of Perceived Exertion"
    )
    superset_group_id: int | None = Field(
        default=None, nullable=True, description="For grouping exercises in supersets"
    )

    # Relationships
    workout: "WorkoutSession" = Relationship(back_populates="sets")
    exercise: "Exercise" = Relationship(back_populates="workout_sets")
