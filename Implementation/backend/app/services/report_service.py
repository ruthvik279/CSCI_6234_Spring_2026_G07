from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.store.memory import store


class ReportService:
    def generate_report(self, repository_id: str, days: int | None = None) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None
        repository_pull_requests = [
            pr for pr in store.pull_requests.values() if pr.repository_id == repository_id
        ]
        if cutoff:
            repository_pull_requests = [
                pr for pr in repository_pull_requests if pr.updated_date.replace(tzinfo=timezone.utc) >= cutoff
            ]
        repository_pull_requests.sort(key=lambda pr: pr.updated_date, reverse=True)
        metrics = [
            metric
            for pull_request_id, metric in store.metrics.items()
            if store.pull_requests[pull_request_id].repository_id == repository_id
        ]
        if cutoff:
            metrics = [metric for metric in metrics if metric.timestamp.replace(tzinfo=timezone.utc) >= cutoff]
        comments = [
            comment
            for pull_request in repository_pull_requests
            for comment in store.comments.get(pull_request.pull_request_id, [])
        ]

        severities = Counter()
        for comment in comments:
            severity_match = re.match(r"^(HIGH|MEDIUM|LOW):", comment.body)
            severities[(severity_match.group(1).lower() if severity_match else "low")] += 1

        average_quality_score = (
            sum(metric.code_quality_score for metric in metrics) / len(metrics) if metrics else 0.0
        )
        average_issue_count = (
            sum(metric.total_issues_count for metric in metrics) / len(metrics) if metrics else 0.0
        )
        worst_metric = min(metrics, key=lambda metric: metric.code_quality_score, default=None)
        latest_pull_request = repository_pull_requests[0] if repository_pull_requests else None

        return {
            "generated_at": datetime.utcnow(),
            "repository_id": repository_id,
            "days": days,
            "pull_request_count": len(repository_pull_requests),
            "total_issue_count": sum(metric.total_issues_count for metric in metrics),
            "average_quality_score": round(average_quality_score, 2),
            "average_issue_count": round(average_issue_count, 2),
            "issues_by_severity": dict(severities),
            "latest_pull_request_number": latest_pull_request.number if latest_pull_request else None,
            "lowest_quality_score": worst_metric.code_quality_score if worst_metric else None,
        }
