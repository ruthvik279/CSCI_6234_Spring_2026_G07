from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    name: str
    github_url: str
    access_token: str = Field(min_length=1)


class FileChangePayload(BaseModel):
    filename: str
    filepath: str
    additions: int = 0
    deletions: int = 0
    change_type: str = "modified"
    patch: str = ""


class PullRequestWebhookPayload(BaseModel):
    repository_id: str
    number: int
    title: str
    description: str = ""
    status: str = "open"
    files: List[FileChangePayload]


class RulePayload(BaseModel):
    name: str
    severity: str
    is_enabled: bool = True
    threshold: float | None = None


class RuleUpdateRequest(BaseModel):
    repository_id: str
    rules: List[RulePayload]


class RepositorySummary(BaseModel):
    repository_id: str
    name: str
    github_url: str
    owner: str
    repo_name: str


class RepositoryListResponse(BaseModel):
    repositories: List[RepositorySummary]


class GitHubPullRequestSummary(BaseModel):
    number: int
    title: str
    state: str
    author: str
    html_url: str


class GitHubPullRequestListResponse(BaseModel):
    repository_id: str
    pull_requests: List[GitHubPullRequestSummary]


class AnalysisHistoryEntry(BaseModel):
    pull_request_id: str
    number: int
    title: str
    status: str
    issue_count: int
    quality_score: float
    avg_complexity: float
    updated_date: datetime
    comment_count: int


class AnalysisHistoryResponse(BaseModel):
    repository_id: str
    history: List[AnalysisHistoryEntry]


class DashboardResponse(BaseModel):
    repository_count: int
    pull_request_count: int
    total_issue_count: int
    average_quality_score: float


class ReportResponse(BaseModel):
    generated_at: datetime
    repository_id: str
    pull_request_count: int
    total_issue_count: int
    average_quality_score: float
    issues_by_severity: dict[str, int]
