# FLUX Backend API Specification

## **1. Core Overview**

FLUX is a stateless, rules-based fitness engine built with **FastAPI** and **Supabase**. It translates a user's biological "State" (Pain, Energy, and Pattern Fatigue) into a specific workout archetype and exercise plan.

## **2. Global State Management**

The user's progression is stored in a **State Document** within the `user_configs` table (`slug: "state"`). 

* **Last Trained Dates:** A dictionary mapping each movement pattern (SQUAT, PUSH, HINGE, PULL) to a UTC ISO-8601 timestamp representing when it was last anchored in a session. Un-trained patterns are set to `null`.
* **Conditioning Levels:** A linear progression tracker for metabolic protocols (HIIT, SIT).

## **3. API Endpoints**

### **A. System Initialization**

* **`GET /bootstrap`**
    * **Purpose:** Fetches global `configs` (the logic rules) and the full `exercises` catalog.
    * **Client Action:** Cache locally to power the UI without constant re-fetching.
* **`GET /user/state`**
    * **Purpose:** Retrieves the current State Document formatted as a View Model so the client performs no datetime math.
    * **Output:** 
        ```json
        {
          "patterns": {
            "SQUAT": {
              "last_trained_datetime": "2026-02-27T11:25:49.136581+00:00",
              "days_since": 0,
              "status_text": "Fatigued"
            },
            "PUSH": {
              "last_trained_datetime": null,
              "days_since": null,
              "status_text": "Fully Primed"
            }
          },
          "conditioning_levels": {
            "HIIT": 2,
            "SIT": 1
          }
        }
        ```

### **B. The Generation Loop**

* **`POST /sessions/generate`**
    * **Input (JSON):**
        ```json
        {
          "knee_pain": 2,
          "energy": 8,
          "last_trained": {
            "SQUAT": "2026-02-27T11:25:49.136581+00:00",
            "PUSH": null,
            "HINGE": null,
            "PULL": null
          },
          "conditioning_levels": {
            "HIIT": 2,
            "SIT": 1
          }
        }
        ```
    * **Logic:** 
        1. **State Check:** Pain > 3 OR Energy < 4 results in a `RECOVERY` Archetype. Otherwise, the session is `PERFORMANCE`.
        2. **Calculation & Tie-Breaking:** The backend calculates the time elapsed since each `last_trained` timestamp. `null` is treated as infinite elapsed time. If multiple patterns have equal elapsed time, the engine strictly prioritizes using the order defined in `logic.yaml` (`pattern_priority`).
    * **Output:** A full session plan containing `metadata` (Archetype, Anchor Pattern) and `blocks` (PREP, POWER, MAIN, ACCESSORY, CONDITIONING).

### **C. Session Execution**

* **`POST /sessions/start`**
    * **Input:** `{"readiness": {"knee_pain": int, "energy": int}}`
    * **Output:** `{"session_id": "uuid"}`
* **`POST /sessions/{session_id}/sets`**
    * **Purpose:** Atomic logging of weight, reps, and RPE for each individual set.
* **`POST /sessions/{session_id}/complete`**
    * **Input:** 
        ```json
        {
          "anchor_pattern": "SQUAT",
          "completed_conditioning_protocol": "HIIT",
          "exercise_notes": {},
          "summary_notes": ""
        }
        ```
    * **Backend Action:** Automatically stamps the current UTC datetime onto the `anchor_pattern` in the user's state document, and levels up the specifically completed conditioning protocol by 1.

## **4. The "Thin Client" Principle**

The mobile app is a presentation layer. It must never calculate which exercise comes next, determine if a user "passed" a level, decide the session archetype, or calculate days elapsed between dates. It simply sends the current biological state to the backend and renders the resulting JSON workout plan or View Model.
