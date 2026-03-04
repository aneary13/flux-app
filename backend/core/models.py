from typing import Any

from pydantic import BaseModel, Field


# -----------------------------
# Exercise Library Models
# -----------------------------
class ExerciseSettings(BaseModel):
    unilateral: bool
    load: str
    unit: str


class ExerciseItem(BaseModel):
    name: str
    settings: ExerciseSettings


class LibraryConfig(BaseModel):
    catalog: list[ExerciseItem]


# -----------------------------
# User Config Models
# -----------------------------
class UserConfigPayload(BaseModel):
    user_id: str
    slug: str
    data: dict[str, Any]


# -----------------------------
# API Request Models
# -----------------------------
class GenerateSessionRequest(BaseModel):
    knee_pain: int
    energy: int
    last_trained: dict[str, str | None] = Field(default_factory=dict)
    conditioning_levels: dict[str, int] = Field(default_factory=dict)
    benchmarks: dict[str, Any] = Field(default_factory=dict)


class StartSessionRequest(BaseModel):
    readiness: dict[str, int]


class LogSetRequest(BaseModel):
    exercise_name: str
    set_index: int
    weight: float | None = None
    reps: int | None = None
    seconds: int | None = None
    is_warmup: bool = False
    is_benchmark: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompleteSessionRequest(BaseModel):
    exercise_notes: dict[str, str] = Field(default_factory=dict)
    summary_notes: str | None = None
    anchor_pattern: str | None = None
    completed_conditioning_protocol: str | None = None


# -----------------------------
# API Response Models (View Models)
# -----------------------------
class PatternState(BaseModel):
    last_trained_datetime: str | None
    days_since: int | None
    status_text: str


class UserStateResponse(BaseModel):
    patterns: dict[str, PatternState]
    conditioning_levels: dict[str, int]
