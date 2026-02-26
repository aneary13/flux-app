# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Authentication Prep**: API and Database schema structured to support isolated user states, currently stubbed with `DUMMY_USER_ID`.

---

## [0.8.0] - 2026-02-26

### Added

- **Decoupled Architecture**: Transitioned the application to a 3-pillar system: React Native (Frontend), FastAPI (Backend), and Supabase (Database).
- **Hybrid Relational/JSON Schema**: Introduced a `metadata` JSONB column in the `workout_sets` Supabase table to capture sparse, protocol-specific conditioning data (e.g., `avg_watts`, `peak_hr`, `protocol_level`) without polluting standard strength columns.
- **Frontend State Management**: Implemented Zustand with dual stores: `useUserStore` for persistent biological state tracking and `useSessionStore` for highly dynamic active-workout lifecycle management.
- **Premium UI System**: Implemented the "Biological Tech" aesthetic using NativeWind (Sage Green `#8FA58A`, Earthy Sand `#D4A373`, Dusty Rose `#CD7B7B`).
- **Conditioning Progression Engine**: Added linear progression tracking for conditioning protocols (HIIT, SIT, SS). Completing a protocol automatically levels up the user in their isolated `state` document.
- **Modern Package Management**: Transitioned backend fully to `uv` (via `pyproject.toml` and `uv.lock`), including `uv export` workflows for Render deployments.
- **Supabase Seeding**: Created `scripts/seed_db.py` to seamlessly upsert YAML-derived "Brain" configs and exercise catalogs directly into the remote database.
- **Modular configuration**: Backend config split from a single `program_config.yaml` into five domain YAML files in `backend/config/`.
- **Red Day (Recovery) sessions**: When readiness state is RED, the engine automatically generates a dedicated recovery session with mobility flows, repair isometrics, and Zone 2 conditioning.

### Changed

- **Database ORM**: Completely removed `SQLModel` and `Alembic`. The backend now uses the official `supabase-py` client for all CRUD operations, leveraging PostgreSQL Row Level Security (RLS) instead of application-layer ORM models.
- **Engine Logic**: `WorkoutResolver` now pulls its rules ("The Brain") directly from the `user_configs` table in Supabase rather than local files, allowing for dynamic, per-user engine adjustments in the future.
- **Documentation**: Consolidated `DEPLOY.md` into highly specific, directory-level `README.md` files to adhere to the DRY principle.

### Removed

- `backend/alembic/` directory and all local SQLite/Alembic migration history.
- `DEPLOY.md` (Superseded by modular READMEs).

---

## [0.7.0] - 2026-02-10

### Added

- **Complete Workout (feedback loop)**:
  - `POST /api/v1/workouts` to log completed sessions with sets. Persists `WorkoutSession` and `WorkoutSet`; upserts `PatternInventory`.
  - Recommend flow builds training history from `PatternInventory`.
- **Database**: New schema via migrations: `PatternInventory` table; `WorkoutSession`/`WorkoutSet`. Fixed asyncpg timezone errors.
- **Pattern priority**: Config key `pattern_priority` (e.g. SQUAT, PUSH, HINGE, PULL) for Upper/Lower rotation tie-breaking.

### Changed

- Workout recommendation uses `PatternInventory` as the source of pattern history.

---

## [0.6.0] - 2026-01-27

### Added

- **Agile Training Logic v2.0 (Phase 6)**:
  - Pattern debt tracking defaults to 100 when never performed.
  - Session type selection: REST when energy < 5, else GYM or CONDITIONING.
  - Block-by-block session composition: PREP, POWER, STRENGTH, ACCESSORIES.
  - Configurable **PATELLAR_ISO**.
  - New config schema: `patterns`, `relationships` (PATTERN:TIER), `library`, `power_selection`, `session_structure`, `states`.

### Changed

- Replaced archetype/session-based selection with pattern-debt and library-based composition.
- Relationships format is now `PATTERN:TIER` (e.g. `PULL:ACCESSORY_HORIZONTAL`).

### Fixed

- SQLModel: removed `nullable=True` from `Field()` when using `sa_column`.

---

## [0.5.0] - 2026-01-21

### Added

- **Deployment Infrastructure (Phase 5)**:
  - Backend deployment configuration for Render.com.
  - Frontend environment variable support (`EXPO_PUBLIC_API_URL`).

### Fixed

- **Render Build Failures**: Updated `requirements.txt` generation command to use `--no-emit-project`.
- **Database Connection Errors**: Resolved `[Errno 8]` DNS errors by mandating Supabase Session Pooler URLs (Port 6543).

---

## [0.4.0] - 2026-01-20

### Added

- **Frontend Application (Phase 4)**:
  - React Native Expo application with TypeScript and Expo Router.
  - NativeWind v4 integration for Tailwind CSS styling.
  - TanStack Query (React Query) for data fetching.
  - User ID persistence using AsyncStorage.
  - Daily Readiness Check-In screen and Workout Plan display screen.

---

## [0.3.0] - 2026-01-20

### Added

- **API Layer (Phase 3)**:
  - FastAPI application with RESTful endpoints.
  - Readiness check-in endpoint and Exercise management endpoints.
  - CORS middleware for frontend integration.
  - API documentation via Swagger UI.

---

## [0.2.0] - 2026-01-20

### Added

- **Database Layer (Phase 2)**:
  - SQLModel database models for persistence.
  - Async database session management.
  - Alembic integration for database migrations.

---

## [0.1.0] - 2026-01-19

### Added

- Initial project structure.
- WorkoutEngine with state determination and session generation.
