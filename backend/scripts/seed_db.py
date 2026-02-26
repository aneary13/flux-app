import os
import yaml
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import ValidationError
import sys

# Ensure Python can find the core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.models import LibraryConfig

load_dotenv()

# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# We use a dummy UUID for the system defaults
DUMMY_USER_ID = "00000000-0000-0000-0000-000000000000"
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")

def load_yaml(filename: str) -> dict:
    filepath = os.path.join(CONFIG_DIR, filename)
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

def seed_exercises():
    print("Seeding Exercises...")
    raw_data = load_yaml("library.yaml")
    
    try:
        # Validate through Pydantic
        library = LibraryConfig(**raw_data)
        
        for item in library.catalog:
            data = {
                "name": item.name,
                "is_unilateral": item.settings.unilateral,
                "load_type": item.settings.load,
                "tracking_unit": item.settings.unit
            }
            # Upsert ensures we don't duplicate if we run this twice
            supabase.table("exercises").upsert(data, on_conflict="name").execute()
            print(f"  ✓ Inserted: {item.name}")
            
    except ValidationError as e:
        print(f"Validation Error in library.yaml: {e}")

def seed_user_configs():
    print("\nSeeding User Configs (The Brain)...")
    config_files = ["logic.yaml", "selections.yaml", "sessions.yaml", "conditioning.yaml"]
    
    for file in config_files:
        slug = file.replace(".yaml", "")
        data = load_yaml(file)
        
        payload = {
            "user_id": DUMMY_USER_ID,
            "slug": slug,
            "data": data
        }
        
        # Upsert into user_configs
        supabase.table("user_configs").upsert(
            payload, 
            on_conflict="user_id, slug"
        ).execute()
        print(f"  ✓ Upserted config: {slug}")

if __name__ == "__main__":
    print("Initializing FLUX Database Seed...\n")
    seed_exercises()
    seed_user_configs()
    print("\n✅ Seeding Complete! The Brain is online.")
