# FLUX Agile Training Logic

## 1. Core Philosophy

The system is a **Non-Linear Session Composer**. It does not follow a static calendar. Instead, it generates a bespoke workout each day by triangulating:

1.  **Biological State:** The user's current capacity (Pain & Energy).
2.  **Training Inventory:** The "freshness" of movement patterns (Squat, Hinge, Push, Pull).
3.  **Role-Based Selection:** A strict separation between an exercise's *Identity* (what it is) and its *Role* (is it a Main Lift today?).

## 2. The Input Layer (Daily Triage)

Every session begins with a check-in that determines the **Traffic Light State**.

### A. Inputs

* **Knee Pain (0–10):** A specific constraint for lower-body loading.
* **Energy Level (0–10):** A systemic constraint for volume and intensity.

### B. The Traffic Light Logic (`logic.yaml`)

The system maps these inputs to a discrete state:
* **GREEN (Full Intensity):** Low Pain (<4) AND High Energy (>6).
    * *Focus:* Heavy loading, high impact, complex movements.
* **ORANGE (Modified Volume):** Moderate Pain (4–6) OR Low Energy (<6).
    * *Focus:* Controlled tempo, reduced range of motion, moderate volume.
* **RED (Recovery Focus):** High Pain (>6).
    * *Focus:* No heavy spinal loading. Isometrics. Blood flow.

## 3. The Session Engine (Logic Flow)

The engine generates one of two distinct session types based on the Traffic Light State.

### Scenario A: The Performance Session (Green/Orange)
If the state is **GREEN** or **ORANGE**, the engine builds a standard "Gym Session" with 5 distinct blocks.

**The Selection Algorithm:**

1.  **Calculate Freshness (Time Delta):** Identify which Main Pattern (Squat, Hinge, Push, Pull) has been neglected the longest by calculating the real-time UTC elapsed duration between `datetime.now()` and the pattern's `last_trained` timestamp. Patterns with `null` timestamps (never trained) have infinite elapsed time and highest priority.
2.  **Tie-Break (Pattern Order):** When two or more patterns have the exact same elapsed time (e.g., multiple `null` values), the engine picks one using a fixed priority order. The **default pattern ordering** is defined in **`logic.yaml`** under `pattern_priority` (e.g. SQUAT → PUSH → HINGE → PULL; first in the list has highest priority).
3.  **Select Main Lift:** Look up the `MAIN` exercise for that pattern in `selections.yaml` for the current color (e.g., *Green Squat* -> *Back Squat*).
4.  **Select Accessories:** Look up the pre-defined complementary accessories for that Main Pattern.
5.  **Append Conditioning:** Select a protocol based on the current energy level.

**Conditioning Progression:** When the user completes a session and has completed a conditioning block, the backend increments that protocol's level by **+1** (linear progression). The **protocol definitions and level structure** (work/rest, rounds, and max level) are defined in **`conditioning.yaml`**. HIIT and SIT each have multiple levels (e.g. up to level 7); Steady State (SS) has a single level (1) and does not progress, therefore it is intentionally omitted from the user's saved state document.

**The Block Structure (`sessions.yaml`):**

1.  **PREP:** Movement preparation specific to the Main Pattern (e.g., Hip Flow).
2.  **POWER:** Neural priming.
    * *Green:* Ballistic/Plyometric (e.g., Box Jumps).
    * *Orange:* Low-impact Power (e.g., Med Ball Throws).
3.  **STRENGTH (Main):** The primary compound lift of the day.
    * *Green:* Heavy Compound (e.g., Back Squat).
    * *Orange:* Tempo/Variation (e.g., Tempo Goblet Squat).
4.  **ACCESSORIES:** Supplemental volume.
    * *Structure:* Always 2 exercises (Accessory 1 + Accessory 2).
    * *Logic:* Hard-coded to balance the Main Lift (e.g., Squat Main -> Pull + Hinge Accessories).
5.  **CONDITIONING:** Metabolic work.
    * *Green/Orange:* Intervals or Capacity (e.g., "6 x 10s on / 40s off").

### Scenario B: The Recovery Session (Red)

If the state is **RED**, the engine switches to a "Repair" archetype. The goal is to retain tissue quality without aggravating pain.

**The Block Structure:**

1.  **MOBILITY (Checklist):** A flow of restorative movements (e.g., Cat Cow, 90/90).
2.  **ISOMETRICS (Timed):** Long-duration static holds to manage tendon pain (e.g., Spanish Squat Hold, 5 x 45s).
3.  **ACCESSORIES:** Low-impact isolation work (e.g., Glute Bridges, Core).
4.  **CONDITIONING:** Low-intensity steady state (Zone 2) to promote blood flow.

## 4. The Data Architecture

### A. Configuration Files

The brain of the logic is split into specific YAML files:

* **`library.yaml`:** The "Grocery Store." Defines the *Identity* of every exercise (Name, Default Unit, Category).
* **`selections.yaml`:** The "Menu." Defines the *Role* of exercises. Explicitly maps `Pattern -> Tier -> Color -> Exercise`.
* **`sessions.yaml`:** The "Recipe." Defines the block structure (Prep -> Power -> Main...) for each archetype.
* **`logic.yaml`:** Defines thresholds (Traffic Light), **pattern tie-break order** (`pattern_priority`), and power/accessory relationships.
* **`conditioning.yaml`:** Defines conditioning protocols (HIIT, SIT, SS), **level structure** (work/rest, rounds per level), and max level; progression (+1 on completion) is applied by the backend using this file. Steady State (SS) is defined here but excluded from the user state database since it does not progress.

### B. Smart Input Logic (Frontend Contract)

The system "Enriches" every block with metadata so the UI knows how to track it:

| Mode | Triggers | UI Behavior |
| :--- | :--- | :--- |
| **WEIGHTED_REPS** | `unit='REPS'`, `is_bw=False` | **Weight (kg)** + **Reps** + **RPE** |
| **WEIGHTED_TIME** | `unit='SECS'`, `is_bw=False` | **Weight (kg)** + **Time (s)** + **RPE** |
| **BODYWEIGHT_REPS** | `unit='REPS'`, `is_bw=True` | **"Bodyweight + [ ] kg"** + **Reps** |
| **BODYWEIGHT_TIME** | `unit='SECS'`, `is_bw=True` | **"Bodyweight + [ ] kg"** + **Time (s)** |
| **CONDITIONING** | `block_type='CONDITIONING'` | **Multi-Row Input:** `rounds` determine row count. Input **Watts** + **Distance**. |
| **CHECKLIST** | `block_type='PREP'`/`MOBILITY` | Simple **Checkbox**. No load tracking. |

### C. Accessory Grouping

* **Backend:** Returns `ACCESSORY_1` and `ACCESSORY_2` as distinct blocks to allow precise exercise selection.
* **Frontend:** Automatically groups these into a single "ACCESSORIES" page/card for a streamlined user experience.

## 5. Summary of Logic

* **No Randomization:** Every workout is deterministic based on the intersection of **State** (Red/Orange/Green) and **History** (Time Elapsed / Last Trained Timestamp).
* **Identity vs. Role:** An exercise like "Split Squat" can be a *Main Lift* on an Orange Day, but an *Accessory* on a Green Day. This is controlled via `selections.yaml`.
* **Red Day Safety:** The Red state hard-switches to a completely different session structure (Mobility/Iso), ensuring the user never faces a heavy barbell when their biological markers are low.
