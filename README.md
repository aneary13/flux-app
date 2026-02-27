# FLUX

**The Biological Training Engine**

FLUX is a premium, auto-regulated training application. Instead of relying on a fixed, rigid workout calendar, FLUX uses an agile periodization approach. It evaluates a user's daily biological readiness (pain and energy levels) alongside their historical "Pattern Freshness" to dynamically generate the exact training session their body needs today.

## 🏗 System Architecture

FLUX is built on a decoupled, three-pillar architecture. 

### 1. The Frontend: "The Thin Client"

* **Location:** [`/frontend`](./frontend/README.md)
* **Tech:** React Native (Expo), TypeScript, Zustand, NativeWind (Tailwind).
* **Role:** Delivers a premium "Biological Tech" UI/UX. It manages the active workout timer and session state locally, deferring all complex progression math to the backend.

### 2. The Backend: "The Brain"

* **Location:** [`/backend`](./backend/README.md)
* **Tech:** Python 3.13+, FastAPI, `uv`, Pydantic V2.
* **Role:** The decision engine. It reads the user's biological inputs, evaluates pattern freshness (e.g., real-time elapsed duration since the last Hinge session), and generates a fully structured, state-appropriate training session (Performance vs. Recovery). 

### 3. The Database: "The Source of Truth"

* **Location:** [`/supabase`](./supabase/README.md)
* **Tech:** PostgreSQL, Supabase CLI.
* **Role:** Stores the core YAML-derived training logic, the exercise catalog, user progression states, and workout history. It utilizes a hybrid relational-JSON schema to securely track highly variable conditioning data without polluting tables.

## 🚀 Quick Start Guide

To get the entire FLUX stack running on your local machine, follow this high-level order of operations. **For detailed instructions, refer to the README inside each specific directory.**

### Step 1: Boot the Database

1. Ensure Docker Desktop is running.
2. Navigate to the `/supabase` directory.
3. Run `supabase start` to spin up your local PostgreSQL instance and API Gateway.

### Step 2: Start the Engine (Backend)

1. Navigate to the `/backend` directory.
2. Install dependencies using `uv sync`.
3. Create a `.env` file pointing to your local Supabase URLs and Keys.
4. Seed the database with the core biological logic: `uv run scripts/seed_db.py`.
5. Start the FastAPI server: `uv run uvicorn main:app --reload`.

### Step 3: Launch the App (Frontend)

1. Navigate to the `/frontend` directory.
2. Install dependencies using `npm install`.
3. Create a `.env` file pointing to your backend API (`EXPO_PUBLIC_API_URL=http://localhost:8000` or your network IP).
4. Start the Expo bundler: `npx expo start`.
5. Press `a` to open the Android simulator, or scan the QR code with the Expo Go app on your physical device.

## 🌍 Production Infrastructure

* **Mobile App:** Built into a standalone `.apk` via **Expo Application Services (EAS)**.
* **API Server:** Deployed as a Web Service on **Render**. 
* **Database:** Hosted on **Supabase Cloud**, heavily utilizing Row Level Security (RLS) to isolate user state documents.
