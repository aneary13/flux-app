"""Pydantic request/response schemas for FLUX API (Schema 3.0)."""

from __future__ import annotations

from datetime import date as dt_date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ReadinessLatest(BaseModel):
    """Latest daily readiness for the authenticated user (GET /readiness/latest)."""

    date: dt_date = Field(..., description="Date of the check-in")
    knee_pain: int = Field(..., ge=0, le=10, description="Knee pain level 0-10")
    energy_level: int = Field(..., ge=0, le=10, description="Energy level 0-10")
    computed_state: str = Field(..., description="RED, ORANGE, or GREEN")


class WorkoutSetCreate(BaseModel):
    """Schema for creating a single workout set (lift or conditioning)."""

    exercise_name: str = Field(..., max_length=255, description="Exercise name (resolved to exercise_id on save)")
    weight_kg: float | None = Field(default=None, gt=0, description="Weight in kg (optional for conditioning)")
    reps: int | None = Field(default=None, gt=0, description="Repetitions (optional for conditioning)")
    rpe: float | None = Field(default=None, ge=1, le=10, description="Rate of Perceived Exertion (optional)")
    set_order: int = Field(..., ge=0, description="Order within workout")
    # Conditioning / flexible fields
    distance_meters: float | None = Field(default=None, description="Distance in meters")
    work_seconds: int | None = Field(default=None, description="Work duration in seconds")
    rest_seconds: int | None = Field(default=None, description="Rest duration in seconds")
    watts_avg: int | None = Field(default=None)
    watts_peak: int | None = Field(default=None)
    is_benchmark: bool = Field(default=False)
    exercise_notes: str | None = Field(default=None)


class WorkoutSessionCreate(BaseModel):
    """Schema for creating a completed workout session (request body). All datetimes in UTC."""

    started_at: datetime = Field(..., description="Session start (UTC)")
    completed_at: datetime = Field(..., description="Session end (UTC)")
    readiness_score: int = Field(..., ge=1, le=10, description="User state before session (1-10)")
    computed_state: str | None = Field(
        default=None,
        description="Snapshot at start: RED, ORANGE, or GREEN (optional)",
    )
    session_notes: str | None = Field(default=None, description="Optional session notes")
    notes: str | None = Field(default=None, description="Deprecated: use session_notes")
    conditioning_tier_performed: str | None = Field(
        default=None,
        description="If session included conditioning finisher: SIT, HIIT, or SS (updates PatternHistory and ConditioningProgress)",
    )
    sets: list[WorkoutSetCreate] = Field(..., min_length=1, description="At least one set required")

    @model_validator(mode="after")
    def completed_after_start(self) -> "WorkoutSessionCreate":
        """Ensure completed_at is not before started_at."""
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must be >= started_at")
        return self

    @model_validator(mode="after")
    def notes_fallback(self) -> "WorkoutSessionCreate":
        """Use notes as session_notes if session_notes not set (backward compat)."""
        if self.session_notes is None and self.notes is not None:
            object.__setattr__(self, "session_notes", self.notes)
        return self


class WorkoutSetRead(BaseModel):
    """Schema for a single set in the response."""

    id: UUID
    exercise_id: int
    exercise_name: str
    weight_kg: float | None
    reps: int | None
    rpe: float | None
    set_order: int
    distance_meters: float | None = None
    work_seconds: int | None = None
    rest_seconds: int | None = None
    watts_avg: int | None = None
    watts_peak: int | None = None
    is_benchmark: bool = False
    exercise_notes: str | None = None


class WorkoutSessionRead(BaseModel):
    """Schema for a completed workout session (response)."""

    id: UUID
    user_id: UUID
    started_at: datetime
    completed_at: datetime
    readiness_score: int
    computed_state: str
    session_notes: str | None
    sets: list[WorkoutSetRead] = Field(default_factory=list)
