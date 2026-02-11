"""Pydantic request/response schemas for FLUX API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class WorkoutSetCreate(BaseModel):
    """Schema for creating a single workout set."""

    exercise_name: str = Field(..., max_length=255, description="Exercise name")
    weight_kg: float = Field(..., gt=0, description="Weight in kg")
    reps: int = Field(..., gt=0, description="Repetitions")
    rpe: float | None = Field(default=None, ge=1, le=10, description="Rate of Perceived Exertion (optional)")
    set_order: int = Field(..., ge=0, description="Order within workout")


class WorkoutSessionCreate(BaseModel):
    """Schema for creating a completed workout session (request body). All datetimes in UTC."""

    started_at: datetime = Field(..., description="Session start (UTC)")
    completed_at: datetime = Field(..., description="Session end (UTC)")
    readiness_score: int = Field(..., ge=1, le=10, description="User state before session (1-10)")
    notes: str | None = Field(default=None, description="Optional session notes")
    sets: list[WorkoutSetCreate] = Field(..., min_length=1, description="At least one set required")

    @model_validator(mode="after")
    def completed_after_start(self) -> "WorkoutSessionCreate":
        """Ensure completed_at is not before started_at."""
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must be >= started_at")
        return self


class WorkoutSetRead(BaseModel):
    """Schema for a single set in the response."""

    id: UUID
    exercise_name: str
    weight_kg: float
    reps: int
    rpe: float | None
    set_order: int


class WorkoutSessionRead(BaseModel):
    """Schema for a completed workout session (response)."""

    id: UUID
    user_id: UUID
    started_at: datetime
    completed_at: datetime
    readiness_score: int
    notes: str | None
    sets: list[WorkoutSetRead] = Field(default_factory=list)
