import os
import logging
import yaml
from supabase import Client

# Configure standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants mapping to your expected YAML structure
CONFIG_SLUGS = ["logic", "sessions", "selections", "conditioning"]
CONFIG_DIR = "config" # Assuming YAMLs live here

def load_yaml(filename: str) -> dict:
    """Helper to safely load a YAML file."""
    filepath = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing required config file: {filepath}")
    
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def auto_seed_database(supabase: Client, dummy_user_id: str):
    """
    Checks if the database is empty and auto-seeds core logic and exercises.
    Designed to be idempotent for multi-worker startup environments.
    """
    try:
        logger.info("FLUX Engine: Running database state check...")

        # 1. Lightweight check: Do we have any exercises?
        ex_check = supabase.table("exercises").select("id").limit(1).execute()
        
        # 2. Lightweight check: Do we have the core user_configs?
        cfg_check = supabase.table("user_configs").select("id").eq("user_id", dummy_user_id).limit(1).execute()

        if ex_check.data and cfg_check.data:
            logger.info("FLUX Engine: DB populated. Skipping auto-seed.")
            return

        logger.info("FLUX Engine: Empty DB detected. Auto-seeding YAML logic...")

        # -----------------------------------------
        # Seed Exercises
        # -----------------------------------------
        if not ex_check.data:
            exercises_data = load_yaml("library.yaml")
            
            # Format according to your relational schema requirements
            exercise_payload = []
            for ex in exercises_data.get("catalog", []):
                exercise_payload.append({
                    "name": ex["name"],
                    "is_unilateral": ex["settings"].get("unilateral", False),
                    "load_type": ex["settings"].get("load", "WEIGHTED"),
                    "tracking_unit": ex["settings"].get("unit", "REPS")
                })
            
            # Upsert relying on the UNIQUE(name) constraint
            supabase.table("exercises").upsert(
                exercise_payload, 
                on_conflict="name"
            ).execute()
            logger.info(f"FLUX Engine: Seeded {len(exercise_payload)} exercises.")

        # -----------------------------------------
        # Seed User Configs (The Brain)
        # -----------------------------------------
        if not cfg_check.data:
            config_payloads = []
            for slug in CONFIG_SLUGS:
                yaml_data = load_yaml(f"{slug}.yaml")
                config_payloads.append({
                    "user_id": dummy_user_id,
                    "slug": slug,
                    "data": yaml_data
                })
            
            # Upsert relying on the UNIQUE(user_id, slug) constraint
            supabase.table("user_configs").upsert(
                config_payloads, 
                on_conflict="user_id, slug"
            ).execute()
            logger.info("FLUX Engine: Seeded core user_configs.")

        logger.info("FLUX Engine: Auto-seed completed successfully.")

    except FileNotFoundError as fnf:
        logger.critical(f"FLUX Engine: Initialization aborted. {str(fnf)}")
    except Exception as e:
        logger.error(f"FLUX Engine: Critical failure during auto-seed: {str(e)}")
