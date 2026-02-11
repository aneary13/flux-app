# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.7.0] - 2026-02-10

### Added
- **Complete Workout (feedback loop)**:
  - `POST /api/v1/workouts` to log completed sessions with sets (exercise_name, weight_kg, reps, RPE). Persists `WorkoutSession` (UUID, started_at, completed_at, readiness_score, notes) and `WorkoutSet`; upserts `PatternInventory` so pattern debt resets for performed exercises.
  - Recommend flow now builds training history from `PatternInventory` (grouped by date) instead of session records.
  - Pydantic schemas `WorkoutSessionCreate`/`WorkoutSessionRead` and service `log_completed_session` in `src/services/workout.py`.
- **Database**: New/updated schema via migrations: `PatternInventory` table; `WorkoutSession`/`WorkoutSet` with UUID PKs and new fields. Second migration alters workout/pattern timestamps to TIMESTAMPTZ (timezone-aware) to fix asyncpg errors when frontend sends ISO 8601 with timezone.
- **Pattern priority**: Config key `pattern_priority` (e.g. SQUAT, PUSH, HINGE, PULL) and engine sort by (-debt, priority index) so tied main-pattern debts follow an Upper/Lower rotation.

### Changed
- Workout recommendation uses `PatternInventory` as the source of pattern history; completing a workout updates inventory and resets debt for those patterns.

---

## [0.6.0] - 2026-01-27

### Added
- **Agile Training Logic v2.0 (Phase 6)**:
  - Pattern debt tracking: days since last performance per pattern; defaults to 100 when never performed.
  - Session type selection (Level 1): REST when energy &lt; 5, else GYM or CONDITIONING based on gym vs conditioning debt.
  - Block-by-block session composition: PREP (PATELLAR_ISO + CORE), POWER (RFD), STRENGTH (main lift), ACCESSORIES from relationships.
  - Configurable **PATELLAR_ISO** in `program_config.yaml` so the first exercise (e.g. "SL Wall Sit") is configurable per state.
  - `session_structure` in config defining PREP, POWER, STRENGTH, ACCESSORIES components.
  - New config schema: `patterns`, `relationships` (PATTERN:TIER), `library` (including CORE tiers, RFD, PATELLAR_ISO), `power_selection`, `session_structure`, `states`.
  - Backward compatibility: SessionPlan computed fields `exercises`, `session_name`, `archetype` for existing frontend.
- Database: `WorkoutSession.impacted_patterns` (JSON) and `session_type`; migration for pattern tracking.
- API: Workout recommendation uses `impacted_patterns` from history (with `None`/empty handling).

### Changed
- Replaced archetype/session-based selection with pattern-debt and library-based composition.
- Removed `power_library`; RFD exercises live under `library.RFD` (HIGH/LOW/UPPER) with state selection via `power_selection`.
- Relationships format is now `PATTERN:TIER` (e.g. `PULL:ACCESSORY_HORIZONTAL`).
- RFD block uses all exercises for the selected type (not a single random choice).

### Fixed
- SQLModel: removed `nullable=True` from `Field()` when using `sa_column` to fix Alembic startup error.
- Test suite updated for v2.0 config and engine (pattern debt, skip logic, relationship logic, backward compat).

---

## [0.5.0] - 2026-01-21

### Added
- **Deployment Infrastructure (Phase 5)**:
  - Backend deployment configuration for Render.com.
  - Production start script (`backend/start.sh`) with automatic database migrations.
  - `DEPLOY.md` guide covering Render setup and Supabase connection specifics.
  - Frontend environment variable support (`EXPO_PUBLIC_API_URL`) for switching between Localhost and Production.

### Fixed
- **Render Build Failures**: Updated `requirements.txt` generation command to use `--no-emit-project`. This prevents local file paths from breaking cloud builds.
- **Database Connection Errors**: Resolved `[Errno 8]` DNS errors by mandating the use of Supabase Session Pooler URLs (Port 6543) for IPv4 compatibility on Render and local networks.
- **Frontend Networking**: Resolved physical device connection timeouts by adding documentation for Expo Tunnel mode (`--tunnel`).

### Changed
- Updated API Client in frontend to prioritize `EXPO_PUBLIC_API_URL` over platform defaults.
- Updated `README.md` with comprehensive troubleshooting steps for "Cold Starts" and networking issues.

---

## [0.4.0] - 2026-01-20

### Added
- **Frontend Application (Phase 4)**:
  - React Native Expo application with TypeScript and Expo Router.
  - NativeWind v4 integration for Tailwind CSS styling.
  - TanStack Query (React Query) for data fetching and caching.
  - Axios HTTP client with platform-aware base URL configuration.
  - User ID persistence using AsyncStorage and expo-crypto.
  - Automatic `X-User-Id` header injection via Axios interceptors.
  - Daily Readiness Check-In screen with interactive number selectors.
  - Workout Plan display screen with loading, success, and error states.
  - Reusable `NumberSelector` component with flex-wrap button layout.
  - Type-safe API client with TypeScript interfaces (`SessionPlan`, `ReadinessCheckInResponse`).
  - Platform detection for Android emulator (`10.0.2.2`) vs iOS simulator (`localhost`).
- Frontend project structure in `frontend/` directory.
- Comprehensive error handling for 404 (Rest Day) and other API errors.
- Modern UI with card-based layouts, rounded corners, and blue/green color scheme.

### Changed
- Updated project structure to include `frontend/` directory.
- Added frontend dependencies: `expo`, `expo-router`, `nativewind`, `@tanstack/react-query`, `axios`, `expo-crypto`, `@react-native-async-storage/async-storage`.

---

## [0.3.0] - 2026-01-20

### Added
- **API Layer (Phase 3)**:
  - FastAPI application with RESTful endpoints.
  - Dependency injection system for database sessions, engine instances, and user identification.
  - Readiness check-in endpoint (`POST /api/v1/readiness/check-in`) with upsert logic.
  - Exercise management endpoints (`GET /api/v1/exercises/`, `POST /api/v1/exercises/seed`).
  - Workout recommendation endpoint (`POST /api/v1/workouts/recommend`).
  - CORS middleware for frontend integration.
  - Lifespan context manager for application startup/shutdown.
  - Health check endpoint (`GET /`).
  - User ID extraction from `X-User-Id` header (ready for authentication upgrade).
  - LRU cache optimization for WorkoutEngine (YAML parsed once at startup).
- API documentation via Swagger UI and ReDoc.
- Comprehensive error handling with appropriate HTTP status codes.

### Changed
- Updated project structure to include `src/api/` directory with routes and dependencies.
- Added API dependencies: `fastapi`, `uvicorn[standard]`.
- Improved separation of concerns: Pydantic models for I/O, SQLModel for database persistence.

---

## [0.2.0] - 2026-01-20

### Added
- **Database Layer (Phase 2)**:
  - SQLModel database models for persistence:
    - `Exercise` table (reference data for exercises).
    - `DailyReadiness` table (user readiness logs with composite unique constraint).
    - `WorkoutSession` table (workout session logs).
    - `WorkoutSet` table (granular set data with relationships).
  - Async database session management (`src/db/session.py`).
  - SQLModel relationships for easy data navigation.
  - Alembic integration for database migrations with async support.
  - Environment variable configuration via `.env` file.
  - `.env.example` template for database connection strings.
- Database migration infrastructure with async SQLModel support.
- Support for PostgreSQL via asyncpg driver.

### Changed
- Updated project structure to include `src/db/` directory.
- Added database dependencies: `sqlmodel`, `alembic`, `asyncpg`, `python-dotenv`, `greenlet`.

---

## [0.1.0] - 2026-01-19

### Added
- Initial project structure.
- WorkoutEngine with state determination and session generation.
- Pydantic models for configuration, input, and output.
- Test suite for models and engine.
- Configuration system with YAML-based program config.
- Pull request template.
- Changelog file.

[Unreleased]: https://github.com/aneary13/flux-app/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/aneary13/flux-app/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/aneary13/flux-app/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/aneary13/flux-app/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/aneary13/flux-app/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/aneary13/flux-app/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/aneary13/flux-app/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/aneary13/flux-app/releases/tag/v0.1.0
