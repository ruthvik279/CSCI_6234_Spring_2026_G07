from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Repository:
    repository_id: str
    name: str
    github_url: str
    webhook_url: str
    webhook_secret: str = ""
    owner: str = ""
    repo_name: str = ""
    access_token: str = ""
    is_active: bool = True

    @property
    def id(self) -> str:
        return self.repository_id

    @property
    def githubUrl(self) -> str:
        return self.github_url

    def connect(self) -> bool:
        self.is_active = True
        return self.is_active

    def disconnect(self) -> bool:
        self.is_active = False
        return self.is_active


@dataclass
class FileChange:
    file_change_id: str
    filename: str
    filepath: str
    additions: int
    deletions: int
    change_type: str
    patch: str = ""

    def parseCode(self) -> str:
        return self.parse_code()

    def parse_code(self) -> str:
        return "\n".join(line for _, line in self.parsed_lines())

    def parsed_lines(self) -> list[tuple[int, str]]:
        if not self.patch:
            return []

        parsed: list[tuple[int, str]] = []
        current_line_number: int | None = None
        hunk_pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        for raw_line in self.patch.splitlines():
            hunk_match = hunk_pattern.match(raw_line)
            if hunk_match:
                current_line_number = int(hunk_match.group(1))
                continue

            if current_line_number is None:
                continue

            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                parsed.append((current_line_number, raw_line[1:]))
                current_line_number += 1
                continue

            if raw_line.startswith(" ") or raw_line == "":
                parsed.append((current_line_number, raw_line[1:] if raw_line.startswith(" ") else raw_line))
                current_line_number += 1
                continue

            if raw_line.startswith("-") and not raw_line.startswith("---"):
                continue

        if parsed:
            return parsed

        return [(index, line) for index, line in enumerate(self.patch.splitlines(), start=1)]


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

    @property
    def id(self) -> str:
        return self.pull_request_id

    @property
    def filesChanged(self) -> List[FileChange]:
        return self.files

    def fetchChanges(self) -> List[FileChange]:
        return self.files

    def getReviewStatus(self) -> str:
        return self.status


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

    @property
    def lineNumber(self) -> int:
        return self.line_number

    def format(self) -> str:
        return f"{self.severity.upper()}: {self.message} Suggestion: {self.suggestion}"


@dataclass
class ReviewComment:
    comment_id: str
    pull_request_id: str
    body: str
    file_path: str
    line_number: int
    created_date: datetime

    @property
    def id(self) -> str:
        return self.comment_id

    @property
    def path(self) -> str:
        return self.file_path

    @property
    def position(self) -> int:
        return self.line_number

    def post(self) -> dict:
        return {
            "id": self.comment_id,
            "body": self.body,
            "path": self.file_path,
            "position": self.line_number,
        }


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

    @property
    def avgComplexity(self) -> float:
        return self.avg_complexity

    @property
    def issueCount(self) -> int:
        return self.total_issues_count

    def calculate(self) -> float:
        return self.code_quality_score

    def store(self) -> "QualityMetrics":
        from app.store.memory import store

        store.metrics[self.pull_request_id] = self
        return self
