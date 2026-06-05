from datetime import datetime
from typing import Any


class WorkoutResolver:
    """
    The FLUX Engine.
    Translates biological inputs and system configs into a structured training session.
    """

    def __init__(self, configs: dict[str, Any], exercises: list[dict[str, Any]]):
        # 1. Load the "Brain"
        self.logic = configs.get("logic", {})
        self.sessions = configs.get("sessions", {})
        self.selections = configs.get("selections", {})
        self.conditioning = configs.get("conditioning", {})

        # 2. Build a fast-lookup dictionary for exercises
        self.exercise_catalog = {ex["name"]: ex for ex in exercises}

        # 3. Session State Variables (populated during generation)
        self.current_state = "GREEN"
        self.archetype = "GREEN_ORANGE"
        self.main_pattern: str | None = None

    def _evaluate_state(self, knee_pain: int, energy: int) -> tuple[str, str]:
        """
        Translates Pain & Energy into a biological State (GREEN/ORANGE/RED)
        and a session template key (GREEN_ORANGE/RED).
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
            return "RED", "RED"
        elif pain_state == "ORANGE" or energy_state == "ORANGE":
            return "ORANGE", "GREEN_ORANGE"
        else:
            return "GREEN", "GREEN_ORANGE"

    def _resolve_main_pattern(self, last_trained: dict[str, str | None]) -> str:
        """
        Determines which pattern is next in the configured rotation order,
        based on which pattern was most recently performed.
        """
        rotation: list[str] = self.logic.get("rotation_order", ["SQUAT", "PUSH", "HINGE", "PULL"])

        if not last_trained or all(v is None for v in last_trained.values()):
            self.main_pattern = rotation[0]
            return rotation[0]

        # Find the most recently trained pattern
        most_recent_pattern = None
        most_recent_time: datetime | None = None
        for pattern in rotation:
            ts = last_trained.get(pattern)
            if ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if most_recent_time is None or dt > most_recent_time:
                    most_recent_time = dt
                    most_recent_pattern = pattern

        if most_recent_pattern is None:
            self.main_pattern = rotation[0]
            return rotation[0]

        # Next in rotation after the most recently trained
        idx = rotation.index(most_recent_pattern)
        next_pattern = rotation[(idx + 1) % len(rotation)]
        self.main_pattern = next_pattern
        return next_pattern

    def _enrich_exercise(self, exercise_name: str) -> dict[str, Any]:
        """
        Attaches the frontend rendering metadata (units, load type) to the raw exercise name.
        """
        metadata = self.exercise_catalog.get(exercise_name, {})
        return {
            "name": exercise_name,
            "is_unilateral": metadata.get("is_unilateral", False),
            "tracking_unit": metadata.get("tracking_unit", "REPS"),
            "load_type": metadata.get("load_type", "WEIGHTED"),
        }

    def _resolve_literal(self, category: str, pattern: str) -> list[dict[str, Any]]:
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

    def _resolve_episodic_flow(
        self, category: str, subcategory: str, flow_index: int
    ) -> list[dict[str, Any]]:
        """
        Selects a flow from an array-of-arrays using modulo math, then enriches
        each exercise in that flow. The flow_index advances each session so the
        user cycles through all defined flows before repeating.
        """
        flows = self.selections.get(category, {}).get(subcategory, {}).get("flows", [])
        if not flows:
            return []
        selected_flow = flows[flow_index % len(flows)]
        return [self._enrich_exercise(name) for name in selected_flow]

    def _parse_component(self, component_str: str) -> list[dict[str, Any]]:
        """
        Interprets layout strings ('MAIN_PATTERN', 'PAIRED_ACCESSORIES', 'MOBILITY:DYNAMIC')
        and resolves them into a list of enriched exercises.
        """
        # 1. Handle dynamic Keyword: MAIN_PATTERN
        if component_str == "MAIN_PATTERN":
            if not self.main_pattern:
                raise ValueError("Main pattern has not been resolved yet!")
            return self._resolve_literal(self.main_pattern, "MAIN")

        # 2. Handle dynamic Keyword: POWER_BLOCK (GREEN→intensive plyos, ORANGE→isometrics)
        if component_str == "POWER_BLOCK":
            if self.current_state == "GREEN":
                pairings = self.selections.get("workout_pairings", {})
                pairing = pairings.get(self.main_pattern, {})
                plyo_index = pairing.get("intensive_plyo_set", 0)
                return self._resolve_episodic_flow("PLYO", "INTENSIVE", plyo_index)
            else:
                # ORANGE: use isometrics instead of intensive plyos
                return self._resolve_literal("ISOMETRIC", "PATELLAR")

        # 3. Handle dynamic Keyword: PAIRED_ACCESSORIES
        if component_str == "PAIRED_ACCESSORIES":
            pairings = self.selections.get("workout_pairings", {})
            pairing = pairings.get(self.main_pattern, {})
            accessories = pairing.get("accessories", [])
            resolved = []
            for acc_str in accessories:
                cat, pat = acc_str.split(":")
                resolved.extend(self._resolve_literal(cat, pat))
            return resolved

        # 4. Handle specific Literals with Colons: e.g., "PUSH:ACCESSORY" or "MOBILITY:DYNAMIC"
        if ":" in component_str:
            cat, pat = component_str.split(":")

            # If the pattern is a generic "ACCESSORY" placeholder (common in RED sessions),
            # we must resolve it to a concrete sub-key in the selections dictionary.
            if pat == "ACCESSORY":
                # Look up available sub-patterns for category (e.g. PUSH -> HORIZONTAL, VERTICAL)
                available_patterns = list(self.selections.get(cat, {}).keys())

                # Filter out 'MAIN' to ensure we only pick actual accessory movements
                accessory_options = [p for p in available_patterns if p != "MAIN"]

                if accessory_options:
                    pat = accessory_options[0]

            # Episodic flow dispatch for MOBILITY:DYNAMIC, PLYO:EXTENSIVE
            EPISODIC_FLOW_MAP = {
                ("MOBILITY", "DYNAMIC"): "mobility",
                ("PLYO", "EXTENSIVE"): "extensive_plyo",
            }
            flow_key = EPISODIC_FLOW_MAP.get((cat, pat))
            if flow_key is not None:
                return self._resolve_episodic_flow(cat, pat, self.flow_indices.get(flow_key, 0))

            return self._resolve_literal(cat, pat)

        # 5. Handle broad Categories: e.g., "CORE"
        # Derives available planes dynamically from YAML keys so the resolver
        # is agnostic to which planes are defined.
        if component_str == "CORE":
            planes = list(self.selections.get("CORE", {}).keys())
            core_index = self.flow_indices.get("core_plane", 0)
            plane = planes[core_index % len(planes)]
            return self._resolve_literal("CORE", plane)

        category_dict = self.selections.get(component_str, {})
        if category_dict:
            first_pattern = next(iter(category_dict.keys()))
            return self._resolve_literal(component_str, first_pattern)

        return []

    def _resolve_conditioning(
        self,
        component_str: str,
        conditioning_levels: dict[str, int],
        benchmarks: dict[str, float],
        last_conditioning_protocol: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Resolves the conditioning block based on protocol progression,
        alternating logic, and benchmark logic.
        """
        # 1. The Alternator: Dynamic Protocol Selection
        if ":" in component_str:
            # E.g., "CONDITIONING:SS" explicitly asks for SS
            _, protocol = component_str.split(":")
        else:
            # Alternate based on what was last performed
            if last_conditioning_protocol == "HIIT":
                protocol = "SIT"
            elif last_conditioning_protocol == "SIT":
                protocol = "HIIT"
            else:
                protocol = "HIIT"

        current_level = conditioning_levels.get(protocol, 1)
        level_str = str(current_level)

        protocols_data = self.conditioning.get("protocols", {})
        protocol_data = protocols_data.get(protocol, {})

        if level_str not in protocol_data and protocol_data:
            max_level = max([int(k) for k in protocol_data])
            level_str = str(max_level)

        level_details = protocol_data.get(level_str, {})
        equipment = self.conditioning.get("equipment", "Rowing Machine")
        tracking_unit = self.conditioning.get("tracking_unit", "WATTS")

        # 2. Benchmark Math & Target Intensity
        target_intensity = None
        is_benchmark: bool = bool(level_details.get("is_benchmark", False))

        if protocol == "HIIT" and not is_benchmark:
            # Retrieve the benchmark watts from the user's state
            hiit_benchmark = benchmarks.get("HIIT_WATTS")

            # Look for an intensity multiplier in your YAML (e.g., 1.2 for 120%), default to 1.2
            intensity_multiplier = level_details.get("intensity_multiplier", 1.2)

            if hiit_benchmark:
                target_intensity = round(hiit_benchmark * intensity_multiplier)

        elif protocol == "SIT":
            # SIT is an all-out sprint, no specific wattage calculation
            target_intensity = "MAX"

        return [
            {
                "name": equipment,
                "is_unilateral": False,
                "load_type": "BODYWEIGHT",
                "tracking_unit": tracking_unit,
                "is_conditioning": True,
                "description": level_details.get("description", protocol),
                "protocol": protocol,
                "rounds": level_details.get("rounds", 1),
                "work_seconds": level_details.get("work_seconds"),
                "rest_seconds": level_details.get("rest_seconds"),
                "is_benchmark": is_benchmark,
                "target_intensity": target_intensity,
            }
        ]

    def generate_session(
        self,
        knee_pain: int,
        energy: int,
        last_trained: dict[str, str | None],
        conditioning_levels: dict[str, int] | None = None,
        benchmarks: dict[str, float] | None = None,
        flow_indices: dict[str, int] | None = None,
        last_conditioning_protocol: str | None = None,
    ) -> dict[str, Any]:
        """
        The master function that builds the entire workout.
        """
        if conditioning_levels is None:
            conditioning_levels = {}
        if benchmarks is None:
            benchmarks = {}
        if flow_indices is None:
            flow_indices = {}
        self.flow_indices = flow_indices

        self.current_state, self.archetype = self._evaluate_state(knee_pain, energy)
        self._resolve_main_pattern(last_trained)

        layout_templates = self.sessions.get(self.archetype, {}).get("blocks", [])

        resolved_blocks = []
        for block in layout_templates:
            resolved_components = []

            for component in block.get("components", []):
                component_key = (
                    component.get("key", component) if isinstance(component, dict) else component
                )
                # Allow state-specific label overrides (e.g. orange_label for ORANGE days)
                state_label_key = f"{self.current_state.lower()}_label"
                if isinstance(component, dict) and state_label_key in component:
                    component_label = component[state_label_key]
                else:
                    component_label = (
                        component.get("label", component_key)
                        if isinstance(component, dict)
                        else component_key
                    )

                if "CONDITIONING" in component_key:
                    exercises = self._resolve_conditioning(
                        component_key,
                        conditioning_levels,
                        benchmarks,
                        last_conditioning_protocol,
                    )
                else:
                    exercises = self._parse_component(component_key)

                if exercises:
                    resolved_components.append(
                        {
                            "label": component_label,
                            "exercises": exercises,
                        }
                    )

            # Filter out empty blocks
            if resolved_components:
                resolved_blocks.append(
                    {
                        "type": block.get("type"),
                        "label": block.get("label"),
                        "components": resolved_components,
                    }
                )

        state_display_map = {
            "GREEN": "Full Intensity Training",
            "ORANGE": "Modified Training",
            "RED": "Rehab and Recovery",
        }

        return {
            "metadata": {
                "state": self.current_state,
                "archetype": self.archetype,
                "anchor_pattern": self.main_pattern,
                "state_display_text": state_display_map.get(
                    self.current_state, "Full Intensity Training"
                ),
            },
            "blocks": resolved_blocks,
        }
