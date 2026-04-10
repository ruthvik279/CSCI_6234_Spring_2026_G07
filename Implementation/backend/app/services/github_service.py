from __future__ import annotations

from uuid import uuid4

from app.models.domain import CodeReviewRule, Repository
from app.store.memory import store


class GitHubService:
    def connect_repository(self, name: str, github_url: str, access_token: str) -> Repository:
        if not access_token.strip():
            raise ValueError("Access token is required.")

        repository = Repository(
            repository_id=str(uuid4()),
            name=name,
            github_url=github_url,
            webhook_url=f"{github_url}/webhooks/code-review-assistant",
        )
        store.repositories[repository.repository_id] = repository
        store.rules[repository.repository_id] = self.default_rules()
        return repository

    def default_rules(self) -> list[CodeReviewRule]:
        return [
            CodeReviewRule(rule_id=str(uuid4()), name="line-length", severity="low", threshold=100),
            CodeReviewRule(rule_id=str(uuid4()), name="complexity", severity="medium", threshold=15),
            CodeReviewRule(rule_id=str(uuid4()), name="secrets", severity="high"),
        ]
