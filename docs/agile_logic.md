# FLUX Agile Trainig Logic (v2.0)

## 1. Core Philosophy
The system does not follow a linear calendar. Instead, it acts as a **Session Composer**, building a bespoke workout each day based on **Biological Constraints** (Readiness) and **Training Inventory** (Debt).

*   **Satisficing:** We do not maximize every session; we aim for the Minimum Effective Dose (MED) to maintain qualities.
*   **Agile:** If a specific pattern (e.g., Squat) is contraindicated by pain, the system automatically pivots to the next best action or modifies the exercise, rather than cancelling the session.

---

## 2. The Input Layer (Daily Triage)

Before generating a session, the system evaluates three variables:

### A. Tendon Readiness (Traffic Light)
*   **GREEN (8–10):** Full Capacity. High load, high impact, reactive work permitted.
*   **ORANGE (5–7):** Modified. Controlled tempo, reduced range, low impact.
*   **RED (<5):** Intervention. No knee loading. Focus on Isometrics and Upper Body.

### B. Systemic Energy (CNS Status)
*   **HIGH (8–10):** Developmental. Full complexity/intensity permitted.
*   **MEDIUM (5–7):** Retainment. Moderate volume/intensity.
*   **LOW (<5):** Restorative. Active recovery or rest only.

### C. Inventory Debt (The Memory)
Calculated as: `Days Since Last Completed [Pattern]`.
*   *Global Patterns (Main Lifts):* SQUAT, HINGE, PUSH, PULL.
*   *Accessory Patterns:*
    *   PUSH (Vertical / Horizontal)
    *   PULL (Vertical / Horizontal)
    *   HINGE (Hip Extension / Knee Flexion)
    *   LUNGE
    *   CORE (Rotation / Lateral Flexion / Linear) — *Note: Core debt is tracked here but executed in the Prep Block.*

---

## 3. Level 1 Logic: Session Type Selector

The engine first determines the broad category of the day.

1.  **REST:** If Energy < 5.
2.  **GYM:** If Gym Pattern Debt > Conditioning Debt (and Energy ≥ 5).
3.  **CONDITIONING:** If Conditioning Debt > Gym Pattern Debt.

---

## 4. Level 2 Logic: The Session Composer (Gym)

If a **GYM** session is selected, the system builds it block-by-block using the following logic:

### Block 1: Prep & Prime
*   **Warmup:** General movement prep.
*   **Tendon Iso:** Mandatory Patellar Isometric (Standardized).
*   **Core:** Selects **1 Core Exercise** based on highest debt:
    *   *Core Patterns:* Anti-Rotation, Anti-Lateral Flexion, Linear (Flex/Ext).

### Block 2: Power (Neural)
Selected based on **Tendon Readiness** (Traffic Light):
*   **GREEN:** `RFD_HIGH` (e.g., Depth Jumps, Sprints, Oly Lifts).
*   **ORANGE:** `RFD_LOW` (e.g., KB Swings, Med Ball Throws).
*   **RED:** `RFD_UPPER` (e.g., Seated Med Ball Chest Pass, Battle Ropes) OR Skip.

### Block 3: Main Lift (Strength)
*   **Selection:** Identify the Broad Pattern (SQUAT, HINGE, PUSH, PULL) with the **Highest Debt**.
*   **Constraint Check:** Look up the specific exercise for `[Pattern] + [MAIN] + [Current State]`.
    *   If the result is specific exercise (e.g., "Box Squat") -> **Select it.**
    *   If the result is `SKIP` (e.g., Squat on a Red Day) -> **Discard Pattern.** Move to the Pattern with the *next highest debt*.

### Block 4: Accessories (Hypertrophy/Structural)
Accessories are **Hard-Coded Constraints** based on the chosen Main Lift to ensure systemic balance. The specific *variant* of the accessory is determined by Tendon Readiness.

| Selected Main Lift | Accessory 1 (Pattern) | Accessory 2 (Pattern) |
| :--- | :--- | :--- |
| **SQUAT** | PULL (Horizontal) | HINGE (Hip Extension) |
| **PUSH** (General) | SQUAT | PULL (Vertical) |
| **HINGE** | PUSH (Horizontal) | LUNGE |
| **PULL** (General) | HINGE (Knee Flexion) | PUSH (Vertical) |

*Note: Main Lifts are generic "PUSH/PULL". Accessories are specific (Horizontal/Vertical) to ensure plane balance.*

### Block 5: The Snack (Metabolic)
*   **Optional:** If Energy is High/Med, add 10-15m of low-CNS conditioning (e.g., AirBike, Rower, SkiErg).

---

## 5. Level 3 Logic: Conditioning Session
If a **CONDITIONING** session is selected, filter by Metabolic Debt + Tendon Status.

*   **AEROBIC_BASE:** (Long/Slow). Always available.
*   **AEROBIC_POWER:** (Intervals). Green=Run; Orange=Incline Walk; Red=Bike.
*   **ALACTIC:** (Max Speed). Green=Sprint; Orange=Sled; Red=Bike Sprint.
*   **LACTIC:** (Capacity). Green=Shuttles; Orange=Rower; Red=AirBike.

---

## 6. The Exercise Matrix (Library Architecture)
The database/config is organized as a 3D Matrix: `[Pattern] x [Tier] x [State]`.

**Example Entry: SQUAT**

| Tier          | Green State | Orange State       | Red State          |
| :------------ | :---------- | :----------------- | :----------------- |
| **MAIN**      | Back Squat  | Tempo Goblet Squat | **SKIP**           |
| **ACCESSORY** | Leg Press   | Split Squat        | Spanish Squat Hold |

**Example Entry: PUSH**

| Tier                 | Green State       | Orange State    | Red State                      |
| :------------------- | :---------------- | :-------------- | :----------------------------- |
| **MAIN**             | Bench Press       | Bench Press     | Larsen Press (Feet Up)         |
| **ACCESSORY (Vert)** | DB Overhead Press | Seated DB Press | Landmine Press (Half Kneeling) |

---

## 7. Removed Constraints (Simplification)
*   **Tendon Lag:** Removed. We rely on the natural rotation of patterns (Squat debt resets to 0 after training) and daily subjective readiness to manage load, rather than forcing a 24-hour lag.
*   **Lunge Main Lift:** Removed. Lunges are classified strictly as **Accessory** movements.
