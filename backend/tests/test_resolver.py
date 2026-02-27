import pytest
from datetime import datetime, timezone, timedelta
from core.resolver import WorkoutResolver

# 1. Create a "mock brain" fixture so we don't need the database
@pytest.fixture
def mock_brain():
    configs = {
        "logic": {
            "thresholds": {
                "knee_pain": {"lower": 3, "upper": 6},
                "energy": {"lower": 2, "upper": 5}
            },
            "pattern_priority": ["SQUAT", "PUSH", "HINGE", "PULL"]
        },
        "sessions": {},
        "selections": {},
        "conditioning": {}
    }
    exercises = []
    return configs, exercises

# 2. Test the triage engine
def test_evaluate_state_red_pain(mock_brain):
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)
    
    # High pain (8), Good energy (8) -> Should force RED / RECOVERY
    state, archetype = resolver._evaluate_state(knee_pain=8, energy=8)
    
    assert state == "RED"
    assert archetype == "RECOVERY"

def test_evaluate_state_low_energy(mock_brain):
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)
    
    # Low pain (1), Terrible energy (2) -> Should force RED / RECOVERY
    state, archetype = resolver._evaluate_state(knee_pain=1, energy=2)
    
    assert state == "RED"
    assert archetype == "RECOVERY"

# 3. Test the UTC timestamp progression engine
def test_resolve_main_pattern_tie_breaker(mock_brain):
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)
    
    # We use timedelta to dynamically generate deterministic timestamps
    now = datetime.now(timezone.utc)
    five_days_ago = (now - timedelta(days=5)).isoformat()
    two_days_ago = (now - timedelta(days=2)).isoformat()
    one_day_ago = (now - timedelta(days=1)).isoformat()
    
    # SQUAT and PUSH are tied at exactly 5 days elapsed
    # According to our logic.pattern_priority, SQUAT should win.
    last_trained = {
        "SQUAT": five_days_ago,
        "PUSH": five_days_ago,
        "HINGE": two_days_ago,
        "PULL": one_day_ago
    }
    
    main_pattern = resolver._resolve_main_pattern(last_trained)
    
    assert main_pattern == "SQUAT"

def test_resolve_main_pattern_null_is_highest_priority(mock_brain):
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)
    
    now = datetime.now(timezone.utc)
    ten_days_ago = (now - timedelta(days=10)).isoformat()
    
    # Even though SQUAT hasn't been trained in 10 days, PULL has NEVER been trained (None)
    # None evaluates to infinite debt and should win
    last_trained = {
        "SQUAT": ten_days_ago,
        "PUSH": ten_days_ago,
        "HINGE": ten_days_ago,
        "PULL": None 
    }
    
    main_pattern = resolver._resolve_main_pattern(last_trained)
    
    assert main_pattern == "PULL"
