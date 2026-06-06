import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from supabase import Client, create_client

from core.models import (
    AIResponse,
    CompleteSessionRequest,
    GeneratedSessionResponse,
    GenerateSessionRequest,
    LogSetRequest,
    PatternState,
    StartSessionRequest,
    UserStateResponse,
)
from core.resolver import WorkoutResolver
from services.system_init import auto_seed_database

# Load environment variables
load_dotenv()

# Configure startup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase Client (Added empty string fallbacks for strict typing)
supabase_url = os.environ.get("SUPABASE_URL", "")
# IMPORTANT: For the API, we use the standard ANON key, not the service_role key.
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(supabase_url, supabase_key)

DUMMY_USER_ID = "00000000-0000-0000-0000-000000000000"

# Groq client for the AI Coach endpoint
groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY", ""))
_COACH_FALLBACK = AIResponse(
    greeting="Great to see you!", message="Whenever you're ready, let's get after today's session."
)


# Set up the Lifespan Hook for robust initialization
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # --- Startup Phase ---
    logger.info("FLUX Engine: Booting sequence initiated...")
    auto_seed_database(supabase, DUMMY_USER_ID)

    yield  # Application serves requests here

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
def read_root() -> dict[str, str]:
    return {"status": "FLUX Engine is Online"}


@app.get("/bootstrap")
def get_bootstrap_data() -> dict[str, Any]:
    """
    Fetches the 'Brain' configs and the exercise library.
    This allows the frontend to cache the rules on app launch.
    """
    try:
        # 1. Fetch User Configs
        configs_response = (
            supabase.table("user_configs")
            .select("slug, data")
            .eq("user_id", DUMMY_USER_ID)
            .execute()
        )

        # 2. Fetch Exercise Library
        exercises_response = supabase.table("exercises").select("*").execute()

        # 3. Format the data into a clean dictionary
        # Cast the response so Mypy knows it's a list of dicts
        configs_data = cast(list[dict[str, Any]], configs_response.data)
        system_configs = {row["slug"]: row["data"] for row in configs_data}

        exercises_data = cast(list[dict[str, Any]], exercises_response.data)

        return {"configs": system_configs, "exercises": exercises_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/user/state", response_model=UserStateResponse)
def get_user_state() -> UserStateResponse:
    """
    Fetches the user's current progression state and formats it as a View Model
    for the Homescreen. Performs datetime calculations on the backend.
    """
    try:
        # Fetch all user configs in one query (state + logic)
        configs_response = (
            supabase.table("user_configs")
            .select("slug, data")
            .eq("user_id", DUMMY_USER_ID)
            .execute()
        )
        configs_data = cast(list[dict[str, Any]], configs_response.data)
        configs_by_slug = {row["slug"]: row["data"] for row in configs_data}

        # Fallback State
        raw_state = configs_by_slug.get(
            "state",
            {
                "last_trained": {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None},
                "conditioning_levels": {"HIIT": 1, "SIT": 1},
            },
        )

        logic_config = configs_by_slug.get("logic", {})

        last_trained_data = cast(
            dict[str, str | None],
            raw_state.get(
                "last_trained", {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None}
            ),
        )

        cond_levels = cast(
            dict[str, int], raw_state.get("conditioning_levels", {"HIIT": 1, "SIT": 1})
        )

        now = datetime.now(UTC)
        patterns_view: dict[str, PatternState] = {}

        for pattern, timestamp_str in last_trained_data.items():
            if not timestamp_str:
                patterns_view[pattern] = PatternState(
                    last_trained_datetime=None,
                    days_since=None,
                    status_text="Fully Primed",
                    days_since_text="Untrained",
                )
            else:
                last_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                days_elapsed = (now - last_dt).days

                # Pure Server-Side View Logic
                if days_elapsed <= 1:
                    status = "Fatigued"
                elif days_elapsed <= 3:
                    status = "Recovering"
                else:
                    status = "Fully Primed"

                if days_elapsed == 0:
                    days_text = "Today"
                elif days_elapsed == 1:
                    days_text = "1 day ago"
                else:
                    days_text = f"{days_elapsed} days ago"

                patterns_view[pattern] = PatternState(
                    last_trained_datetime=timestamp_str,
                    days_since=days_elapsed,
                    status_text=status,
                    days_since_text=days_text,
                )

        # Derive next pattern from rotation order
        rotation = logic_config.get("rotation_order", ["SQUAT", "PUSH", "HINGE", "PULL"])
        next_pattern: str | None = None
        if all(v is None for v in last_trained_data.values()):
            next_pattern = rotation[0]
        else:
            most_recent_pattern = None
            most_recent_time: datetime | None = None
            for p in rotation:
                ts = last_trained_data.get(p)
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if most_recent_time is None or dt > most_recent_time:
                        most_recent_time = dt
                        most_recent_pattern = p
            if most_recent_pattern:
                idx = rotation.index(most_recent_pattern)
                next_pattern = rotation[(idx + 1) % len(rotation)]
            else:
                next_pattern = rotation[0]

        # Derive next conditioning protocol
        last_cond = raw_state.get("last_conditioning_protocol")
        if last_cond == "HIIT":
            next_cond = "SIT"
        elif last_cond == "SIT":
            next_cond = "HIIT"
        else:
            next_cond = "HIIT"

        return UserStateResponse(
            patterns=patterns_view,
            conditioning_levels=cond_levels,
            next_pattern=next_pattern,
            next_conditioning_protocol=next_cond,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/sessions/generate")
def generate_workout_session(request: GenerateSessionRequest) -> GeneratedSessionResponse:
    """
    The core generation endpoint.
    """
    try:
        configs_response = (
            supabase.table("user_configs")
            .select("slug, data")
            .eq("user_id", DUMMY_USER_ID)
            .execute()
        )
        configs_data = cast(list[dict[str, Any]], configs_response.data)
        system_configs = {row["slug"]: row["data"] for row in configs_data}

        # Extract flow_indices from the state doc (already fetched above alongside YAML configs)
        _default_flow_indices: dict[str, int] = {
            "mobility": 0,
            "extensive_plyo": 0,
            "intensive_plyo": 0,
            "core_plane": 0,
        }
        state_doc = system_configs.get("state", {})
        flow_indices = {**_default_flow_indices, **state_doc.get("flow_indices", {})}

        exercises_response = supabase.table("exercises").select("*").execute()
        exercises_catalog = cast(list[dict[str, Any]], exercises_response.data)

        resolver = WorkoutResolver(configs=system_configs, exercises=exercises_catalog)

        last_conditioning_protocol = state_doc.get("last_conditioning_protocol")

        session_plan = resolver.generate_session(
            knee_pain=request.knee_pain,
            energy=request.energy,
            last_trained=request.last_trained,
            conditioning_levels=request.conditioning_levels,
            flow_indices=flow_indices,
            last_conditioning_protocol=last_conditioning_protocol,
        )

        return GeneratedSessionResponse(**session_plan)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/sessions/start")
def start_session(request: StartSessionRequest) -> dict[str, Any]:
    """
    Creates a new session record. Evaluates readiness against the Brain
    to securely determine the session archetype.
    """
    try:
        # 1. Fetch the logic configs to determine the rules
        configs_response = (
            supabase.table("user_configs")
            .select("slug, data")
            .eq("user_id", DUMMY_USER_ID)
            .execute()
        )
        configs_data = cast(list[dict[str, Any]], configs_response.data)
        system_configs = {row["slug"]: row["data"] for row in configs_data}

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
            "status": "IN_PROGRESS",
        }

        # Cast payload to Any
        response = supabase.table("workout_sessions").upsert(cast(Any, session_data)).execute()

        if not response.data:
            raise Exception("Failed to start session.")

        res_data = cast(list[dict[str, Any]], response.data)
        return {
            "session_id": res_data[0]["id"],
            "derived_archetype": derived_archetype,
            "derived_state": state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/sessions/{session_id}/sets")
def log_atomic_set(session_id: str, request: LogSetRequest) -> dict[str, str]:
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
            "metadata": request.metadata,
        }

        # Cast payload to Any to bypass SDK JSON limitations
        supabase.table("workout_sets").upsert(
            cast(Any, set_data), on_conflict="session_id, exercise_name, set_index"
        ).execute()
        return {"status": "Set logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/sessions/{session_id}/complete")
def complete_session(session_id: str, request: CompleteSessionRequest) -> dict[str, str]:
    """
    Finalizes the session. Only updates progression state for exercises
    that were actually performed (have logged sets).
    """
    try:
        # 1. Update the Session Record with notes, timestamp, and anchor pattern
        update_data = {
            "status": "COMPLETED",
            "exercise_notes": request.exercise_notes,
            "summary_notes": request.summary_notes,
            "completed_at": datetime.now(UTC).isoformat(),
            "anchor_pattern": request.anchor_pattern,
        }
        supabase.table("workout_sessions").update(cast(Any, update_data)).eq(
            "id", session_id
        ).execute()

        # 2. Query what was actually logged in this session
        sets_response = (
            supabase.table("workout_sets")
            .select("exercise_name")
            .eq("session_id", session_id)
            .execute()
        )
        logged_exercises = {
            row["exercise_name"] for row in cast(list[dict[str, Any]], sets_response.data)
        }

        # 3. Fetch user configs (state + selections + conditioning)
        configs_response = (
            supabase.table("user_configs")
            .select("id, slug, data")
            .eq("user_id", DUMMY_USER_ID)
            .execute()
        )
        configs_data = cast(list[dict[str, Any]], configs_response.data)
        configs_by_slug = {row["slug"]: row for row in configs_data}

        state_row = configs_by_slug.get("state")
        if state_row:
            current_state = cast(dict[str, Any], state_row["data"])
            state_row_id = state_row["id"]
        else:
            current_state = {
                "last_trained": {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None},
                "conditioning_levels": {"HIIT": 1, "SIT": 1},
                "flow_indices": {"mobility": 0, "extensive_plyo": 0, "core_plane": 0},
            }
            state_row_id = None

        current_state.setdefault(
            "last_trained",
            {
                "SQUAT": None,
                "PUSH": None,
                "HINGE": None,
                "PULL": None,
            },
        )

        selections_config = configs_by_slug.get("selections", {}).get("data", {})
        conditioning_config = configs_by_slug.get("conditioning", {}).get("data", {})

        # 4. Conditionally update last_trained for anchor pattern
        if request.anchor_pattern and logged_exercises:
            anchor = request.anchor_pattern
            main_options = selections_config.get(anchor, {}).get("MAIN", {})
            # Collect all possible exercise names for this pattern across states
            main_exercises: set[str] = set()
            for exercises_list in main_options.values():
                if isinstance(exercises_list, list):
                    main_exercises.update(exercises_list)
            if main_exercises & logged_exercises:
                current_state["last_trained"][anchor] = datetime.now(UTC).isoformat()

        # 5. Conditionally advance conditioning
        if request.completed_conditioning_protocol and logged_exercises:
            protocol = request.completed_conditioning_protocol
            equipment = conditioning_config.get("equipment", "Rowing Machine")
            if equipment in logged_exercises:
                current_state.setdefault("conditioning_levels", {})
                current_level = current_state["conditioning_levels"].get(protocol, 1)
                current_state["conditioning_levels"][protocol] = current_level + 1
                current_state["last_conditioning_protocol"] = protocol

        # 6. Conditionally advance flow indices based on what was performed
        _default_flow_indices: dict[str, int] = {
            "mobility": 0,
            "extensive_plyo": 0,
            "core_plane": 0,
        }
        current_state.setdefault("flow_indices", dict(_default_flow_indices))
        for key, default in _default_flow_indices.items():
            current_state["flow_indices"].setdefault(key, default)

        # Build sets of exercise names per flow category for comparison
        flow_exercise_sets: dict[str, set[str]] = {}

        # Mobility exercises
        mobility_flows = selections_config.get("MOBILITY", {}).get("DYNAMIC", {}).get("flows", [])
        flow_exercise_sets["mobility"] = {name for flow in mobility_flows for name in flow}

        # Extensive plyo exercises
        ext_plyo_flows = selections_config.get("PLYO", {}).get("EXTENSIVE", {}).get("flows", [])
        flow_exercise_sets["extensive_plyo"] = {name for flow in ext_plyo_flows for name in flow}

        # Core exercises (all planes)
        core_config = selections_config.get("CORE", {})
        core_names: set[str] = set()
        for plane_data in core_config.values():
            if isinstance(plane_data, dict):
                for exercises_list in plane_data.values():
                    if isinstance(exercises_list, list):
                        core_names.update(exercises_list)
        flow_exercise_sets["core_plane"] = core_names

        for flow_key in _default_flow_indices:
            if flow_exercise_sets.get(flow_key, set()) & logged_exercises:
                current_state["flow_indices"][flow_key] += 1

        # 7. Save the new state to Supabase
        if state_row_id:
            supabase.table("user_configs").update(cast(Any, {"data": current_state})).eq(
                "id", state_row_id
            ).execute()
        else:
            supabase.table("user_configs").upsert(
                cast(Any, {"user_id": DUMMY_USER_ID, "slug": "state", "data": current_state})
            ).execute()

        return {"status": "Session completed and progression state updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- AI Coach Helpers ---


def _fetch_coach_context() -> dict[str, Any]:
    """
    Synchronous helper that gathers all training context for the AI coach prompt.
    Pre-computes derived values so the prompt builder can stay clean.
    """
    now = datetime.now(UTC)

    # 1. Fetch state document + logic config
    configs_response = (
        supabase.table("user_configs")
        .select("slug, data")
        .eq("user_id", DUMMY_USER_ID)
        .in_("slug", ["state", "logic"])
        .execute()
    )
    configs_by_slug = {
        row["slug"]: row["data"] for row in cast(list[dict[str, Any]], configs_response.data)
    }

    state_data = configs_by_slug.get("state", {})
    logic_config = configs_by_slug.get("logic", {})

    last_trained: dict[str, Any] = state_data.get("last_trained", {})
    conditioning_levels: dict[str, int] = state_data.get("conditioning_levels", {})
    last_conditioning_protocol: str | None = state_data.get("last_conditioning_protocol")

    # 2. Compute next pattern from rotation
    rotation: list[str] = logic_config.get("rotation_order", ["SQUAT", "PUSH", "HINGE", "PULL"])
    next_pattern = rotation[0]
    if last_trained and not all(v is None for v in last_trained.values()):
        most_recent_pattern = None
        most_recent_time: datetime | None = None
        for p in rotation:
            ts = last_trained.get(p)
            if ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if most_recent_time is None or dt > most_recent_time:
                    most_recent_time = dt
                    most_recent_pattern = p
        if most_recent_pattern:
            idx = rotation.index(most_recent_pattern)
            next_pattern = rotation[(idx + 1) % len(rotation)]

    # 3. Compute days since each pattern
    days_since: dict[str, int | None] = {}
    for pattern in rotation:
        ts = last_trained.get(pattern)
        if ts:
            last_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            days_since[pattern] = (now - last_dt).days
        else:
            days_since[pattern] = None

    # 4. Compute next conditioning protocol
    if last_conditioning_protocol == "HIIT":
        next_conditioning = "SIT"
    elif last_conditioning_protocol == "SIT":
        next_conditioning = "HIIT"
    else:
        next_conditioning = "HIIT"

    # 5. Derive last session info from state doc (reflects actual performance, not prescription)
    last_session_pattern: str | None = None
    days_since_last_session: int | None = None
    most_recent_time = None
    for pattern_name in rotation:
        ts = last_trained.get(pattern_name)
        if ts:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if most_recent_time is None or dt > most_recent_time:
                most_recent_time = dt
                last_session_pattern = pattern_name
    if most_recent_time:
        days_since_last_session = (now - most_recent_time).days

    # 6. Session frequency counts (these track completed sessions including empty ones,
    # which is fine for a rough consistency measure)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    sessions_7d_resp = (
        supabase.table("workout_sessions")
        .select("id")
        .eq("user_id", DUMMY_USER_ID)
        .eq("status", "COMPLETED")
        .gte("completed_at", seven_days_ago)
        .execute()
    )
    sessions_30d_resp = (
        supabase.table("workout_sessions")
        .select("id")
        .eq("user_id", DUMMY_USER_ID)
        .eq("status", "COMPLETED")
        .gte("completed_at", thirty_days_ago)
        .execute()
    )

    return {
        "next_pattern": next_pattern,
        "next_conditioning": next_conditioning,
        "days_since": days_since,
        "conditioning_levels": conditioning_levels,
        "count_7d": len(cast(list[dict[str, Any]], sessions_7d_resp.data)),
        "count_30d": len(cast(list[dict[str, Any]], sessions_30d_resp.data)),
        "last_session_pattern": last_session_pattern,
        "days_since_last_session": days_since_last_session,
    }


def _build_coach_prompt(ctx: dict[str, Any], local_hour: int, local_day: str) -> str:
    if local_hour < 12:
        time_of_day = "morning"
    elif local_hour < 18:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    # Format days-since into readable lines
    pattern_lines = []
    for pattern, days in ctx["days_since"].items():
        if days is None:
            pattern_lines.append(f"  {pattern}: never trained")
        elif days == 0:
            pattern_lines.append(f"  {pattern}: trained today")
        elif days == 1:
            pattern_lines.append(f"  {pattern}: 1 day ago")
        else:
            pattern_lines.append(f"  {pattern}: {days} days ago")

    cond = ctx["conditioning_levels"]
    cond_lines = [f"  {k}: Level {v}" for k, v in cond.items() if k != "SS"]

    dsl = ctx["days_since_last_session"]
    days_since_last = "never" if dsl is None else dsl

    return (
        "You are an experienced strength and conditioning coach. Your tone is calm, "
        "measured, and quietly confident — like an Irish coach who lets the work speak "
        "for itself. You're warm but not overly familiar. No forced enthusiasm, no "
        "bro energy, no clichés. Think of a coach who nods approvingly when the work "
        "is done and says something brief and genuine.\n\n"
        "Generate a JSON response with two fields:\n"
        '- "greeting": A brief, natural greeting (1-8 words). Use time of day or '
        "day of week naturally. Never say 'mate', 'bro', or 'buddy'.\n"
        '- "message": One calm, observational sentence (max 40 words)\n\n'
        "TRAINING CONTEXT:\n"
        f"- Time: {time_of_day}, {local_day}\n"
        f"- Sessions in last 7 days: {ctx['count_7d']}\n"
        f"- Sessions in last 30 days: {ctx['count_30d']}\n"
        f"- Days since last session: {days_since_last}\n"
        f"- Last session anchor pattern: {ctx['last_session_pattern'] or 'none yet'}\n"
        f"- Next anchor pattern: {ctx['next_pattern']}\n"
        f"- Next conditioning type: {ctx['next_conditioning']}\n"
        f"- Days since each pattern was anchored:\n" + "\n".join(pattern_lines) + "\n"
        "- Conditioning levels:\n" + "\n".join(cond_lines) + "\n\n"
        "CRITICAL RULES:\n"
        "1. Every session is FULL BODY. The anchor pattern (SQUAT, PUSH, HINGE, PULL) "
        "is just the primary lift — each session also includes accessories, plyos, core, "
        "and conditioning. NEVER describe a session as 'upper body', 'lower body', "
        "'leg day', 'pull day', etc. Just say 'session' or 'training'.\n"
        "2. NEVER assume WHEN the next session is. Don't say 'today', 'tomorrow', "
        "'this week', or 'big day ahead'. You don't know when they're training next.\n"
        "3. NEVER name specific exercises. The data only shows pattern categories.\n"
        "4. NEVER use pattern codes (PULL, PUSH, SQUAT, HINGE) in the message.\n"
        "5. Pick at most one data point that's genuinely notable — consistency streak, "
        "a long gap, conditioning progress. If nothing stands out, just offer an encouraging "
        "observation or leave it simple.\n"
        "6. No clichés: crush it, beast mode, let's go, get after it, let's get it, "
        "time to work, ready to roll. Avoid exclamation marks.\n"
        "7. If there's a gap in training, be matter-of-fact, not guilt-tripping or "
        "overly encouraging. A simple acknowledgement is fine.\n\n"
        'Respond ONLY with valid JSON: {"greeting": "...", "message": "..."}'
    )


async def _call_groq(prompt: str) -> AIResponse:
    resp = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=150,
    )
    content = resp.choices[0].message.content or ""
    data = json.loads(content)
    return AIResponse(**data)


@app.get("/user/coach-message")
async def get_coach_message(local_hour: int, local_day: str = "Today") -> AIResponse:
    """
    Fetches a dynamic AI-generated hype message based on the user's training context.
    Falls back gracefully on timeout or validation failure.
    """
    try:
        ctx = await asyncio.to_thread(_fetch_coach_context)
        prompt = _build_coach_prompt(ctx, local_hour, local_day)
        result = await asyncio.wait_for(_call_groq(prompt), timeout=2.0)
        return result
    except Exception as e:
        logger.error(f"AI Coach failed: {e}")
        return _COACH_FALLBACK
