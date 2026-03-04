# FLUX App (Frontend)

This is the React Native (Expo) frontend for **FLUX**, a premium biological training engine.

The app acts as a "Thin Client"—it focuses on delivering a beautiful, offline-tolerant, and highly responsive user experience, while deferring complex progression math and session generation to the FastAPI backend.

## 🛠 Tech Stack

- **Framework:** React Native / Expo
- **Routing:** Expo Router (File-based routing)
- **State Management:** Zustand
- **Language:** TypeScript
- **Build System:** EAS (Expo Application Services)

## 📁 Project Structure

```text
frontend/
├── app/                     # Expo Router screens and layouts
│   ├── (session)/           # Active workout flow (check-in, active, complete)
│   ├── _layout.tsx          # Global app shell
│   └── index.tsx            # Home Dashboard (Biological State)
├── components/              # UI Components
│   ├── core/                # Design system primitives (Button, Card, Typography)
│   └── domain/              # Feature-specific components (ExerciseCard, ChecklistCard)
├── services/                # API communication
│   └── api.ts               # Fetch wrappers and FastAPI endpoint definitions
├── store/                   # Zustand State Management
│   ├── useSessionStore.ts   # Ephemeral state for active workouts and timers
│   └── useUserStore.ts      # Persistent-ish state for user biological readiness
├── theme/                   # Centralized Design System
│   └── index.ts             # Colors, spacing, radii, and readiness hex codes
└── types/                   # TypeScript interfaces
    └── api.d.ts             # Strict typings mapping to backend Pydantic models
```

## 🧠 State Management

The application relies on **Zustand** for state management, split into two distinct domains to prevent unnecessary re-renders:

1. `useUserStore`: Holds the user's current "Biological State" (the Pattern Readiness View Model and active Conditioning Levels). It is refreshed via `useFocusEffect` every time the user navigates back to the Home screen (`app/index.tsx`).
2. `useSessionStore`: Handles the highly dynamic state of an active workout. It logs completed sets, manages background block timers, and gathers notes. It is intentionally cleared (`clearSession()`) upon completing a workout.

## 🎨 Design System

The UI adheres to a "Premium Biological Tech" aesthetic. We strictly map the `status_text` strings returned by the backend View Model to our designated theme colors defined in `theme/index.ts`:

- **Sage Green** (`#8FA58A`): Fully Primed
- **Earthy Sand** (`#D4A373`): Priming / Recovering
- **Dusty Rose** (`#CD7B7B`): Fatigued / Engine Cooling

## 🚀 Usage & Development Instructions

### 1. Environment Setup

Create a `.env` file in the `frontend/` root directory. Do **not** commit this file.

```
# For local dev via tunneling or direct Render URL
EXPO_PUBLIC_API_URL=https://your-flux-backend.onrender.com
```

### 2. Running Locally

Install dependencies and start the Expo development server:

```bash
npm install
npx expo start
```

_Note: If testing on a physical device on a strict Wi-Fi network, run `npx expo start --tunnel` to bypass AP isolation._

### 3. Building for Production (Android APK)

The app is configured via `eas.json` to build a standalone Android `.apk` for direct installation. The production API URL is baked into the EAS preview profile.

To trigger a cloud build:

```bash
eas build -p android --profile preview
```

Once the build completes, scan the generated QR code with your Android device to download and install the app.
