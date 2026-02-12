"""SQLModel database models for FLUX application (Schema 3.0)."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """Central user profile and anchor for all foreign keys."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    first_name: str = Field(max_length=255, default="")
    last_name: str = Field(max_length=255, default="")
    email: str = Field(unique=True, index=True, max_length=255)
    dob: date | None = Field(default=None)
    gender: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Exercise(SQLModel, table=True):
    """Reference table for exercises (catalog of all available movements)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=255)
    category: str = Field(max_length=100, description="e.g., 'SQUAT', 'PUSH', 'CONDITIONING'")
    modality: str = Field(max_length=100, description="e.g., 'Barbell', 'Machine'")
    tracking_unit: str = Field(default="REPS", max_length=20)  # REPS, SECS, METERS, WATTS
    is_unilateral: bool = Field(default=False)
    is_bodyweight: bool = Field(default=False)

    # Relationships
    workout_sets: list["WorkoutSet"] = Relationship(back_populates="exercise")


class ConditioningProtocol(SQLModel, table=True):
    """Reference table: static 'recipes' from the Gassed to Ready program."""

    id: int | None = Field(default=None, primary_key=True)
    tier: str = Field(max_length=20, description="SIT, HIIT, SS")
    level: int = Field(ge=1, le=8)
    description: str = Field(max_length=500)
    work_duration: int | None = Field(default=None, description="Seconds")
    rest_duration: int | None = Field(default=None, description="Seconds")
    rounds: int = Field(default=1)
    target_modifier: str | None = Field(default=None, max_length=100, description="e.g. BENCHMARK_1.2")


class PatternHistory(SQLModel, table=True):
    """Tracks 'When did I last do X?' for all movement types (renamed from PatternInventory)."""

    __tablename__ = "patternhistory"
    __table_args__ = (UniqueConstraint("user_id", "pattern", name="uq_pattern_history_user_pattern"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    pattern: str = Field(max_length=150, index=True, description="e.g. SQUAT:MAIN, CONDITIONING:SIT")
    last_performed: datetime = Field(
        description="UTC timestamp when pattern was last performed",
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ConditioningBenchmark(SQLModel, table=True):
    """Log table: benchmark test results used to calculate future targets."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    date: date
    benchmark_type: str = Field(max_length=50, description="e.g. 2_MILE_TT, MAX_WATTS_30S, RAMP_TEST")
    equipment: str = Field(max_length=100)
    result_metric: float = Field(description="Primary score used for calc (e.g. Avg Watts)")
    peak_watts: int | None = None
    avg_hr: int | None = None
    peak_hr: int | None = None
    hr_recovery: int | None = None
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class ConditioningProgress(SQLModel, table=True):
    """Tracks user's current conditioning difficulty level (game save)."""

    user_id: UUID = Field(primary_key=True)  # No FK to User table (allow anonymous)
    sit_level: int = Field(default=1, ge=1, le=8)
    hiit_level: int = Field(default=1, ge=1, le=8)
    last_tier_performed: str = Field(default="NONE", max_length=20)  # SIT, HIIT, NONE
    last_performed: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


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
    """Log table for completed workout sessions."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    started_at: datetime = Field(
        description="Session start (UTC)",
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime = Field(
        description="Session end (UTC)",
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    computed_state: str = Field(max_length=50, description="Snapshot of state at start (RED/ORANGE/GREEN)")
    readiness_score: int = Field(ge=1, le=10, description="User state before session (1-10)")
    session_notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Relationships
    sets: list["WorkoutSet"] = Relationship(back_populates="workout")


class WorkoutSet(SQLModel, table=True):
    """Granular data table for individual workout sets (lifts, runs, sprints)."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="workoutsession.id")
    exercise_id: int = Field(foreign_key="exercise.id")
    set_order: int = Field(description="Order within workout")

    # Flexible metrics (all nullable)
    weight_kg: float | None = None
    reps: int | None = None
    rpe: float | None = None
    distance_meters: float | None = None
    work_seconds: int | None = None
    rest_seconds: int | None = None
    watts_avg: int | None = None
    watts_peak: int | None = None
    hr_avg: int | None = None
    hr_peak: int | None = None
    is_benchmark: bool = Field(default=False)
    exercise_notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Relationships
    workout: "WorkoutSession" = Relationship(back_populates="sets")
    exercise: "Exercise" = Relationship(back_populates="workout_sets")


