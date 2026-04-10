from __future__ import annotations

from collections import Counter
from datetime import datetime

from app.store.memory import store


class ReportService:
    def generate_report(self, repository_id: str) -> dict:
        repository_pull_requests = [
            pr for pr in store.pull_requests.values() if pr.repository_id == repository_id
        ]
        metrics = [
            metric
            for pull_request_id, metric in store.metrics.items()
            if store.pull_requests[pull_request_id].repository_id == repository_id
        ]
        comments = [
            comment
            for pull_request in repository_pull_requests
            for comment in store.comments.get(pull_request.pull_request_id, [])
        ]

        severities = Counter()
        for comment in comments:
            if comment.body.startswith("HIGH:"):
                severities["high"] += 1
            elif comment.body.startswith("MEDIUM:"):
                severities["medium"] += 1
            else:
                severities["low"] += 1

        average_quality_score = (
            sum(metric.code_quality_score for metric in metrics) / len(metrics) if metrics else 0.0
        )

        return {
            "generated_at": datetime.utcnow(),
            "repository_id": repository_id,
            "pull_request_count": len(repository_pull_requests),
            "total_issue_count": sum(metric.total_issues_count for metric in metrics),
            "average_quality_score": round(average_quality_score, 2),
            "issues_by_severity": dict(severities),
        }
