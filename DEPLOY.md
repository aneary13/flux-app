# Deployment Guide for Render.com

This guide explains how to deploy the FLUX backend to Render.com as a Python Web Service.

## Prerequisites

- A Render.com account
- A Supabase database (or other PostgreSQL database) with connection string
- Git repository access

## Render.com Configuration

### Service Settings

1. **Service Type**: Python Web Service
2. **Root Directory**: `backend`
3. **Python Version**: 3.13
4. **Build Command**: (Render will auto-detect from `requirements.txt`)
5. **Start Command**: `./start.sh` or `bash start.sh`

### Environment Variables

Set the following environment variable in Render's dashboard:

- **`DATABASE_URL`**: Your Supabase PostgreSQL connection string
  - Format: `postgresql+asyncpg://user:password@host:port/database`
  - Example: `postgresql+asyncpg://postgres:password@db.xxxxx.supabase.co:5432/postgres`

## Deployment Steps

1. **Connect Repository**
   - In Render dashboard, click "New" → "Web Service"
   - Connect your Git repository
   - Select the repository and branch

2. **Configure Service**
   - **Name**: Choose a name for your service (e.g., `flux-backend`)
   - **Root Directory**: Set to `backend`
   - **Environment**: Python 3
   - **Build Command**: Leave empty (auto-detected)
   - **Start Command**: `./start.sh`

3. **Set Environment Variables**
   - Go to the "Environment" tab
   - Add `DATABASE_URL` with your database connection string

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - The service will be available at `https://your-service-name.onrender.com`

## What Happens on Deploy

1. Render installs dependencies from `requirements.txt`
2. The `start.sh` script runs:
   - Executes `alembic upgrade head` to apply database migrations
   - Starts the FastAPI server using uvicorn on `0.0.0.0:$PORT`

## Health Check

After deployment, you can verify the service is running by visiting:

```
https://your-service-name.onrender.com/
```

This should return:
```json
{"status": "ok", "version": "flux-api-v1"}
```

## Troubleshooting

- **Migrations fail**: Ensure `DATABASE_URL` is correctly set and the database is accessible
- **Service won't start**: Check Render logs for errors in the start script
- **Port binding issues**: The script automatically uses Render's `$PORT` environment variable

## Notes

- The `requirements.txt` file is generated using `uv export --no-dev` to exclude development dependencies
- Database migrations run automatically on each deployment
- The service binds to `0.0.0.0` to accept connections from Render's load balancer
