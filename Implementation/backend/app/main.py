from __future__ import annotations

from io import StringIO

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.models.domain import CodeReviewRule
from app.schemas.api import (
    AnalysisHistoryResponse,
    DashboardResponse,
    GitHubPullRequestListResponse,
    PullRequestWebhookPayload,
    ReportResponse,
    RepositoryCreate,
    RepositoryListResponse,
    RuleUpdateRequest,
)
from app.services.github_service import GitHubService
from app.services.report_service import ReportService
from app.services.review_service import ReviewService
from app.store.memory import store

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

github_service = GitHubService()
review_service = ReviewService()
report_service = ReportService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/repositories", response_model=RepositoryListResponse)
def list_repositories() -> RepositoryListResponse:
    return RepositoryListResponse(
        repositories=[
            {
                "repository_id": repository.repository_id,
                "name": repository.name,
                "github_url": repository.github_url,
                "owner": repository.owner,
                "repo_name": repository.repo_name,
            }
            for repository in store.repositories.values()
        ]
    )


@app.post("/repositories")
def connect_repository(request: RepositoryCreate) -> dict:
    try:
        repository = github_service.connect_repository(
            name=request.name,
            github_url=request.github_url,
            access_token=request.access_token,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "repository_id": repository.repository_id,
        "name": repository.name,
        "github_url": repository.github_url,
        "webhook_url": repository.webhook_url,
        "owner": repository.owner,
        "repo_name": repository.repo_name,
        "rules": store.rules[repository.repository_id],
    }


@app.get("/repositories/{repository_id}")
def get_repository(repository_id: str) -> dict:
    repository = store.repositories.get(repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return {
        "repository_id": repository.repository_id,
        "name": repository.name,
        "github_url": repository.github_url,
        "owner": repository.owner,
        "repo_name": repository.repo_name,
        "webhook_url": repository.webhook_url,
        "rules": store.rules[repository_id],
    }


@app.get("/repositories/{repository_id}/pull-requests", response_model=GitHubPullRequestListResponse)
def list_pull_requests(repository_id: str) -> GitHubPullRequestListResponse:
    if repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")
    try:
        pull_requests = github_service.list_pull_requests(repository_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return GitHubPullRequestListResponse(
        repository_id=repository_id,
        pull_requests=pull_requests,
    )


@app.get("/repositories/{repository_id}/rules")
def get_rules(repository_id: str) -> dict:
    if repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return {"repository_id": repository_id, "rules": store.rules[repository_id]}


@app.get("/repositories/{repository_id}/history", response_model=AnalysisHistoryResponse)
def get_analysis_history(repository_id: str) -> AnalysisHistoryResponse:
    if repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")

    history = []
    for pull_request in store.pull_requests.values():
        if pull_request.repository_id != repository_id:
            continue
        metrics = store.metrics.get(pull_request.pull_request_id)
        comments = store.comments.get(pull_request.pull_request_id, [])
        history.append(
            {
                "pull_request_id": pull_request.pull_request_id,
                "number": pull_request.number,
                "title": pull_request.title,
                "status": pull_request.status,
                "issue_count": metrics.total_issues_count if metrics else 0,
                "quality_score": metrics.code_quality_score if metrics else 0.0,
                "avg_complexity": metrics.avg_complexity if metrics else 0.0,
                "updated_date": pull_request.updated_date,
                "comment_count": len(comments),
            }
        )

    history.sort(key=lambda item: item["updated_date"], reverse=True)
    return AnalysisHistoryResponse(repository_id=repository_id, history=history)


@app.post("/repositories/{repository_id}/pull-requests/{pull_request_number}/analyze")
def analyze_github_pull_request(repository_id: str, pull_request_number: int) -> dict:
    if repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")
    try:
        pull_request = github_service.fetch_pull_request_details(repository_id, pull_request_number)
        if not pull_request["files"]:
            raise HTTPException(
                status_code=400,
                detail="GitHub did not return any text patches for this pull request.",
            )
        return review_service.process_github_pull_request(repository_id, pull_request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/rules")
def configure_rules(request: RuleUpdateRequest) -> dict:
    if request.repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")

    existing = store.rules[request.repository_id]
    updated_rules = []
    for index, rule in enumerate(request.rules):
        rule_id = existing[index].rule_id if index < len(existing) else f"rule-{index + 1}"
        updated_rules.append(
            CodeReviewRule(
                rule_id=rule_id,
                name=rule.name,
                severity=rule.severity,
                is_enabled=rule.is_enabled,
                threshold=rule.threshold,
            )
        )
    store.rules[request.repository_id] = updated_rules
    return {"repository_id": request.repository_id, "rules": updated_rules}


@app.post("/webhooks/pull-request")
def submit_pull_request(payload: PullRequestWebhookPayload) -> dict:
    if payload.repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return review_service.process_pull_request(payload)


@app.get("/dashboard", response_model=DashboardResponse)
def view_dashboard() -> DashboardResponse:
    metrics = list(store.metrics.values())
    average_quality_score = (
        sum(metric.code_quality_score for metric in metrics) / len(metrics) if metrics else 0.0
    )
    return DashboardResponse(
        repository_count=len(store.repositories),
        pull_request_count=len(store.pull_requests),
        total_issue_count=sum(metric.total_issues_count for metric in metrics),
        average_quality_score=round(average_quality_score, 2),
    )


@app.get("/reports/{repository_id}", response_model=ReportResponse)
def generate_report(repository_id: str) -> ReportResponse:
    if repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return ReportResponse(**report_service.generate_report(repository_id))


@app.get("/reports/{repository_id}/download")
def download_report(repository_id: str) -> Response:
    repository = store.repositories.get(repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found.")

    report = report_service.generate_report(repository_id)
    csv_buffer = StringIO()
    csv_buffer.write("field,value\n")
    csv_buffer.write(f"repository,{repository.owner}/{repository.repo_name}\n")
    csv_buffer.write(f"generated_at,{report['generated_at'].isoformat()}\n")
    csv_buffer.write(f"pull_request_count,{report['pull_request_count']}\n")
    csv_buffer.write(f"total_issue_count,{report['total_issue_count']}\n")
    csv_buffer.write(f"average_quality_score,{report['average_quality_score']}\n")
    for severity, count in report["issues_by_severity"].items():
        csv_buffer.write(f"issues_{severity},{count}\n")

    filename = f"{repository.repo_name or repository.name}-report.csv"
    return Response(
        content=csv_buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
