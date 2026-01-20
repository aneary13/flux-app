"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.main import api_router
from src.api.deps import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown.

    On startup: Initialize database connection and load WorkoutEngine.
    On shutdown: Clean up resources.
    """
    # Startup: Initialize engine (this will parse YAML and cache it)
    # This ensures the database connection is ready and config is loaded
    _ = get_engine()
    yield
    # Shutdown: Clean up if needed (currently no cleanup required)


app = FastAPI(
    title="FLUX API",
    version="1.0.0",
    description="FLUX - Flexible Training Logic Engine API",
    lifespan=lifespan,
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health check.

    Returns:
        Dictionary with status and version
    """
    return {"status": "ok", "version": "flux-api-v1"}
