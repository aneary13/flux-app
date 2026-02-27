import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

from core.models import GenerateSessionRequest, StartSessionRequest, LogSetRequest, CompleteSessionRequest, UserStateResponse, PatternState
from core.resolver import WorkoutResolver
from services.system_init import auto_seed_database

# Load environment variables
load_dotenv()

# Configure startup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase Client
supabase_url = os.environ.get("SUPABASE_URL")
# IMPORTANT: For the API, we use the standard ANON key, not the service_role key.
supabase_key = os.environ.get("SUPABASE_KEY") 
supabase: Client = create_client(supabase_url, supabase_key)

DUMMY_USER_ID = "00000000-0000-0000-0000-000000000000"

# Set up the Lifespan Hook for robust initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Phase ---
    logger.info("FLUX Engine: Booting sequence initiated...")
    auto_seed_database(supabase, DUMMY_USER_ID)
    
    yield # Application serves requests here
    
    # --- Shutdown Phase ---
    logger.info("FLUX Engine: Shutting down gracefully...")

# Initialize FastAPI App WITH the lifespan hook
app = FastAPI(title="FLUX API", version="1.0.0", lifespan=lifespan)

# Set up CORS (allows your frontend to talk to this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, we will lock this down to your app's domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "FLUX Engine is Online"}

@app.get("/bootstrap")
def get_bootstrap_data():
    """
    Fetches the 'Brain' configs and the exercise library.
    This allows the frontend to cache the rules on app launch.
    """
    try:
        # 1. Fetch User Configs
        configs_response = supabase.table("user_configs").select("slug, data").eq("user_id", DUMMY_USER_ID).execute()
        
        # 2. Fetch Exercise Library
        exercises_response = supabase.table("exercises").select("*").execute()

        # 3. Format the data into a clean dictionary
        system_configs = {row["slug"]: row["data"] for row in configs_response.data}
        
        return {
            "configs": system_configs,
            "exercises": exercises_response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/state", response_model=UserStateResponse)
def get_user_state():
    """
    Fetches the user's current progression state and formats it as a View Model
    for the Homescreen. Performs datetime calculations on the backend.
    """
    try:
        response = supabase.table("user_configs").select("data").eq("user_id", DUMMY_USER_ID).eq("slug", "state").execute()
        
        # Fallback State
        raw_state = {
            "last_trained": {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None},
            "conditioning_levels": {"HIIT": 1, "SIT": 1}
        }
        
        if response.data and response.data[0].get("data"):
            raw_state = response.data[0]["data"]

        last_trained_data = raw_state.get("last_trained", {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None})
        now = datetime.now(timezone.utc)
        
        patterns_view = {}
        for pattern, timestamp_str in last_trained_data.items():
            if not timestamp_str:
                patterns_view[pattern] = PatternState(
                    last_trained_datetime=None,
                    days_since=None,
                    status_text="Fully Primed"
                )
            else:
                last_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                days_elapsed = (now - last_dt).days
                
                # Pure Server-Side View Logic
                if days_elapsed <= 1:
                    status = "Fatigued"
                elif days_elapsed <= 3:
                    status = "Recovering"
                else:
                    status = "Fully Primed"
                    
                patterns_view[pattern] = PatternState(
                    last_trained_datetime=timestamp_str,
                    days_since=days_elapsed,
                    status_text=status
                )

        return UserStateResponse(
            patterns=patterns_view,
            conditioning_levels=raw_state.get("conditioning_levels", {"HIIT": 1, "SIT": 1})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/generate")
def generate_workout_session(request: GenerateSessionRequest):
    """
    The core generation endpoint.
    """
    try:
        configs_response = supabase.table("user_configs").select("slug, data").eq("user_id", DUMMY_USER_ID).execute()
        system_configs = {row["slug"]: row["data"] for row in configs_response.data}
        
        exercises_response = supabase.table("exercises").select("*").execute()
        exercises_catalog = exercises_response.data

        resolver = WorkoutResolver(configs=system_configs, exercises=exercises_catalog)

        session_plan = resolver.generate_session(
            knee_pain=request.knee_pain,
            energy=request.energy,
            last_trained=request.last_trained,
            conditioning_levels=request.conditioning_levels
        )

        return session_plan

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/start")
def start_session(request: StartSessionRequest):
    """
    Creates a new session record. Evaluates readiness against the Brain 
    to securely determine the session archetype.
    """
    try:
        # 1. Fetch the logic configs to determine the rules
        configs_response = supabase.table("user_configs").select("slug, data").eq("user_id", DUMMY_USER_ID).execute()
        system_configs = {row["slug"]: row["data"] for row in configs_response.data}
        
        # 2. Extract readiness variables
        knee_pain = request.readiness.get("knee_pain", 0)
        energy = request.readiness.get("energy", 10)
        
        # 3. Consult the Brain
        # (We pass an empty list for exercises because we only need the triage logic here)
        resolver = WorkoutResolver(configs=system_configs, exercises=[])
        state, derived_archetype = resolver._evaluate_state(knee_pain=knee_pain, energy=energy)

        # 4. Create the Session Record
        session_data = {
            "user_id": DUMMY_USER_ID,
            "archetype": derived_archetype,  # The backend dictated this!
            "readiness": request.readiness,
            "status": "IN_PROGRESS"
        }
        
        response = supabase.table("workout_sessions").upsert(session_data).execute()
        
        if not response.data:
            raise Exception("Failed to start session.")
            
        return {
            "session_id": response.data[0]["id"],
            "derived_archetype": derived_archetype,
            "derived_state": state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/{session_id}/sets")
def log_atomic_set(session_id: str, request: LogSetRequest):
    """Logs a single set immediately to the database."""
    try:
        set_data = {
            "session_id": session_id,
            "exercise_name": request.exercise_name,
            "set_index": request.set_index,
            "weight": request.weight,
            "reps": request.reps,
            "seconds": request.seconds,
            "is_warmup": request.is_warmup,
            "is_benchmark": request.is_benchmark,
            "metadata": request.metadata
        }
        
        supabase.table("workout_sets").upsert(
            set_data,
            on_conflict="session_id, exercise_name, set_index"
        ).execute()
        return {"status": "Set logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/{session_id}/complete")
def complete_session(session_id: str, request: CompleteSessionRequest):
    """
    Finalizes the session and securely updates the UTC timestamp for the anchor pattern.
    """
    try:
        # 1. Update the Session Record with notes and timestamp
        update_data = {
            "status": "COMPLETED",
            "exercise_notes": request.exercise_notes,
            "summary_notes": request.summary_notes,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        supabase.table("workout_sessions").update(update_data).eq("id", session_id).execute()

        # 2. Fetch the user's current state
        state_response = supabase.table("user_configs").select("id, data").eq("user_id", DUMMY_USER_ID).eq("slug", "state").execute()
        
        if state_response.data:
            current_state = state_response.data[0]["data"]
            state_row_id = state_response.data[0]["id"]
        else:
            current_state = {
                "last_trained": {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None},
                "conditioning_levels": {"HIIT": 1, "SIT": 1}
            }
            state_row_id = None

        # Ensure schema structure exists
        if "last_trained" not in current_state:
            current_state["last_trained"] = {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None}

        # ---------------------------------------------------------
        # TODO: VERIFY WORK AGAINST ACTUAL SETS LOGGED
        # Currently, we blindly trust the frontend payload to progress levels.
        # Fix: Query the `workout_sets` table for this `session_id`. 
        # - Only reset anchor_pattern debt if a matching working set exists.
        # - Only bump conditioning level if a conditioning set exists.
        # This handles the "ran out of time at the gym" edge case.
        # ---------------------------------------------------------
        
        # 3. Update specific anchor pattern with UTC Now
        if request.anchor_pattern:
            current_state["last_trained"][request.anchor_pattern] = datetime.now(timezone.utc).isoformat()

        # 4. Recalculate conditioning (fully automatic linear progression)
        if request.completed_conditioning_protocol:
            protocol = request.completed_conditioning_protocol
            if "conditioning_levels" not in current_state:
                current_state["conditioning_levels"] = {}
            current_level = current_state["conditioning_levels"].get(protocol, 1)
            current_state["conditioning_levels"][protocol] = current_level + 1

        # 5. Save the new state to Supabase
        if state_row_id:
            supabase.table("user_configs").update({"data": current_state}).eq("id", state_row_id).execute()
        else:
            supabase.table("user_configs").upsert({
                "user_id": DUMMY_USER_ID,
                "slug": "state",
                "data": current_state
            }).execute()

        return {"status": "Session completed and progression state updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
