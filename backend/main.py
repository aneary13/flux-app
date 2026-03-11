import asyncio
import json
import logging
import os
import secrets
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
        response = (
            supabase.table("user_configs")
            .select("data")
            .eq("user_id", DUMMY_USER_ID)
            .eq("slug", "state")
            .execute()
        )

        # Fallback State
        raw_state = {
            "last_trained": {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None},
            "conditioning_levels": {"HIIT": 1, "SIT": 1},
        }

        data_list = cast(list[dict[str, Any]], response.data)
        if data_list and data_list[0].get("data"):
            raw_state = cast(dict[str, Any], data_list[0]["data"])

        # Explicitly type the dictionaries so Mypy knows they aren't generic objects
        # Force Mypy to trust the JSON schema we expect
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

        return UserStateResponse(
            patterns=patterns_view,
            conditioning_levels=cond_levels,
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

        exercises_response = supabase.table("exercises").select("*").execute()
        exercises_catalog = cast(list[dict[str, Any]], exercises_response.data)

        resolver = WorkoutResolver(configs=system_configs, exercises=exercises_catalog)

        session_plan = resolver.generate_session(
            knee_pain=request.knee_pain,
            energy=request.energy,
            last_trained=request.last_trained,
            conditioning_levels=request.conditioning_levels,
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
    Finalizes the session and securely updates the UTC timestamp for the anchor pattern.
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

        # 2. Fetch the user's current state
        state_response = (
            supabase.table("user_configs")
            .select("id, data")
            .eq("user_id", DUMMY_USER_ID)
            .eq("slug", "state")
            .execute()
        )

        state_data = cast(list[dict[str, Any]], state_response.data)
        if state_data:
            current_state = cast(dict[str, Any], state_data[0]["data"])
            state_row_id = state_data[0]["id"]
        else:
            current_state = {
                "last_trained": {"SQUAT": None, "PUSH": None, "HINGE": None, "PULL": None},
                "conditioning_levels": {"HIIT": 1, "SIT": 1},
            }
            state_row_id = None

        # Ensure schema structure exists
        if "last_trained" not in current_state:
            current_state["last_trained"] = {
                "SQUAT": None,
                "PUSH": None,
                "HINGE": None,
                "PULL": None,
            }

        # 3. Update specific anchor pattern with UTC Now
        if request.anchor_pattern:
            current_state["last_trained"][request.anchor_pattern] = datetime.now(UTC).isoformat()

        # 4. Recalculate conditioning (fully automatic linear progression)
        if request.completed_conditioning_protocol:
            protocol = request.completed_conditioning_protocol
            if "conditioning_levels" not in current_state:
                current_state["conditioning_levels"] = {}
            current_level = current_state["conditioning_levels"].get(protocol, 1)
            current_state["conditioning_levels"][protocol] = current_level + 1

        # 5. Save the new state to Supabase
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


def _fetch_coach_context() -> tuple[
    dict[str, Any], int, int, dict[str, int], dict[str, Any] | None
]:
    """
    Synchronous helper to fetch context for the AI coach prompt.
    Returns: (last_trained, count_7d, count_30d, conditioning_levels, last_session_dict)
    """
    # 1. Fetch State Document (Contains Pattern Debts & Conditioning Levels)
    state_response = (
        supabase.table("user_configs")
        .select("data")
        .eq("user_id", DUMMY_USER_ID)
        .eq("slug", "state")
        .execute()
    )
    state_list = cast(list[dict[str, Any]], state_response.data)

    last_trained: dict[str, Any] = {}
    conditioning_levels: dict[str, int] = {}

    if state_list and state_list[0].get("data"):
        state_data = cast(dict[str, Any], state_list[0]["data"])
        last_trained = state_data.get("last_trained", {})
        conditioning_levels = state_data.get("conditioning_levels", {})

    now = datetime.now(UTC)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # 2. Fetch last 7 days of sessions (Order by newest first to grab the last session)
    sessions_7d_resp = (
        supabase.table("workout_sessions")
        .select("id, archetype, anchor_pattern")
        .eq("user_id", DUMMY_USER_ID)
        .eq("status", "COMPLETED")
        .gte("completed_at", seven_days_ago)
        .order("completed_at", desc=True)
        .execute()
    )

    # 3. Fetch 30 day count
    sessions_30d_resp = (
        supabase.table("workout_sessions")
        .select("id")
        .eq("user_id", DUMMY_USER_ID)
        .eq("status", "COMPLETED")
        .gte("completed_at", thirty_days_ago)
        .execute()
    )

    sessions_7d = cast(list[dict[str, Any]], sessions_7d_resp.data)
    count_7d = len(sessions_7d)
    count_30d = len(cast(list[dict[str, Any]], sessions_30d_resp.data))

    # Grab the single most recent session for extra context
    last_session = sessions_7d[0] if sessions_7d else None

    return last_trained, count_7d, count_30d, conditioning_levels, last_session


def _build_coach_prompt(
    last_trained: dict[str, Any],
    count_7d: int,
    count_30d: int,
    cond_levels: dict[str, int],
    last_session: dict[str, Any] | None,
    local_hour: int,
    local_day: str,
) -> str:

    now = datetime.now(UTC)

    # --- PYTHON PRE-COMPUTATION ---
    longest_overdue_pattern = "Any"
    max_days = -1

    for pattern in ["SQUAT", "HINGE", "PUSH", "PULL"]:
        ts = last_trained.get(pattern)
        if not ts:
            max_days = 999
            longest_overdue_pattern = pattern
            break
        else:
            last_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            days = (now - last_dt).days
            if days > max_days:
                max_days = days
                longest_overdue_pattern = pattern

    days_str = f"{max_days} days" if max_days != 999 else "a while"

    if local_hour < 12:
        time_of_day = "Morning"
    elif local_hour < 18:
        time_of_day = "Afternoon"
    else:
        time_of_day = "Evening"

    # --- OPTIONAL CONTEXT FORMATTING ---
    last_session_context = ""
    if last_session:
        anchor = last_session.get("anchor_pattern") or last_session.get("archetype", "")
        if anchor:
            last_session_context = f"- Last workout focused on: {anchor}\n"

    cond_context = ""
    if cond_levels:
        cond_str = ", ".join([f"{k} Level {v}" for k, v in cond_levels.items()])
        cond_context = f"- Conditioning progress: {cond_str}\n"

    # --- RANDOMIZED INSTRUCTION VECTOR ---
    last_focus = (last_session or {}).get("anchor_pattern") or (last_session or {}).get(
        "archetype", "recent"
    )
    instruction_angles = [
        (
            f"Focus heavily on the fact that today is {local_day}. "
            f"Make it feel like a fresh opportunity."
        ),
        (
            f"Acknowledge their rolling 30-day consistency ({count_30d} sessions), "
            f"then pivot to today's {longest_overdue_pattern} focus."
        ),
        (
            f"Keep it very brief and philosophical about showing up, "
            f"then mention the {longest_overdue_pattern}."
        ),
        (
            f"If they had a recent session, reference how that {last_focus} session "
            f"sets them up perfectly for today's {longest_overdue_pattern}."
        ),
    ]
    chosen_angle = secrets.choice(instruction_angles)

    # --- THE PROMPT ---
    tone_rule_3 = (
        "3. CRITICAL: NEVER use the phrase 'this week' or 'this month' when referring "
        "to the last 7 days or the last 30 days, respectively. Always refer to "
        "'the last few days' or 'recent momentum' to avoid calendar confusion. "
        "You can use the phrases 'this week' and 'this month' in reference to "
        "the calendar periods."
    )

    return (
        f"You are a grounded, attentive, and supportive human fitness coach for the FLUX app. "
        f"Generate a two-part response: a short, punchy greeting, "
        f"and a 1-to-2 sentence message (max 30 words). "
        f"Use a mix of the following user data to personalize the message naturally:\n"
        f"- Time: {time_of_day} on a {local_day}\n"
        f"- Short-term consistency: {count_7d} sessions in the last 7 days\n"
        f"- Long-term consistency: {count_30d} sessions in the last 30 days\n"
        f"- Focus for today: {longest_overdue_pattern} ({days_str} since last trained)\n"
        f"{last_session_context}"
        f"{cond_context}"
        f"TONE RULES:\n"
        f"1. Conversational, warm, and encouraging.\n"
        f"2. Absolutely NO cliches ('crush it', 'legend', 'beast mode').\n"
        f"{tone_rule_3}\n"
        f"YOUR SPECIFIC DIRECTIVE FOR THIS MESSAGE: {chosen_angle}\n"
        f"EXAMPLES OF EXACT JSON FORMAT WE WANT:\n"
        f'{{"greeting": "Happy {local_day}!", '
        f'"message": "Your consistency over the last month is really showing. '
        f"Let's channel that into your {longest_overdue_pattern} mechanics today.\"}}\n"
        f'{{"greeting": "Good {time_of_day.lower()}.", '
        f'"message": "Showing up is the hardest part, and you\'re here. '
        f"Let's get the body moving and focus on the {longest_overdue_pattern}.\"}}\n"
        f"Respond ONLY with valid JSON matching the exact schema: "
        f'{{"greeting": "...", "message": "..."}}'
    )


async def _call_groq(prompt: str) -> AIResponse:
    resp = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=60,
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
        # Unpack the newly expanded context
        last_trained, count_7d, count_30d, cond_levels, last_session = await asyncio.to_thread(
            _fetch_coach_context
        )

        prompt = _build_coach_prompt(
            last_trained, count_7d, count_30d, cond_levels, last_session, local_hour, local_day
        )

        result = await asyncio.wait_for(_call_groq(prompt), timeout=2.0)

        # Validate length (give a little buffer for 2 sentences, ~30 words max)
        if len(result.message.split()) > 30:
            return _COACH_FALLBACK

        return result
    except Exception as e:
        logger.error(f"Coach LLM failed: {e}")
        return _COACH_FALLBACK
