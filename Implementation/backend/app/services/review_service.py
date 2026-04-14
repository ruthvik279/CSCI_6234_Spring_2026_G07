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
        self.analyzer_map = {
            "line-length": StyleAnalyzer(),
            "complexity": ComplexityAnalyzer(),
            "secrets": SecurityAnalyzer(),
        }
        self.severity_penalties = {
            "low": 3.0,
            "medium": 8.0,
            "high": 20.0,
        }

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
        existing_pull_request = self._find_existing_pull_request(repository_id, number)
        created_date = existing_pull_request.created_date if existing_pull_request else datetime.utcnow()
        pull_request_id = existing_pull_request.pull_request_id if existing_pull_request else str(uuid4())
        pull_request = PullRequest(
            pull_request_id=pull_request_id,
            repository_id=repository_id,
            number=number,
            title=title,
            description=description,
            status=status,
            created_date=created_date,
            updated_date=datetime.utcnow(),
            files=files,
        )
        store.pull_requests[pull_request.pull_request_id] = pull_request

        issues = []
        rules_by_name = {
            rule.name: {
                "severity": rule.severity,
                "threshold": rule.threshold,
                "enabled": rule.is_enabled,
            }
            for rule in store.rules.get(repository_id, [])
        }
        for file_change in pull_request.files:
            for rule_name, analyzer in self.analyzer_map.items():
                rule_config = rules_by_name.get(
                    rule_name,
                    {"severity": analyzer.severity, "threshold": None, "enabled": True},
                )
                if not rule_config.get("enabled", True):
                    continue
                issues.extend(analyzer.analyze(file_change, rule_config))

        comments = [
            ReviewComment(
                comment_id=str(uuid4()),
                pull_request_id=pull_request.pull_request_id,
                body=issue.format(),
                file_path=issue.file_path,
                line_number=issue.line_number,
                created_date=datetime.utcnow(),
            )
            for issue in issues
        ]
        store.comments[pull_request.pull_request_id] = comments

        avg_complexity = self._estimate_average_complexity(pull_request.files)
        issue_penalty = sum(
            self.severity_penalties.get(issue.severity.lower(), 5.0) for issue in issues
        )
        issue_density_penalty = min(len(issues) * 1.5, 12.0)
        quality_score = max(0.0, 100.0 - issue_penalty - issue_density_penalty - avg_complexity * 0.75)
        metrics = QualityMetrics(
            metrics_id=str(uuid4()),
            pull_request_id=pull_request.pull_request_id,
            timestamp=datetime.utcnow(),
            total_issues_count=len(issues),
            code_quality_score=round(quality_score, 2),
            avg_complexity=round(avg_complexity, 2),
        )
        metrics.store()

        return {
            "pull_request_id": pull_request.pull_request_id,
            "pull_request_number": pull_request.number,
            "pull_request_title": pull_request.title,
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
            score = 1 + sum(
                1
                for _, line in file_change.parsed_lines()
                if any(term in line.lower() for term in ("if ", "for ", "while ", "case ", "elif ", "switch "))
            )
            scores.append(score)
        return sum(scores) / len(scores)

    def _find_existing_pull_request(self, repository_id: str, number: int) -> PullRequest | None:
        for pull_request in store.pull_requests.values():
            if pull_request.repository_id == repository_id and pull_request.number == number:
                return pull_request
        return None
