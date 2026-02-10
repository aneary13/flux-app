"""SQLModel database models for FLUX application."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Text, UniqueConstraint
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel


class Exercise(SQLModel, table=True):
    """Reference table for exercises."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=255)
    category: str = Field(max_length=100, description="e.g., 'SQUAT', 'RFD' (pattern)")
    modality: str = Field(max_length=100, description="e.g., 'Barbell', 'Dumbbell', 'Bodyweight'")


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


class PatternInventory(SQLModel, table=True):
    """Per-user, per-pattern last-performed timestamp for debt calculation."""

    __table_args__ = (UniqueConstraint("user_id", "pattern", name="uq_pattern_inventory_user_pattern"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    pattern: str = Field(max_length=100, index=True, description="e.g., SQUAT, RFD")
    last_performed: datetime = Field(description="UTC timestamp when pattern was last performed")


class WorkoutSession(SQLModel, table=True):
    """Log table for completed workout sessions."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    started_at: datetime = Field(description="Session start (UTC)")
    completed_at: datetime = Field(description="Session end (UTC)")
    readiness_score: int = Field(ge=1, le=10, description="User state before session (1-10)")
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Relationships
    sets: list["WorkoutSet"] = Relationship(back_populates="workout")


class WorkoutSet(SQLModel, table=True):
    """Granular data table for individual workout sets."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="workoutsession.id")
    exercise_name: str = Field(max_length=255, description="Exercise name (decoupled from seed for custom exercises)")
    weight_kg: float = Field(description="Weight in kg")
    reps: int = Field(description="Repetitions")
    rpe: float | None = Field(default=None, description="Rate of Perceived Exertion (optional)")
    set_order: int = Field(description="Order within workout")

    # Relationships
    workout: "WorkoutSession" = Relationship(back_populates="sets")
