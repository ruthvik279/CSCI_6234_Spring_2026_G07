# Code Review Automation Assistant

This repository implements the project defined in the UML/design artifacts for the OOD project. It provides a starter full-stack architecture for:

- connecting GitHub repositories
- receiving pull request webhook events
- analyzing changed files for code quality issues
- generating review comments and quality metrics
- exposing dashboard and report endpoints
- managing configurable review rules

## Stack

- Backend: Python, FastAPI
- Frontend: React, Vite
- Storage: in-memory starter store for rapid development

## Project Structure

- `backend/` FastAPI API, analyzers, review workflow, and report logic
- `frontend/` React dashboard starter

## Core Domain Mapping

The code mirrors the UML domain closely:

- `Repository`
- `PullRequest`
- `FileChange`
- `Issue`
- `ReviewComment`
- `CodeReviewRule`
- `QualityMetrics`

## MVP Features

1. Connect a repository and define default review rules
2. Receive a pull request payload and analyze changed files
3. Produce issues, review comments, and quality metrics
4. View dashboard summaries and export simple reports

## Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Easy Startup On Windows

Use these scripts from the `Implementation` folder:

- `start-app.cmd` starts backend and frontend in separate terminal windows
- `run-backend.cmd` starts only the FastAPI backend on `http://127.0.0.1:8000`
- `run-frontend.cmd` starts only the Vite frontend on `http://127.0.0.1:5173`

The scripts also install missing local dependencies the first time you run them.

## Deployment

Recommended split for this repo:

- Frontend on Vercel with project root set to `Implementation/frontend`
- Backend on Render using the root-level `render.yaml`
- Or deploy both services together on Render using the same root-level `render.yaml`

### Files Used For Deployment

- `frontend/.env.example` documents the `VITE_API_BASE_URL` variable used by the React app
- `backend/.env.example` documents backend environment variables for webhook URL and CORS
- `../render.yaml` defines both Render services for a single Blueprint deployment
- `backend/Dockerfile` builds the FastAPI backend container
- `frontend/Dockerfile` builds the Vite frontend into an Nginx image
- `frontend/nginx.conf` serves the frontend and proxies `/api/*` to the backend in Docker
- `../docker-compose.yml` runs the full stack locally with one command

### Vercel Settings

Use these project settings in Vercel:

- Root Directory: `Implementation/frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variable: `VITE_API_BASE_URL=https://<your-render-service>.onrender.com`

This Vite frontend does not require a `vercel.json` file for the current setup.

### Render Settings

If you use the Blueprint from `render.yaml`, Render can create both the backend and the frontend from one repo. Set these values in Render:

- Backend `PUBLIC_WEBHOOK_URL=https://<your-render-backend>.onrender.com/webhooks/github`
- Backend `CORS_ORIGINS=https://<your-vercel-project>.vercel.app`
- Optional backend `CORS_ORIGIN_REGEX=https://.*\\.vercel\\.app` if you want Vercel preview deployments to work too
- Frontend `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`

You can also include local origins in `CORS_ORIGINS` as a comma-separated list when you want both deployed and local frontend access.

### Docker Usage

Run the full stack locally with Docker Compose from the repository root:

```bash
docker compose up --build
```

This starts:

- frontend on `http://localhost:3000`
- backend on `http://localhost:8000`

The frontend container is built with `VITE_API_BASE_URL=/api`, and Nginx forwards `/api/*` requests to the backend container.

Note for this workspace: `docker compose` can fail when run through the `C:\Users\nikhi\Box` junction path on Windows. The images and compose setup are valid, but Docker Compose may require running from the underlying non-junction path in this specific local environment.

### Recommended Deployment Paths

1. Simplest overall: deploy both services on Render from `render.yaml`
2. Mixed hosting: deploy frontend on Vercel and backend on Render
3. Docker-based backend on Render: use `backend/Dockerfile` if you prefer Render's Docker runtime instead of the native Python runtime

## Next Steps

- replace the in-memory store with a database
- integrate real GitHub webhook signature validation
- post review comments back to GitHub through the API
- add authentication and repository-level permissions
