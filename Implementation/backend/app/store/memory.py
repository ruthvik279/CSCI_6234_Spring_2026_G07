from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

from app.models.domain import CodeReviewRule, PullRequest, QualityMetrics, Repository, ReviewComment


class InMemoryStore:
    def __init__(self) -> None:
        self.repositories: dict[str, Repository] = {}
        self.pull_requests: dict[str, PullRequest] = {}
        self.rules: dict[str, list[CodeReviewRule]] = defaultdict(list)
        self.comments: dict[str, list[ReviewComment]] = defaultdict(list)
        self.metrics: dict[str, QualityMetrics] = {}

    def snapshot(self) -> dict:
        return {
            "repositories": [asdict(item) for item in self.repositories.values()],
            "pull_requests": [asdict(item) for item in self.pull_requests.values()],
            "metrics": [asdict(item) for item in self.metrics.values()],
        }


store = InMemoryStore()
