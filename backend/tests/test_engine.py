"""Tests for WorkoutEngine logic."""

from datetime import date, timedelta

import pytest

from src.engine import WorkoutEngine
from src.models import HistoryEntry, Readiness, TrainingHistory


@pytest.fixture
def config_path(tmp_path):
    """Create a temporary config file for testing v2.0 structure."""
    config_file = tmp_path / "program_config.yaml"
    config_file.write_text(
        """
patterns:
  main:
    - SQUAT
    - HINGE
    - PUSH
    - PULL
  accessory:
    - LUNGE
  core:
    - CORE

relationships:
  SQUAT:
    - PULL:ACCESSORY_HORIZONTAL
    - HINGE:ACCESSORY_HIP
  PUSH:
    - SQUAT:ACCESSORY
    - PULL:ACCESSORY_VERTICAL
  HINGE:
    - PUSH:ACCESSORY_HORIZONTAL
    - LUNGE:ACCESSORY
  PULL:
    - HINGE:ACCESSORY_KNEE
    - PUSH:ACCESSORY_VERTICAL

library:
  SQUAT:
    MAIN:
      GREEN: "Back Squat"
      ORANGE: "Tempo Goblet Squat"
      RED: "SKIP"
    ACCESSORY:
      GREEN: "Goblet Squat"
      ORANGE: "Bodyweight Squat"
      RED: "Wall Sit"
  HINGE:
    MAIN:
      GREEN: "Romanian Deadlift"
      ORANGE: "Tempo Romanian Deadlift"
      RED: "SKIP"
    ACCESSORY_HIP:
      GREEN: "Romanian Deadlift"
      ORANGE: "Good Morning"
      RED: "Glute Bridge"
    ACCESSORY_KNEE:
      GREEN: "Leg Curl"
      ORANGE: "Nordic Curl"
      RED: "Glute Bridge"
  PUSH:
    MAIN:
      GREEN: "Bench Press"
      ORANGE: "Dumbbell Press"
      RED: "Push-ups"
    ACCESSORY_VERTICAL:
      GREEN: "Overhead Press"
      ORANGE: "Dumbbell Press"
      RED: "Wall Slides"
    ACCESSORY_HORIZONTAL:
      GREEN: "Dumbbell Fly"
      ORANGE: "Push-ups"
      RED: "Wall Slides"
  PULL:
    MAIN:
      GREEN: "Barbell Row"
      ORANGE: "Cable Row"
      RED: "Band Row"
    ACCESSORY_VERTICAL:
      GREEN: "Pull-ups"
      ORANGE: "Lat Pulldown"
      RED: "Band Row"
    ACCESSORY_HORIZONTAL:
      GREEN: "Cable Row"
      ORANGE: "Dumbbell Row"
      RED: "Band Row"
  LUNGE:
    ACCESSORY:
      GREEN: "Walking Lunge"
      ORANGE: "Reverse Lunge"
      RED: "SKIP"
  CORE:
    TRANSVERSE:
      GREEN: "Pallof Press"
      ORANGE: "Band Anti-Rotation"
      RED: "Dead Bug"
    SAGITTAL:
      GREEN: "Dead Bug"
      ORANGE: "Bird Dog"
      RED: "Cat-Cow"
    FRONTAL:
      GREEN: "Side Plank"
      ORANGE: "Band Anti-Lateral"
      RED: "Dead Bug"
  RFD:
    HIGH:
      - "Depth Jumps"
      - "Sprints"
      - "Box Jumps"
    LOW:
      - "Broad Jumps"
      - "Medicine Ball Throws"
      - "Kettlebell Swings"
    UPPER:
      - "Medicine Ball Slams"
      - "Band Pull-apart"
      - "Shoulder Circles"

power_selection:
  GREEN: "HIGH"
  ORANGE: "LOW"
  RED: "UPPER"

session_structure:
  PREP:
    - WARM_UP
    - PATELLAR_ISO
    - CORE
  POWER:
    - RFD
  STRENGTH:
    - MAIN_PATTERN
  ACCESSORIES:
    - RELATED_ACCESSORIES

states:
  - name: "RED"
    condition: "knee_pain >= 6"
  - name: "ORANGE"
    condition: "(knee_pain >= 3) OR (energy <= 3)"
  - name: "GREEN"
    condition: "default"
"""
    )
    return str(config_file)


@pytest.fixture
def engine(config_path):
    """Create a WorkoutEngine instance for testing."""
    return WorkoutEngine(config_path)


class TestStateDetermination:
    """Tests for determine_state method."""

    def test_red_state(self, engine: WorkoutEngine) -> None:
        """Test RED state determination (knee_pain >= 6)."""
        readiness = Readiness(knee_pain=6, energy=5)
        assert engine.determine_state(readiness) == "RED"

        readiness = Readiness(knee_pain=10, energy=10)
        assert engine.determine_state(readiness) == "RED"

    def test_orange_state_pain(self, engine: WorkoutEngine) -> None:
        """Test ORANGE state from pain condition (knee_pain >= 3)."""
        readiness = Readiness(knee_pain=3, energy=5)
        assert engine.determine_state(readiness) == "ORANGE"

        readiness = Readiness(knee_pain=5, energy=7)
        assert engine.determine_state(readiness) == "ORANGE"

    def test_orange_state_energy(self, engine: WorkoutEngine) -> None:
        """Test ORANGE state from energy condition (energy <= 3)."""
        readiness = Readiness(knee_pain=2, energy=3)
        assert engine.determine_state(readiness) == "ORANGE"

        readiness = Readiness(knee_pain=1, energy=0)
        assert engine.determine_state(readiness) == "ORANGE"

    def test_orange_state_both_conditions(self, engine: WorkoutEngine) -> None:
        """Test ORANGE state when both conditions are true."""
        readiness = Readiness(knee_pain=4, energy=2)
        assert engine.determine_state(readiness) == "ORANGE"

    def test_green_state(self, engine: WorkoutEngine) -> None:
        """Test GREEN state (default, low pain and decent energy)."""
        readiness = Readiness(knee_pain=2, energy=5)
        assert engine.determine_state(readiness) == "GREEN"

        readiness = Readiness(knee_pain=0, energy=10)
        assert engine.determine_state(readiness) == "GREEN"


class TestPatternDebtCalculation:
    """Tests for calculate_pattern_debts method (replaces old priority calculation)."""

    def test_pattern_debts_with_history(self, engine: WorkoutEngine) -> None:
        """Test pattern debt calculation with training history."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT", "PULL_HORIZ"],
                    date=today - timedelta(days=5),
                ),
                HistoryEntry(
                    impacted_patterns=["HINGE"],
                    date=today - timedelta(days=2),
                ),
            ]
        )

        debts = engine.calculate_pattern_debts(history)

        assert debts["SQUAT"] == 5
        assert debts["HINGE"] == 2
        # Patterns not in history should have default debt of 100
        assert debts["PUSH"] == 100
        assert debts["PULL"] == 100

    def test_pattern_debts_no_history(self, engine: WorkoutEngine) -> None:
        """Test pattern debt calculation with no history."""
        history = TrainingHistory()

        debts = engine.calculate_pattern_debts(history)

        # All patterns should have default debt of 100
        assert debts["SQUAT"] == 100
        assert debts["HINGE"] == 100
        assert debts["PUSH"] == 100
        assert debts["PULL"] == 100

    def test_pattern_debts_most_recent_date(self, engine: WorkoutEngine) -> None:
        """Test that most recent date is used when pattern appears multiple times."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=10),
                ),
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=2),  # More recent
                ),
            ]
        )

        debts = engine.calculate_pattern_debts(history)

        # Should use most recent date (2 days ago)
        assert debts["SQUAT"] == 2


class TestSessionGeneration:
    """Tests for generate_session method with v2.0 architecture."""

    def test_generate_session_gym_session(self, engine: WorkoutEngine) -> None:
        """Test that GYM session is generated with proper blocks."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=5),
                ),
            ]
        )
        readiness = Readiness(knee_pain=2, energy=7)  # GREEN state

        plan = engine.generate_session(readiness, history)

        assert plan.session_type == "GYM"
        assert plan.archetype == "GYM"  # Computed field
        assert len(plan.blocks) > 0
        # Should have PREP, POWER, MAIN, and ACCESSORY blocks
        block_types = [b.block_type for b in plan.blocks]
        assert "MAIN" in block_types
        assert "PREP" in block_types

    def test_generate_session_rest_on_low_energy(self, engine: WorkoutEngine) -> None:
        """Test that REST session is returned when energy is low."""
        history = TrainingHistory()
        readiness = Readiness(knee_pain=2, energy=3)  # Low energy, ORANGE state

        plan = engine.generate_session(readiness, history)

        assert plan.session_type == "REST"
        assert len(plan.blocks) == 0

    def test_generate_session_red_state_skips_patterns(self, engine: WorkoutEngine) -> None:
        """Test that RED state skips patterns that are marked SKIP."""
        today = date.today()
        # SQUAT has highest debt but SKIPs in RED
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=10),
                ),
                HistoryEntry(
                    impacted_patterns=["PUSH"],
                    date=today - timedelta(days=5),
                ),
            ]
        )
        readiness = Readiness(knee_pain=7, energy=6)  # RED state

        plan = engine.generate_session(readiness, history)

        assert plan.session_type == "GYM"
        # Should select PUSH (not SQUAT which is SKIP in RED)
        main_blocks = [b for b in plan.blocks if b.block_type == "MAIN"]
        assert len(main_blocks) == 1
        assert main_blocks[0].pattern != "SQUAT"  # SQUAT should be skipped
        assert main_blocks[0].pattern in ["PUSH", "PULL", "HINGE"]  # Valid patterns

    def test_generate_session_with_no_history(self, engine: WorkoutEngine) -> None:
        """Test session generation with no history (all patterns have default debt)."""
        history = TrainingHistory()
        readiness = Readiness(knee_pain=2, energy=7)  # GREEN state

        plan = engine.generate_session(readiness, history)

        assert plan.session_type == "GYM"
        assert len(plan.blocks) > 0
        # Should still generate a valid session
        main_blocks = [b for b in plan.blocks if b.block_type == "MAIN"]
        assert len(main_blocks) == 1


@pytest.fixture
def new_config_path(tmp_path):
    """Create a temporary config file for testing new v2.0 structure."""
    config_file = tmp_path / "program_config_v2.yaml"
    config_file.write_text(
        """
patterns:
  main:
    - SQUAT
    - HINGE
    - PUSH
    - PULL
  accessory:
    - LUNGE
  core:
    - CORE

relationships:
  SQUAT:
    - PULL:ACCESSORY_HORIZONTAL
    - HINGE:ACCESSORY_HIP
  PUSH:
    - SQUAT:ACCESSORY
    - PULL:ACCESSORY_VERTICAL
  HINGE:
    - PUSH:ACCESSORY_HORIZONTAL
    - LUNGE:ACCESSORY
  PULL:
    - HINGE:ACCESSORY_KNEE
    - PUSH:ACCESSORY_VERTICAL

library:
  SQUAT:
    MAIN:
      GREEN: "Back Squat"
      ORANGE: "Tempo Goblet Squat"
      RED: "SKIP"
    ACCESSORY:
      GREEN: "Goblet Squat"
      ORANGE: "Bodyweight Squat"
      RED: "Wall Sit"
  HINGE:
    MAIN:
      GREEN: "Romanian Deadlift"
      ORANGE: "Tempo Romanian Deadlift"
      RED: "SKIP"
    ACCESSORY_HIP:
      GREEN: "Romanian Deadlift"
      ORANGE: "Good Morning"
      RED: "Glute Bridge"
    ACCESSORY_KNEE:
      GREEN: "Leg Curl"
      ORANGE: "Nordic Curl"
      RED: "Glute Bridge"
  PUSH:
    MAIN:
      GREEN: "Bench Press"
      ORANGE: "Dumbbell Press"
      RED: "Push-ups"
    ACCESSORY_VERTICAL:
      GREEN: "Overhead Press"
      ORANGE: "Dumbbell Press"
      RED: "Wall Slides"
    ACCESSORY_HORIZONTAL:
      GREEN: "Dumbbell Fly"
      ORANGE: "Push-ups"
      RED: "Wall Slides"
  PULL:
    MAIN:
      GREEN: "Barbell Row"
      ORANGE: "Cable Row"
      RED: "Band Row"
    ACCESSORY_VERTICAL:
      GREEN: "Pull-ups"
      ORANGE: "Lat Pulldown"
      RED: "Band Row"
    ACCESSORY_HORIZONTAL:
      GREEN: "Cable Row"
      ORANGE: "Dumbbell Row"
      RED: "Band Row"
  LUNGE:
    ACCESSORY:
      GREEN: "Walking Lunge"
      ORANGE: "Reverse Lunge"
      RED: "SKIP"
  CORE:
    TRANSVERSE:
      GREEN: "Pallof Press"
      ORANGE: "Band Anti-Rotation"
      RED: "Dead Bug"
    SAGITTAL:
      GREEN: "Dead Bug"
      ORANGE: "Bird Dog"
      RED: "Cat-Cow"
    FRONTAL:
      GREEN: "Side Plank"
      ORANGE: "Band Anti-Lateral"
      RED: "Dead Bug"
  RFD:
    HIGH:
      - "Depth Jumps"
      - "Sprints"
      - "Box Jumps"
    LOW:
      - "Broad Jumps"
      - "Medicine Ball Throws"
      - "Kettlebell Swings"
    UPPER:
      - "Medicine Ball Slams"
      - "Band Pull-apart"
      - "Shoulder Circles"

power_selection:
  GREEN: "HIGH"
  ORANGE: "LOW"
  RED: "UPPER"

session_structure:
  PREP:
    - WARM_UP
    - PATELLAR_ISO
    - CORE
  POWER:
    - RFD
  STRENGTH:
    - MAIN_PATTERN
  ACCESSORIES:
    - RELATED_ACCESSORIES

states:
  - name: "RED"
    condition: "knee_pain >= 6"
  - name: "ORANGE"
    condition: "(knee_pain >= 3) OR (energy <= 3)"
  - name: "GREEN"
    condition: "default"
"""
    )
    return str(config_file)


@pytest.fixture
def new_engine(new_config_path):
    """Create a WorkoutEngine instance with new v2.0 config for testing."""
    return WorkoutEngine(new_config_path)


class TestPatternDebtCalculation:
    """Tests for calculate_pattern_debts method."""

    def test_pattern_debts_with_history(self, new_engine: WorkoutEngine) -> None:
        """Test pattern debt calculation with valid history."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT", "PULL_HORIZ"],
                    date=today - timedelta(days=5),
                ),
                HistoryEntry(
                    impacted_patterns=["HINGE"],
                    date=today - timedelta(days=2),
                ),
            ]
        )

        debts = new_engine.calculate_pattern_debts(history)

        assert debts["SQUAT"] == 5
        assert debts["HINGE"] == 2
        # Patterns not in history should have default debt of 100
        assert debts["PUSH"] == 100
        assert debts["PULL"] == 100

    def test_pattern_debts_none_handling(self, new_engine: WorkoutEngine) -> None:
        """Test that empty impacted_patterns (from None in DB) are handled gracefully.
        
        Note: Pydantic model requires List[str], so None from DB is converted to []
        at the API boundary. This test verifies the same code path handles empty lists.
        """
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=3),
                ),
                HistoryEntry(
                    impacted_patterns=[],  # Empty list (represents None from DB)
                    date=today - timedelta(days=1),
                ),
            ]
        )

        debts = new_engine.calculate_pattern_debts(history)

        # Should only track SQUAT, not crash on empty list
        assert debts["SQUAT"] == 3
        assert debts["HINGE"] == 100  # Default for untracked patterns

    def test_pattern_debts_empty_list_handling(
        self, new_engine: WorkoutEngine
    ) -> None:
        """Test that empty list impacted_patterns are handled gracefully."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["PUSH"],
                    date=today - timedelta(days=4),
                ),
                HistoryEntry(
                    impacted_patterns=[],
                    date=today - timedelta(days=1),
                ),
            ]
        )

        debts = new_engine.calculate_pattern_debts(history)

        # Should only track PUSH, not crash on empty list
        assert debts["PUSH"] == 4
        assert debts["SQUAT"] == 100  # Default for untracked patterns

    def test_pattern_debts_no_history(self, new_engine: WorkoutEngine) -> None:
        """Test pattern debt calculation with no history."""
        history = TrainingHistory()

        debts = new_engine.calculate_pattern_debts(history)

        # All patterns should have default debt of 100
        assert debts["SQUAT"] == 100
        assert debts["HINGE"] == 100
        assert debts["PUSH"] == 100
        assert debts["PULL"] == 100

    def test_pattern_debts_most_recent_date(self, new_engine: WorkoutEngine) -> None:
        """Test that most recent date is used when pattern appears multiple times."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=10),
                ),
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=2),  # More recent
                ),
            ]
        )

        debts = new_engine.calculate_pattern_debts(history)

        # Should use most recent date (2 days ago)
        assert debts["SQUAT"] == 2


class TestSkipLogic:
    """Tests for SKIP logic in session composition."""

    def test_skip_logic_red_state_squat(self, new_engine: WorkoutEngine) -> None:
        """Test that SQUAT is skipped in RED state and next pattern is selected."""
        readiness = Readiness(knee_pain=7, energy=5)  # RED state
        # SQUAT has highest debt but SKIPs in RED
        pattern_debts = {"SQUAT": 10, "HINGE": 8, "PUSH": 5, "PULL": 3}

        plan = new_engine.compose_gym_session(readiness, pattern_debts)

        # Assert SQUAT is NOT the main lift
        main_blocks = [b for b in plan.blocks if b.block_type == "MAIN"]
        assert len(main_blocks) == 1
        assert main_blocks[0].pattern != "SQUAT"
        # Should select next highest debt (HINGE) or next valid pattern
        # HINGE also SKIPs in RED, so should select PUSH or PULL
        assert main_blocks[0].pattern in ["PUSH", "PULL"]


class TestRelationshipLogic:
    """Tests for relationship-based accessory selection."""

    def test_relationship_logic_squat_accessories(
        self, new_engine: WorkoutEngine
    ) -> None:
        """Test that SQUAT main lift generates PULL_HORIZ and HINGE_HIP accessories."""
        readiness = Readiness(knee_pain=2, energy=7)  # GREEN state
        # Force SQUAT selection by giving it highest debt
        pattern_debts = {"SQUAT": 10, "HINGE": 3, "PUSH": 2, "PULL": 1}

        plan = new_engine.compose_gym_session(readiness, pattern_debts)

        # Assert main lift is SQUAT
        main_blocks = [b for b in plan.blocks if b.block_type == "MAIN"]
        assert len(main_blocks) == 1
        assert main_blocks[0].pattern == "SQUAT"

        # Assert accessories match relationship constraints
        accessory_blocks = [
            b for b in plan.blocks if b.block_type.startswith("ACCESSORY")
        ]
        accessory_patterns = [b.pattern for b in accessory_blocks]
        assert "PULL" in accessory_patterns  # PULL:ACCESSORY_HORIZONTAL
        assert "HINGE" in accessory_patterns  # HINGE:ACCESSORY_HIP


class TestBackwardCompatibility:
    """Tests for backward compatibility of computed fields."""

    def test_session_plan_computed_fields(self, new_engine: WorkoutEngine) -> None:
        """Test that SessionPlan includes computed fields in JSON output."""
        today = date.today()
        history = TrainingHistory(
            entries=[
                HistoryEntry(
                    impacted_patterns=["SQUAT"],
                    date=today - timedelta(days=5),
                ),
            ]
        )
        readiness = Readiness(knee_pain=2, energy=7)  # GREEN state

        plan = new_engine.generate_session(readiness, history)

        # Verify computed fields are present
        assert hasattr(plan, "exercises")
        assert isinstance(plan.exercises, list)
        assert len(plan.exercises) > 0

        assert hasattr(plan, "session_name")
        assert isinstance(plan.session_name, str)
        assert plan.session_name.startswith(plan.session_type)

        assert hasattr(plan, "archetype")
        assert plan.archetype == plan.session_type

        # Verify JSON serialization includes computed fields
        plan_dict = plan.model_dump()
        assert "exercises" in plan_dict
        assert "session_name" in plan_dict
        assert "archetype" in plan_dict
        assert "session_type" in plan_dict
        assert "blocks" in plan_dict
