import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

from core.models import GenerateSessionRequest, StartSessionRequest, LogSetRequest, CompleteSessionRequest
from core.resolver import WorkoutResolver

# Load environment variables
load_dotenv()

# Initialize FastAPI App
app = FastAPI(title="FLUX API", version="1.0.0")

# Set up CORS (allows your frontend to talk to this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, we will lock this down to your app's domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase Client
supabase_url = os.environ.get("SUPABASE_URL")
# IMPORTANT: For the API, we use the standard ANON key, not the service_role key.
supabase_key = os.environ.get("SUPABASE_KEY") 
supabase: Client = create_client(supabase_url, supabase_key)

DUMMY_USER_ID = "00000000-0000-0000-0000-000000000000"

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

@app.get("/user/state")
def get_user_state():
    """
    Fetches the user's current progression state for the Homescreen.
    """
    try:
        response = supabase.table("user_configs").select("data").eq("user_id", DUMMY_USER_ID).eq("slug", "state").execute()
        
        if not response.data:
            return {
                "pattern_debts": {"SQUAT": 0, "PUSH": 0, "HINGE": 0, "PULL": 0},
                "conditioning_levels": {"HIIT": 1, "SIT": 1, "SS": 1}
            }
            
        return response.data[0]["data"]
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
            pattern_debts=request.pattern_debts,
            conditioning_levels=request.conditioning_levels # Updated parameter
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
    Finalizes the session and automatically recalculates Pattern Debt 
    and Conditioning Progression.
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

        # 2. Fetch the user's current State Document
        state_response = supabase.table("user_configs").select("id, data").eq("user_id", DUMMY_USER_ID).eq("slug", "state").execute()
        
        if state_response.data:
            current_state = state_response.data[0]["data"]
            state_row_id = state_response.data[0]["id"]
        else:
            # Fallback if no state exists yet
            current_state = {
                "pattern_debts": {"SQUAT": 0, "PUSH": 0, "HINGE": 0, "PULL": 0},
                "conditioning_levels": {"HIIT": 1, "SIT": 1, "SS": 1}
            }
            state_row_id = None

        # ---------------------------------------------------------
        # TODO: VERIFY WORK AGAINST ACTUAL SETS LOGGED
        # Currently, we blindly trust the frontend payload to progress levels.
        # Fix: Query the `workout_sets` table for this `session_id`. 
        # - Only reset anchor_pattern debt if a matching working set exists.
        # - Only bump conditioning level if a conditioning set exists.
        # This handles the "ran out of time at the gym" edge case.
        # ---------------------------------------------------------

        # 3. Recalculate Debts (Reset the completed pattern, +1 to the rest)
        if request.anchor_pattern:
            for pattern in current_state["pattern_debts"]:
                if pattern == request.anchor_pattern:
                    current_state["pattern_debts"][pattern] = 0 
                else:
                    current_state["pattern_debts"][pattern] += 1 

        # 4. Recalculate Conditioning (Fully automatic linear progression)
        if request.completed_conditioning_protocol:
            protocol = request.completed_conditioning_protocol
            
            # Ensure dictionary exists
            if "conditioning_levels" not in current_state:
                current_state["conditioning_levels"] = {}
                
            current_level = current_state["conditioning_levels"].get(protocol, 1)
            # You did the work, you automatically level up
            current_state["conditioning_levels"][protocol] = current_level + 1

        # 5. Save the New State Document to Supabase
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
