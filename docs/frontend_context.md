# FLUX Frontend Context & UI Blueprint

## **1. Visual Identity & Design System**
The aesthetic is "Premium Biological Tech"—muted, organic, and high-end.

### **Color Palette**
* **Background:** `#F6F5F2` (Warm off-white)
* **Surface/Cards:** `#FFFFFF` (Pure white)
* **Primary Text:** `#222222` (Soft charcoal)
* **Muted Text:** `#8E8E93` (Medium grey)
* **Biological States (Muted/Organic):**
    * **GREEN:** `#8FA58A` (Sage)
    * **ORANGE:** `#D4A373` (Earthy sand)
    * **RED:** `#CD7B7B` (Dusty rose)
* **Accents:** `#2A2A2A` (Dark charcoal for primary actions)

### **Geometry & Spacing**
* **Border Radii:** Large and soft. Cards use `16px` to `20px`. Buttons use `24px`. Interactive "pills" use a full pill shape (`999px`).
* **Padding:** Generous internal breathing room (standard `20px` to `24px` for card content).
* **Elevation:** Avoid heavy shadows. Use subtle `4px` vertical offsets with very low opacity (`0.03`) to lift cards off the background.

---

## **2. The User Journey (State Machine)**
The app follows a linear, focused path. Navigation should feel like a guided process rather than a free-roaming exploration.

0. **Login:** Where users login or create an account. Can be left for future work, currently defaulting to a test UUID for authentication.
1.  **Home/Dashboard:** Displays the user's current "Pattern Debts" and readiness to start. In time, this screen will have multiple tabs (e.g Home, Settings, Progress, History, etc.)
2.  **Check-In (Biological Input):** A dedicated screen for "Knee Pain" and "Energy" sliders (Scale 1-10).
3.  **Today's Plan (Preview):** A vertical stack of workout "Blocks" (PREP, POWER, STRENGTH, etc.), with the exercises for each contained within the block.
4.  **Active Session (The Work):** A block-by-block execution view. Users log sets as they go.
5.  **Session Complete:** A celebratory summary of blocks and exercise sets completed, time, total sets, and exercise volume.

---

## **3. Intelligent UI Logic (Metadata Rendering)**
The UI must adapt dynamically based on the metadata attached to each exercise in the JSON response.

### **Unilateral vs. Bilateral**
* **If `is_unilateral == True`:** The input row must explicitly label reps as "per side" or provide a distinct UI indicator to ensure the user performs the work on both limbs.
* **If `is_unilateral == False`:** Standard bilateral display.

### **Tracking Units**
Exercise inputs must transform based on the `tracking_unit`:
* **REPS:** Display a numeric input for repetitions ("reps" or "reps / side").
* **SECONDS:** Display a duration input ("secs" or "secs / side").
* **DISTANCE:** Display an input for meters/kilometers ("metres").
* **WEIGHT:** Always accompany the primary tracking unit with a "kg" input field.

### **State-Based Styling**
The "Biological State" (Green/Orange/Red) returned by the backend should color the header tags, progress bars, and "Pill" components throughout the entire session to remind the user of their current training archetype (Performance vs. Recovery).

---

## **4. Technical Constraints**
* **Thin Client:** The frontend performs NO biological calculations. If a value needs to be rounded or a progression level determined, it must come from the backend.
* **Navigation:** Use `expo-router` for file-based routing.
* **State Management:** Use `Zustand` for global app state (storing the current session and user state).
* **Icons:** Use `Ionicons` (Expo Vector Icons) for all UI iconography.
