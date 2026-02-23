# FLUX Backend API Specification (V1.0)

## **1. Core Overview**
FLUX is a stateless, rules-based fitness engine built with **FastAPI** and **Supabase**. It translates a user's biological "State" (Pain, Energy, and Pattern Debt) into a specific workout Archetype and exercise plan.

---

## **2. Global State Management**
The user's progression is stored in a **State Document** within the `user_configs` table (`slug: "state"`). 
* **Pattern Debts:** A counter that tracks how many sessions have passed since a specific movement pattern (SQUAT, PUSH, HINGE, PULL) was last trained.
* **Conditioning Levels:** A linear progression tracker for metabolic protocols (HIIT, SIT, SS).

---

## **3. API Endpoints**

### **A. System Initialization**
* **`GET /bootstrap`**
    * **Purpose:** Fetches global `configs` (the logic rules) and the full `exercises` catalog.
    * **Client Action:** Cache locally to power the UI without constant re-fetching.
* **`GET /user/state`**
    * **Purpose:** Retrieves the current State Document.
    * **Output:** `{"pattern_debts": {...}, "conditioning_levels": {...}}`

### **B. The Generation Loop**
* **`POST /sessions/generate`**
    * **Input (JSON):**
        ```json
        {
          "knee_pain": 2,
          "energy": 8,
          "pattern_debts": {"SQUAT": 0, "PUSH": 1, "HINGE": 0, "PULL": 0},
          "conditioning_levels": {"HIIT": 1, "SIT": 1, "SS": 1}
        }
        ```
    * **Logic:** 1. **State Check:** Pain > 3 OR Energy < 4 results in a `RECOVERY` Archetype. Otherwise, the session is `PERFORMANCE`.
        2. **Tie-Breaking:** If multiple patterns have equal debt, the engine prioritizes in order: SQUAT > HINGE > PUSH > PULL.
    * **Output:** A full session plan containing `metadata` (Archetype, Anchor Pattern) and `blocks` (PREP, POWER, MAIN, ACCESSORY, CONDITIONING).

### **C. Session Execution**
* **`POST /sessions/start`**
    * **Input:** `{"readiness": {"knee_pain": int, "energy": int}}`
    * **Output:** `{"session_id": "uuid"}`
* **`POST /sessions/{session_id}/sets`**
    * **Purpose:** Atomic logging of weight, reps, and RPE for each individual set.
* **`POST /sessions/{session_id}/complete`**
    * **Input:** ```json
        {
          "anchor_pattern": "SQUAT",
          "completed_conditioning_protocol": "HIIT",
          "exercise_notes": {},
          "summary_notes": ""
        }
        ```
    * **Backend Action:** Automatically resets the debt for the `anchor_pattern` to 0, increments all other pattern debts by 1, and levels up the specifically completed conditioning protocol by 1.

---

## **4. The "Thin Client" Principle**
The mobile app is a presentation layer. It must never calculate which exercise comes next, determine if a user "passed" a level, or decide the session archetype. It simply sends the current biological state to the backend and renders the resulting JSON workout plan.
