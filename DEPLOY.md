# Deployment Guide for Render.com

This guide explains how to deploy the FLUX backend to Render.com as a Python Web Service.

## Prerequisites

- A Render.com account
- A Supabase database (or other PostgreSQL database) with connection string
- Git repository access

## 1. Prepare Dependencies (Critical Step)

Render requires a standard `requirements.txt` file. You must generate this file using `uv` with specific flags to ensure it works in a cloud environment.

Run this command in your `backend` directory:

```bash
cd backend
uv export --format requirements-txt --no-dev --no-emit-project --output-file requirements.txt
```

**Why these flags?**
- `--no-dev`: Excludes testing libraries (pytest) to keep the production build light.
- `--no-emit-project`: **Crucial.** Prevents `uv` from adding a reference to your local file system (e.g., `file:///Users/...`), which causes build failures on Render.

## 2. Render.com Configuration

### Service Settings

Create a new **Web Service** on Render and connect your GitHub repo. Use these settings:

1.  **Name**: `flux-app` (or similar)
2.  **Root Directory**: `backend` (If you miss this, the build will fail)
3.  **Runtime**: Python 3
4.  **Build Command**: `pip install -r requirements.txt`
5.  **Start Command**: `./start.sh`

### Environment Variables

Go to the **Environment** tab and add the following:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.13.7` | Or match your local version (e.g. `3.12.0`). Defaults to 3.7 if missing. |
| `DATABASE_URL` | `postgresql+asyncpg://...` | **See Supabase Note below** |

### ⚠️ Critical Note on Supabase Connections

Render (and many local networks) usually run on IPv4, while Supabase's direct connection is often IPv6. To avoid `[Errno 8] nodename nor servname provided` errors:

1.  Use the **Session Pooler** connection string (usually Port **6543**).
2.  Ensure the protocol is set to `postgresql+asyncpg://`.
3.  **URL Encode your password**: If your password contains special characters (like `@`), replace them with their hex code (e.g., `%40`).

## 3. What Happens on Deploy

1.  Render installs dependencies from the clean `requirements.txt`.
2.  The `start.sh` script runs:
    -   Executes `alembic upgrade head` to apply any pending database migrations.
    -   Starts the FastAPI server using `uvicorn` on `0.0.0.0:$PORT`.
3.  The server loads `config/program_config.yaml` at startup for workout logic (patterns, library, session structure). Ensure this file is committed to the repo.

## 4. Verification

After deployment, verify the service is running by visiting the URL (e.g., `https://flux-api.onrender.com`).

You should see:
```json
{"status": "ok", "version": "flux-api-v1"}
```

## 5. Known Limitations (Free Tier)

**The "Cold Start" Delay**
Render's free tier spins down services after 15 minutes of inactivity.
-   **Symptom**: When you open the FLUX mobile app after a break, you might get a "Network Error" or the spinner hangs for ~45 seconds.
-   **Solution**: This is normal. The first request wakes the server up. Simply reload the app or refresh the API URL in your browser, and it will work instantly.
