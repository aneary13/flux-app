"""API router collection."""

from fastapi import APIRouter

from src.api.routes import exercises, readiness, workouts

api_router = APIRouter()

api_router.include_router(readiness.router, prefix="/readiness", tags=["readiness"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
