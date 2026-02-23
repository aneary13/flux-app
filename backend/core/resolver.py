from typing import Dict, Any, Tuple, List

class WorkoutResolver:
    """
    The FLUX Engine. 
    Translates biological inputs and system configs into a structured training session.
    """
    def __init__(self, configs: Dict[str, Any], exercises: List[Dict[str, Any]]):
        # 1. Load the "Brain"
        self.logic = configs.get("logic", {})
        self.sessions = configs.get("sessions", {})
        self.selections = configs.get("selections", {})
        self.conditioning = configs.get("conditioning", {})
        
        # 2. Build a fast-lookup dictionary for exercises
        self.exercise_catalog = {ex["name"]: ex for ex in exercises}
        
        # 3. Session State Variables (populated during generation)
        self.current_state = "GREEN"
        self.archetype = "PERFORMANCE"
        self.main_pattern = None

    def _evaluate_state(self, knee_pain: int, energy: int) -> Tuple[str, str]:
        """
        Translates Pain & Energy into a biological State (GREEN/ORANGE/RED) 
        and an Archetype (PERFORMANCE/RECOVERY).
        """
        thresholds = self.logic.get("thresholds", {})
        kp_limits = thresholds.get("knee_pain", {"lower": 3, "upper": 6})
        en_limits = thresholds.get("energy", {"lower": 2, "upper": 5})

        # Evaluate Pain
        if knee_pain >= kp_limits["upper"]:
            pain_state = "RED"
        elif knee_pain > kp_limits["lower"]:
            pain_state = "ORANGE"
        else:
            pain_state = "GREEN"

        # Evaluate Energy (Note: Energy is inverse. Low energy = RED)
        if energy <= en_limits["lower"]:
            energy_state = "RED"
        elif energy < en_limits["upper"]:
            energy_state = "ORANGE"
        else:
            energy_state = "GREEN"

        # Resolve Final Status (The worst score dictates the state)
        if pain_state == "RED" or energy_state == "RED":
            return "RED", "RECOVERY"
        elif pain_state == "ORANGE" or energy_state == "ORANGE":
            return "ORANGE", "PERFORMANCE"
        else:
            return "GREEN", "PERFORMANCE"
    
    def _resolve_main_pattern(self, pattern_debts: Dict[str, int]) -> str:
        """
        Calculates which pattern is 'due' based on historical debt and priority tie-breakers.
        """
        # If no history exists, default to 0 for all priorities
        priorities = self.logic.get("pattern_priority", ["SQUAT", "PUSH", "HINGE", "PULL"])
        if not pattern_debts:
            pattern_debts = {p: 0 for p in priorities}

        # 1. Find the highest debt value (e.g., 5 days)
        max_debt = max(pattern_debts.values())
        
        # 2. Find all patterns tied for that highest debt
        due_patterns = [p for p, d in pattern_debts.items() if d == max_debt]

        # 3. Tie-breaker: Consult the system priority list
        for pattern in priorities:
            if pattern in due_patterns:
                self.main_pattern = pattern
                return pattern
                
        # Fallback safeguard
        self.main_pattern = due_patterns[0]
        return self.main_pattern

    def _enrich_exercise(self, exercise_name: str) -> Dict[str, Any]:
        """
        Attaches the frontend rendering metadata (units, load type) to the raw exercise name.
        """
        metadata = self.exercise_catalog.get(exercise_name, {})
        return {
            "name": exercise_name,
            "is_unilateral": metadata.get("is_unilateral", False),
            "tracking_unit": metadata.get("tracking_unit", "REPS"),
            "load_type": metadata.get("load_type", "WEIGHTED")
        }

    def _resolve_literal(self, category: str, pattern: str) -> List[Dict[str, Any]]:
        """
        Takes a strict literal (e.g., 'SQUAT', 'MAIN') and returns the enriched exercises.
        """
        # Navigate the selections dictionary: selections -> SQUAT -> MAIN
        options = self.selections.get(category, {}).get(pattern, {})
        
        # Determine which list of exercises to pull based on state or defaults
        exercise_names = []
        if self.current_state in options:
            exercise_names = options[self.current_state]  # e.g., GREEN -> ["Back Squat"]
        elif "DEFAULT" in options:
            exercise_names = options["DEFAULT"]
        elif options:
            # Fallback to the first available key if state/default is missing
            exercise_names = next(iter(options.values()))
            
        return [self._enrich_exercise(name) for name in exercise_names]

    def _parse_component(self, component_str: str) -> List[Dict[str, Any]]:
        """
        Interprets layout strings ('MAIN_PATTERN', 'RELATED_ACCESSORIES', 'MOBILITY:DYNAMIC') 
        and resolves them into a list of enriched exercises.
        """
        # 1. Handle dynamic Keyword: MAIN_PATTERN
        if component_str == "MAIN_PATTERN":
            if not self.main_pattern:
                raise ValueError("Main pattern has not been resolved yet!")
            return self._resolve_literal(self.main_pattern, "MAIN")

        # 2. Handle dynamic Keyword: RELATED_ACCESSORIES
        if component_str == "RELATED_ACCESSORIES":
            accessories = self.logic.get("relationships", {}).get(self.main_pattern, [])
            resolved_accs = []
            for acc in accessories:
                # Accessories are stored as "HINGE:ACCESSORY_KNEE"
                cat, pat = acc.split(":")
                resolved_accs.extend(self._resolve_literal(cat, pat))
            return resolved_accs

        # 3. Handle specific Literals: e.g., "MOBILITY:DYNAMIC"
        if ":" in component_str:
            cat, pat = component_str.split(":")
            return self._resolve_literal(cat, pat)

        # 4. Handle broad Categories: e.g., "CORE"
        # (For now, we'll just pick the first sub-pattern in the category as a default)
        category_dict = self.selections.get(component_str, {})
        if category_dict:
            first_pattern = next(iter(category_dict.keys()))
            return self._resolve_literal(component_str, first_pattern)
            
        return []

    def _resolve_conditioning(self, component_str: str, conditioning_levels: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Resolves the conditioning block based on the protocol and the user's current progression level.
        """
        if ":" in component_str:
            _, protocol = component_str.split(":")
        else:
            protocol = "HIIT" 
            
        current_level = conditioning_levels.get(protocol, 1)
        level_str = str(current_level)
        
        protocols_data = self.conditioning.get("protocols", {})
        protocol_data = protocols_data.get(protocol, {})
        
        if level_str not in protocol_data and protocol_data:
            max_level = max([int(k) for k in protocol_data.keys()])
            level_str = str(max_level)
            
        level_details = protocol_data.get(level_str, {})
        equipment = self.conditioning.get("equipment", "Assault Bike")
        tracking_unit = self.conditioning.get("tracking_unit", "WATTS")
        
        return [{
            "name": f"{equipment} - {protocol} (Level {level_str})",
            "is_unilateral": False,
            "load_type": "BODYWEIGHT",
            "tracking_unit": tracking_unit,
            "is_conditioning": True,
            "description": level_details.get("description", ""),
            "rounds": level_details.get("rounds", 1),
            "work_seconds": level_details.get("work_seconds"),
            "rest_seconds": level_details.get("rest_seconds"),
            "is_benchmark": level_details.get("is_benchmark", False)
        }]

    def generate_session(self, knee_pain: int, energy: int, pattern_debts: Dict[str, int], conditioning_levels: Dict[str, int] = None) -> Dict[str, Any]:
        """
        The master function that builds the entire workout.
        """
        if conditioning_levels is None:
            conditioning_levels = {}

        self.current_state, self.archetype = self._evaluate_state(knee_pain, energy)
        self._resolve_main_pattern(pattern_debts)
        
        layout_templates = self.sessions.get(self.archetype, {}).get("blocks", [])
        
        resolved_blocks = []
        for block in layout_templates:
            resolved_components = []
            
            for component_str in block.get("components", []):
                if "CONDITIONING" in component_str:
                    # Pass the updated variable here
                    exercises = self._resolve_conditioning(component_str, conditioning_levels)
                    resolved_components.extend(exercises)
                    continue 
                
                exercises = self._parse_component(component_str)
                resolved_components.extend(exercises)
                
            resolved_blocks.append({
                "type": block.get("type"),
                "label": block.get("label"),
                "exercises": resolved_components
            })
            
        return {
            "metadata": {
                "state": self.current_state,
                "archetype": self.archetype,
                "anchor_pattern": self.main_pattern
            },
            "blocks": resolved_blocks
        }
