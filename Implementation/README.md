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

## Next Steps

- replace the in-memory store with a database
- integrate real GitHub webhook signature validation
- post review comments back to GitHub through the API
- add authentication and repository-level permissions
