from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

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
    catalog: List[ExerciseItem]

# -----------------------------
# User Config Models
# -----------------------------
class UserConfigPayload(BaseModel):
    user_id: str
    slug: str
    data: Dict[str, Any]

# -----------------------------
# API Request Models
# -----------------------------
class GenerateSessionRequest(BaseModel):
    knee_pain: int
    energy: int
    last_trained: Dict[str, Optional[str]] = Field(default_factory=dict)
    conditioning_levels: Dict[str, int] = Field(default_factory=dict)
    benchmarks: Dict[str, Any] = Field(default_factory=dict)

class StartSessionRequest(BaseModel):
    readiness: Dict[str, int]

class LogSetRequest(BaseModel):
    exercise_name: str
    set_index: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    seconds: Optional[int] = None
    is_warmup: bool = False
    is_benchmark: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CompleteSessionRequest(BaseModel):
    exercise_notes: Dict[str, str] = Field(default_factory=dict)
    summary_notes: Optional[str] = None
    anchor_pattern: Optional[str] = None
    completed_conditioning_protocol: Optional[str] = None

# -----------------------------
# API Response Models (View Models)
# -----------------------------
class PatternState(BaseModel):
    last_trained_datetime: Optional[str]
    days_since: Optional[int]
    status_text: str

class UserStateResponse(BaseModel):
    patterns: Dict[str, PatternState]
    conditioning_levels: Dict[str, int]
