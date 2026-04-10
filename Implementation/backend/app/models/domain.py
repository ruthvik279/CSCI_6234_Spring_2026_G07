from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Repository:
    repository_id: str
    name: str
    github_url: str
    webhook_url: str
    is_active: bool = True


@dataclass
class FileChange:
    file_change_id: str
    filename: str
    filepath: str
    additions: int
    deletions: int
    change_type: str
    patch: str = ""

    def parse_code(self) -> str:
        return self.patch


@dataclass
class PullRequest:
    pull_request_id: str
    repository_id: str
    number: int
    title: str
    description: str
    status: str
    created_date: datetime
    updated_date: datetime
    files: List[FileChange] = field(default_factory=list)


@dataclass
class Issue:
    issue_id: str
    issue_type: str
    line_number: int
    severity: str
    message: str
    suggestion: str
    detected_date: datetime
    file_path: str


@dataclass
class ReviewComment:
    comment_id: str
    pull_request_id: str
    body: str
    file_path: str
    line_number: int
    created_date: datetime


@dataclass
class CodeReviewRule:
    rule_id: str
    name: str
    severity: str
    is_enabled: bool = True
    threshold: float | None = None


@dataclass
class QualityMetrics:
    metrics_id: str
    pull_request_id: str
    timestamp: datetime
    total_issues_count: int
    code_quality_score: float
    avg_complexity: float
