#!/bin/bash
set -e  # Exit on any error

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI server
# Use PORT environment variable (default to 10000 if not set)
PORT=${PORT:-10000}
echo "Starting server on 0.0.0.0:${PORT}..."
uvicorn src.main:app --host 0.0.0.0 --port "${PORT}"
