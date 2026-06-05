import logging
import os
from typing import Any, cast

import yaml
from supabase import Client

# Configure standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants mapping to your expected YAML structure
CONFIG_SLUGS = ["logic", "sessions", "selections", "conditioning"]
CONFIG_DIR = "config"  # Assuming YAMLs live here


def load_yaml(filename: str) -> dict[str, Any]:
    """Helper to safely load a YAML file."""
    filepath = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing required config file: {filepath}")

    with open(filepath) as f:
        # Enforce the boundary: Cast the untyped YAML output to our internal type
        return cast(dict[str, Any], yaml.safe_load(f))


def auto_seed_database(supabase: Client, dummy_user_id: str) -> None:
    """
    Checks if the database is empty and auto-seeds core logic and exercises.
    Designed to be idempotent for multi-worker startup environments.
    """
    try:
        logger.info("FLUX Engine: Running database state check...")

        # -----------------------------------------
        # Sync Exercises (always upsert from YAML)
        # Uses UNIQUE(name) constraint — updates metadata for existing exercises,
        # inserts new ones. Historical workout_sets referencing removed exercises
        # are unaffected (exercise_name is a text field).
        # -----------------------------------------
        exercises_data = load_yaml("library.yaml")

        exercise_payload = []
        for ex in exercises_data.get("catalog", []):
            exercise_payload.append(
                {
                    "name": ex["name"],
                    "is_unilateral": ex["settings"].get("unilateral", False),
                    "load_type": ex["settings"].get("load", "WEIGHTED"),
                    "tracking_unit": ex["settings"].get("unit", "REPS"),
                }
            )

        supabase.table("exercises").upsert(
            cast(Any, exercise_payload), on_conflict="name"
        ).execute()
        logger.info(f"FLUX Engine: Synced {len(exercise_payload)} exercises.")

        # -----------------------------------------
        # Sync System Configs (always upsert from YAML)
        # These are system-level definitions, not user data.
        # User state (slug="state") is not in CONFIG_SLUGS and is never touched.
        # -----------------------------------------
        config_payloads = []
        for slug in CONFIG_SLUGS:
            yaml_data = load_yaml(f"{slug}.yaml")
            config_payloads.append({"user_id": dummy_user_id, "slug": slug, "data": yaml_data})

        supabase.table("user_configs").upsert(
            cast(Any, config_payloads), on_conflict="user_id, slug"
        ).execute()
        logger.info("FLUX Engine: Synced system configs from YAML.")

        logger.info("FLUX Engine: Startup sync completed successfully.")

    except FileNotFoundError as fnf:
        logger.critical(f"FLUX Engine: Initialization aborted. {str(fnf)}")
    except Exception as e:
        logger.error(f"FLUX Engine: Critical failure during auto-seed: {str(e)}")
