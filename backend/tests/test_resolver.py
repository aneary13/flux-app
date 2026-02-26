import pytest
from core.resolver import WorkoutResolver

# 1. Create a "Mock Brain" fixture so we don't need the database
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

# 2. Test the Triage Engine
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

# 3. Test the Debt Tie-Breaker
def test_resolve_main_pattern_tie_breaker(mock_brain):
    configs, exercises = mock_brain
    resolver = WorkoutResolver(configs, exercises)
    
    # SQUAT and PUSH are tied at 5 days of debt. 
    # According to our logic.pattern_priority, SQUAT should win.
    pattern_debts = {
        "SQUAT": 5,
        "PUSH": 5,
        "HINGE": 2,
        "PULL": 1
    }
    
    main_pattern = resolver._resolve_main_pattern(pattern_debts)
    
    assert main_pattern == "SQUAT"
