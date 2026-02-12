"""WorkoutEngine - Core logic for determining next best action (Session Builder: GYM + Conditioning)."""

from datetime import date
from pathlib import Path
from typing import Dict, List

import yaml
from simpleeval import SimpleEval

from src.models import (
    ExerciseBlock,
    HistoryEntry,
    ProgramConfig,
    Readiness,
    SessionPlan,
    TrainingHistory,
)


class WorkoutEngine:
    """Engine for determining the next best training session."""

    def __init__(self, config_path: str | Path) -> None:
        """Initialize engine with configuration file.

        Args:
            config_path: Path to program_config.yaml file
        """
        config_path = Path(config_path)
        with config_path.open() as f:
            config_data = yaml.safe_load(f)
        self.config = ProgramConfig(**config_data)

    def determine_state(self, readiness: Readiness) -> str:
        """Determine readiness state based on pain and energy levels.

        Evaluates state conditions in order (RED → ORANGE → GREEN).
        GREEN is the default catch-all if no previous states match.

        Args:
            readiness: User readiness with pain and energy levels

        Returns:
            State name ("RED", "ORANGE", or "GREEN")
        """
        # Create safe evaluator with only readiness fields
        evaluator = SimpleEval(names={"knee_pain": readiness.knee_pain, "energy": readiness.energy})

        # Evaluate states in order (RED → ORANGE → GREEN)
        for state in self.config.states:
            if state.condition.lower() == "default":
                # GREEN is the default catch-all
                return state.name

            try:
                # Normalize logical operators to lowercase for simpleeval
                condition = state.condition.replace(" OR ", " or ").replace(" AND ", " and ")
                result = evaluator.eval(condition)
                if result:
                    return state.name
            except Exception:
                # If evaluation fails, skip to next state
                continue

        # Fallback to GREEN if somehow no state matched
        return "GREEN"

    def calculate_pattern_debts(self, history: TrainingHistory) -> Dict[str, int]:
        """Calculate days since last occurrence for each pattern.

        Handles legacy data gracefully by skipping entries with None or empty
        impacted_patterns. Returns default debt of 100 for patterns never performed.

        Args:
            history: User training history with impacted_patterns

        Returns:
            Dictionary mapping pattern names to days since last occurrence
        """
        today = date.today()
        pattern_last_dates: Dict[str, date] = {}

        # Track most recent date for each pattern
        for entry in history.entries:
            # Skip entries with None or empty impacted_patterns (legacy data)
            if not entry.impacted_patterns:
                continue

            for pattern in entry.impacted_patterns:
                if pattern not in pattern_last_dates:
                    pattern_last_dates[pattern] = entry.date
                elif entry.date > pattern_last_dates[pattern]:
                    pattern_last_dates[pattern] = entry.date

        # Calculate debts for all patterns in config
        debts: Dict[str, int] = {}
        all_patterns = (
            self.config.patterns.main
            + self.config.patterns.accessory
            + self.config.patterns.core
        )

        for pattern in all_patterns:
            if pattern in pattern_last_dates:
                days_since = (today - pattern_last_dates[pattern]).days
                debts[pattern] = days_since
            else:
                # Pattern never performed - use high default to prioritize
                debts[pattern] = 100

        return debts

    def _get_exercise_from_library(
        self, pattern: str, tier: str, state: str
    ) -> str | None:
        """Get exercise name from library for given pattern, tier, and state.

        Args:
            pattern: Pattern name (e.g., "SQUAT", "CORE", "RFD")
            tier: Tier name (e.g., "MAIN", "ACCESSORY", "TRANSVERSE", "HIGH")
            state: State name (e.g., "GREEN", "ORANGE", "RED")

        Returns:
            Exercise name or None if not found
        """
        pattern_lib = self.config.library.get(pattern)
        if not pattern_lib:
            return None

        tier_lib = pattern_lib.get(tier)
        if not tier_lib:
            return None

        exercise = tier_lib.get(state)
        # Handle case where exercise might be a list (shouldn't happen for non-RFD)
        if isinstance(exercise, list):
            return None  # Lists are handled separately for RFD
        
        return exercise

    def compose_gym_session(
        self, readiness: Readiness, pattern_debts: Dict[str, int]
    ) -> SessionPlan:
        """Compose a gym session block-by-block (Level 2 logic).

        Args:
            readiness: User readiness with pain and energy levels
            pattern_debts: Dictionary of pattern debts

        Returns:
            SessionPlan with composed blocks

        Raises:
            ValueError: If no valid main lift is available
        """
        state = self.determine_state(readiness)
        blocks: List[ExerciseBlock] = []

        # Block 1: Prep
        # Follow session_structure.PREP: WARM_UP, PATELLAR_ISO, CORE
        
        # WARM_UP - could be pattern-specific warm-up (placeholder for now)
        # For now, we'll skip explicit warm-up and go to Patellar ISO
        
        # PATELLAR_ISO - always included, read from config
        patellar_exercise = self._get_exercise_from_library(
            "PATELLAR_ISO", "PREP", state
        )
        if patellar_exercise:
            blocks.append(
                ExerciseBlock(
                    block_type="PREP",
                    exercise_name=patellar_exercise,
                    pattern="PATELLAR_ISO",
                )
            )
        
        # CORE - select core pattern with highest debt
        core_patterns = self.config.patterns.core
        if core_patterns:
            core_debts = {
                pattern: pattern_debts.get(pattern, 100)
                for pattern in core_patterns
            }
            if core_debts:
                selected_core = max(core_debts.items(), key=lambda x: x[1])[0]
                # CORE has multiple tiers: TRANSVERSE, SAGITTAL, FRONTAL
                # Select tier with highest debt (for now, use TRANSVERSE as default)
                core_tiers = ["TRANSVERSE", "SAGITTAL", "FRONTAL"]
                # TODO: Could implement tier debt tracking in future
                selected_tier = core_tiers[0]  # Default to TRANSVERSE
                core_exercise = self._get_exercise_from_library(
                    selected_core, selected_tier, state
                )
                if core_exercise:
                    blocks.append(
                        ExerciseBlock(
                            block_type="PREP",
                            exercise_name=core_exercise,
                            pattern=selected_core,
                        )
                    )

        # Block 2: Power
        # Follow session_structure.POWER: RFD
        power_selection_dict = self.config.power_selection.model_dump()
        rfd_type = power_selection_dict[state]
        # RFD library structure: RFD -> HIGH/LOW/UPPER -> [list of exercises]
        rfd_lib = self.config.library.get("RFD", {})
        rfd_exercises = rfd_lib.get(rfd_type, [])
        if isinstance(rfd_exercises, list) and rfd_exercises:
            # Add all RFD exercises for the selected type
            for rfd_exercise in rfd_exercises:
                blocks.append(
                    ExerciseBlock(
                        block_type="POWER",
                        exercise_name=rfd_exercise,
                        pattern="RFD",
                    )
                )

        # Block 3: Main Lift
        main_patterns = self.config.patterns.main
        # Tie-breaker: when debts are equal, use pattern_priority (Lower/Upper rotation)
        priority_index = {
            name: idx for idx, name in enumerate(self.config.pattern_priority)
        }
        fallback_priority = len(self.config.pattern_priority)

        def sort_key(p: str) -> tuple:
            debt = pattern_debts.get(p, 100)
            idx = priority_index.get(p, fallback_priority)
            return (-debt, idx)

        sorted_main = sorted(main_patterns, key=sort_key)

        main_selected = False
        selected_main_pattern = None
        selected_main_exercise = None

        for pattern in sorted_main:
            exercise = self._get_exercise_from_library(pattern, "MAIN", state)
            if exercise and exercise != "SKIP":
                selected_main_pattern = pattern
                selected_main_exercise = exercise
                main_selected = True
                break

        if not main_selected:
            raise ValueError("No valid main lift available")

        blocks.append(
            ExerciseBlock(
                block_type="MAIN",
                exercise_name=selected_main_exercise,
                pattern=selected_main_pattern,
            )
        )

        # Block 4: Accessories
        # Follow session_structure.ACCESSORIES: RELATED_ACCESSORIES
        # Get required accessories from relationships (format: PATTERN:TIER)
        required_accessories = self.config.relationships.get(
            selected_main_pattern, []
        )

        for idx, accessory_spec in enumerate(required_accessories[:2], start=1):
            # Parse PATTERN:TIER format
            if ":" in accessory_spec:
                accessory_pattern, accessory_tier = accessory_spec.split(":", 1)
            else:
                # Fallback: assume ACCESSORY tier if not specified
                accessory_pattern = accessory_spec
                accessory_tier = "ACCESSORY"
            
            exercise = self._get_exercise_from_library(
                accessory_pattern, accessory_tier, state
            )
            if exercise and exercise != "SKIP":
                blocks.append(
                    ExerciseBlock(
                        block_type=f"ACCESSORY_{idx}",
                        exercise_name=exercise,
                        pattern=accessory_pattern,
                    )
                )

        return SessionPlan(session_type="GYM", blocks=blocks)


    def generate_session(
        self, readiness: Readiness, history: TrainingHistory
    ) -> SessionPlan:
        """Generate the recommended session plan (lifting blocks only).

        Every request is a GYM session. Returns Prep + Power + Main + Accessories
        only; the conditioning block is appended by the route via the conditioning
        service (Option II: Service Composition).

        Args:
            readiness: User readiness with pain and energy levels
            history: User training history

        Returns:
            SessionPlan with session_type="GYM" and lifting blocks only

        Raises:
            ValueError: If no valid main lift is available
        """
        pattern_debts = self.calculate_pattern_debts(history)
        return self.compose_gym_session(readiness, pattern_debts)
