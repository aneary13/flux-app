# FLUX Engine: Logic & Rules Summary (logic.yaml)

This document summarizes the internal decision-making logic of the FLUX Python backend. The frontend uses this context to understand why certain archetypes or exercise variations are presented.

---

## **1. Biological State Thresholds**
The engine evaluates the user's `knee_pain` and `energy` inputs to determine the session **Archetype**.

| Input | Threshold | Resulting Archetype |
| :--- | :--- | :--- |
| **Knee Pain** | > 3 (4-10) | **RECOVERY** (Protective loading) |
| **Energy** | < 4 (1-3) | **RECOVERY** (Reduced volume/intensity) |
| **Both** | Pain <= 3 AND Energy >= 4 | **PERFORMANCE** (Optimal training state) |

---

## **2. Pattern Selection Logic (The Anchor)**
FLUX uses a "Debt-Based" system to ensure movement variability.

* **Pattern Debt:** Every time a session is completed, the "Anchor Pattern" (e.g., SQUAT) resets to **0**, while all other patterns (PUSH, HINGE, PULL) increment by **1**.
* **Prioritization:** The pattern with the **highest debt** is selected as today's Anchor.
* **Tie-Breaking:** If debts are equal, the engine follows a hard-coded hierarchy:
    1.  **SQUAT** (Highest Priority)
    2.  **HINGE**
    3.  **PUSH**
    4.  **PULL** (Lowest Priority)

---

## **3. Archetype Constraints**
The Archetype modifies the contents of the session blocks:

### **PERFORMANCE Archetype**
* **POWER Block:** Included (Explosive movements like jumps or throws).
* **MAIN Block:** High intensity (Lower reps, higher RPE).
* **CONDITIONING:** Metabolic protocols (HIIT or SIT) are prioritized.

### **RECOVERY Archetype**
* **POWER Block:** Removed to reduce CNS fatigue and impact.
* **MAIN Block:** Reduced intensity (Higher reps, tempo work, or isometric variations).
* **CONDITIONING:** Low-intensity Steady State (SS) or mobility-focused finishers.

---

## **4. Progression Logic**
* **Linear Progression:** HIIT and SIT Conditioning levels increment by **+1** upon successful completion of a protocol (max level 7). There are no levels for SS conditioning (level always = 1 for SS).
* **State Reset:** After a "Complete" signal is received, the backend handles the state mutation before the next session can be generated.
