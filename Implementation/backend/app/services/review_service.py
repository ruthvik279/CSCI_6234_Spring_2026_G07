from __future__ import annotations

from collections import Counter
from datetime import datetime
from uuid import uuid4

from app.models.domain import FileChange, PullRequest, QualityMetrics, ReviewComment
from app.schemas.api import PullRequestWebhookPayload
from app.services.analyzers.complexity import ComplexityAnalyzer
from app.services.analyzers.security import SecurityAnalyzer
from app.services.analyzers.style import StyleAnalyzer
from app.store.memory import store


class ReviewService:
    def __init__(self) -> None:
        self.analyzers = [
            StyleAnalyzer(),
            ComplexityAnalyzer(),
            SecurityAnalyzer(),
        ]

    def process_pull_request(self, payload: PullRequestWebhookPayload) -> dict:
        files = [
            FileChange(
                file_change_id=str(uuid4()),
                filename=file.filename,
                filepath=file.filepath,
                additions=file.additions,
                deletions=file.deletions,
                change_type=file.change_type,
                patch=file.patch,
            )
            for file in payload.files
        ]
        return self._process_files(
            repository_id=payload.repository_id,
            number=payload.number,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            files=files,
        )

    def process_github_pull_request(self, repository_id: str, github_pull_request: dict) -> dict:
        files = [
            FileChange(
                file_change_id=str(uuid4()),
                filename=file["filename"],
                filepath=file["filepath"],
                additions=file["additions"],
                deletions=file["deletions"],
                change_type=file["change_type"],
                patch=file["patch"],
            )
            for file in github_pull_request["files"]
        ]
        return self._process_files(
            repository_id=repository_id,
            number=github_pull_request["number"],
            title=github_pull_request["title"],
            description=github_pull_request["description"],
            status=github_pull_request["status"],
            files=files,
        )

    def _process_files(
        self,
        *,
        repository_id: str,
        number: int,
        title: str,
        description: str,
        status: str,
        files: list[FileChange],
    ) -> dict:
        pull_request = PullRequest(
            pull_request_id=str(uuid4()),
            repository_id=repository_id,
            number=number,
            title=title,
            description=description,
            status=status,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow(),
            files=files,
        )
        store.pull_requests[pull_request.pull_request_id] = pull_request

        issues = []
        for file_change in pull_request.files:
            for analyzer in self.analyzers:
                issues.extend(analyzer.analyze(file_change))

        comments = [
            ReviewComment(
                comment_id=str(uuid4()),
                pull_request_id=pull_request.pull_request_id,
                body=f"{issue.severity.upper()}: {issue.message} Suggestion: {issue.suggestion}",
                file_path=issue.file_path,
                line_number=issue.line_number,
                created_date=datetime.utcnow(),
            )
            for issue in issues
        ]
        store.comments[pull_request.pull_request_id] = comments

        avg_complexity = self._estimate_average_complexity(pull_request.files)
        quality_score = max(0.0, 100.0 - len(issues) * 7.5 - avg_complexity * 0.5)
        metrics = QualityMetrics(
            metrics_id=str(uuid4()),
            pull_request_id=pull_request.pull_request_id,
            timestamp=datetime.utcnow(),
            total_issues_count=len(issues),
            code_quality_score=round(quality_score, 2),
            avg_complexity=round(avg_complexity, 2),
        )
        store.metrics[pull_request.pull_request_id] = metrics

        return {
            "pull_request_id": pull_request.pull_request_id,
            "issues_found": len(issues),
            "issues_by_severity": dict(Counter(issue.severity for issue in issues)),
            "comments": comments,
            "metrics": metrics,
        }

    def _estimate_average_complexity(self, files: list[FileChange]) -> float:
        if not files:
            return 0.0
        scores = []
        for file_change in files:
            score = sum(
                1
                for line in file_change.parse_code().splitlines()
                if any(term in line for term in ("if ", "for ", "while ", "case ", "elif "))
            )
            scores.append(score)
        return sum(scores) / len(scores)
