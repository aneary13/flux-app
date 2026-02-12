"""Configuration loader for modular YAML config (library, logic, sessions, selections, conditioning)."""

from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field


# --- Library ---


class CatalogEntrySettings(BaseModel):
    """Optional settings for a catalog exercise."""

    unit: str | None = None  # REPS, SECS, WATTS
    unilateral: bool = False
    load: str | None = None  # WEIGHTED, BODYWEIGHT


class CatalogEntry(BaseModel):
    """Single exercise in the library catalog."""

    name: str
    category: str
    settings: CatalogEntrySettings | Dict[str, Any] | None = None

    def get_settings(self) -> Dict[str, Any]:
        """Return settings as a dict for easy lookup (unit, unilateral, load)."""
        if self.settings is None:
            return {}
        if isinstance(self.settings, CatalogEntrySettings):
            return self.settings.model_dump(exclude_none=True)
        return dict(self.settings)


class LibraryConfig(BaseModel):
    """The catalog and metadata for all exercises."""

    catalog: List[CatalogEntry] = Field(default_factory=list)


# --- Logic ---


class PatternsConfig(BaseModel):
    """Pattern groups for main, accessory, core."""

    main: List[str] = Field(default_factory=list)
    accessory: List[str] = Field(default_factory=list)
    core: List[str] = Field(default_factory=list)


class PowerSelectionConfig(BaseModel):
    """Power selection by state."""

    GREEN: str = "HIGH"
    ORANGE: str = "LOW"
    RED: str = "UPPER"


class LogicConfig(BaseModel):
    """Thresholds, pattern priority, power selection, relationships."""

    thresholds: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    pattern_priority: List[str] = Field(default_factory=list)
    power_selection: PowerSelectionConfig = Field(default_factory=PowerSelectionConfig)
    relationships: Dict[str, List[str]] = Field(default_factory=dict)
    patterns: PatternsConfig = Field(default_factory=PatternsConfig)


# --- Sessions ---


class BlockComponent(BaseModel):
    """Single block in session structure."""

    block: str
    components: List[str] = Field(default_factory=list)


class RecoveryIsometricEntry(BaseModel):
    """Repair isometric for RECOVERY session."""

    name: str
    settings: Dict[str, int | str] = Field(default_factory=dict)


class RecoveryConfig(BaseModel):
    """RECOVERY (Red Day) session definition."""

    structure: List[BlockComponent] = Field(default_factory=list)
    mobility_flow: List[str] = Field(default_factory=list)
    repair_isometrics: List[RecoveryIsometricEntry] = Field(default_factory=list)


class GymConfig(BaseModel):
    """GYM session structure."""

    structure: List[BlockComponent] = Field(default_factory=list)


class SessionConfig(BaseModel):
    """Session archetypes: GYM and RECOVERY."""

    GYM: GymConfig = Field(default_factory=GymConfig)
    RECOVERY: RecoveryConfig = Field(default_factory=RecoveryConfig)


# --- Selections: pattern -> tier -> state -> name (or list for RFD) ---
# Stored as plain dict for dynamic keys (SQUAT, HINGE, PUSH, RFD, ...).


# --- Conditioning ---


class ConditioningProtocolEntry(BaseModel):
    """Single conditioning protocol."""

    tier: str
    level: int
    description: str
    work_duration: int | None = None
    rest_duration: int | None = None
    rounds: int = 1
    target_modifier: str | None = None


class ConditioningConfig(BaseModel):
    """Conditioning protocols and equipment."""

    equipment: str = ""
    protocols: List[ConditioningProtocolEntry] = Field(default_factory=list)


# --- Root Program Config ---


class ProgramConfig(BaseModel):
    """Root configuration built from the 5 domain YAML files."""

    library: LibraryConfig = Field(default_factory=LibraryConfig)
    logic: LogicConfig = Field(default_factory=LogicConfig)
    sessions: SessionConfig = Field(default_factory=SessionConfig)
    selections: Dict[str, Dict[str, Dict[str, str] | List[str]]] = Field(
        default_factory=dict,
        description="Pattern -> Tier -> State -> exercise name (or list for RFD)",
    )
    conditioning: ConditioningConfig = Field(default_factory=ConditioningConfig)


def load_config(config_dir: Path) -> ProgramConfig:
    """Load all 5 YAML files and merge into ProgramConfig.

    Args:
        config_dir: Directory containing library.yaml, logic.yaml, sessions.yaml,
                    selections.yaml, conditioning.yaml.

    Returns:
        ProgramConfig with library, logic, sessions, selections, conditioning.
    """
    config_dir = Path(config_dir)

    def load_yaml(name: str) -> dict:
        path = config_dir / name
        if not path.exists():
            return {}
        with path.open() as f:
            return yaml.safe_load(f) or {}

    library_data = load_yaml("library.yaml")
    logic_data = load_yaml("logic.yaml")
    sessions_data = load_yaml("sessions.yaml")
    selections_data = load_yaml("selections.yaml")
    conditioning_data = load_yaml("conditioning.yaml")

    library = LibraryConfig(**library_data)
    logic = LogicConfig(**logic_data)
    sessions = SessionConfig(**sessions_data)
    selections = selections_data  # keep as dict
    conditioning = ConditioningConfig(**conditioning_data)

    return ProgramConfig(
        library=library,
        logic=logic,
        sessions=sessions,
        selections=selections,
        conditioning=conditioning,
    )
