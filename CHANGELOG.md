# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.3.0] - 2026-01-20

### Added
- **API Layer (Phase 3)**:
  - FastAPI application with RESTful endpoints
  - Dependency injection system for database sessions, engine instances, and user identification
  - Readiness check-in endpoint (`POST /api/v1/readiness/check-in`) with upsert logic
  - Exercise management endpoints (`GET /api/v1/exercises/`, `POST /api/v1/exercises/seed`)
  - Workout recommendation endpoint (`POST /api/v1/workouts/recommend`)
  - CORS middleware for frontend integration
  - Lifespan context manager for application startup/shutdown
  - Health check endpoint (`GET /`)
  - User ID extraction from `X-User-Id` header (ready for authentication upgrade)
  - LRU cache optimization for WorkoutEngine (YAML parsed once at startup)
- API documentation via Swagger UI and ReDoc
- Comprehensive error handling with appropriate HTTP status codes

### Changed
- Updated project structure to include `src/api/` directory with routes and dependencies
- Added API dependencies: `fastapi`, `uvicorn[standard]`
- Improved separation of concerns: Pydantic models for I/O, SQLModel for database persistence

---

## [0.2.0] - 2026-01-20

### Added
- **Database Layer (Phase 2)**:
  - SQLModel database models for persistence:
    - `Exercise` table (reference data for exercises)
    - `DailyReadiness` table (user readiness logs with composite unique constraint)
    - `WorkoutSession` table (workout session logs)
    - `WorkoutSet` table (granular set data with relationships)
  - Async database session management (`src/db/session.py`)
  - SQLModel relationships for easy data navigation
  - Alembic integration for database migrations with async support
  - Environment variable configuration via `.env` file
  - `.env.example` template for database connection strings
- Database migration infrastructure with async SQLModel support
- Support for PostgreSQL via asyncpg driver

### Changed
- Updated project structure to include `src/db/` directory
- Added database dependencies: `sqlmodel`, `alembic`, `asyncpg`, `python-dotenv`, `greenlet`

---

## [0.1.0] - 2026-01-19

### Added
- Initial project structure
- WorkoutEngine with state determination and session generation
- Pydantic models for configuration, input, and output
- Test suite for models and engine
- Configuration system with YAML-based program config
- Pull request template
- Changelog file

[Unreleased]: https://github.com/aneary13/flux-app/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/aneary13/flux-app/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/aneary13/flux-app/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/aneary13/flux-app/releases/tag/v0.1.0
