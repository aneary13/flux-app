from pydantic import BaseModel
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
# Since the logic, sessions, selections, and conditioning files are highly nested,
# we will treat them as flexible dictionaries at the root level for now, 
# while strictly typing the Exercise Library.
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
    pattern_debts: Dict[str, int] = {}
    conditioning_levels: Dict[str, int] = {}

class StartSessionRequest(BaseModel):
    readiness: Dict[str, int]

class LogSetRequest(BaseModel):
    exercise_name: str
    weight: Optional[float] = None
    reps: Optional[int] = None
    seconds: Optional[int] = None
    is_warmup: bool = False
    is_benchmark: bool = False

class CompleteSessionRequest(BaseModel):
    exercise_notes: Dict[str, str] = {}
    summary_notes: Optional[str] = None
    anchor_pattern: Optional[str] = None  # e.g., "SQUAT"
    completed_conditioning_protocol: Optional[str] = None # e.g., "HIIT"
