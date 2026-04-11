from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from app.models.domain import CodeReviewRule, Repository
from app.store.memory import store


class GitHubService:
    def connect_repository(self, name: str, github_url: str, access_token: str) -> Repository:
        if not access_token.strip():
            raise ValueError("Access token is required.")

        owner, repo_name = self.parse_github_url(github_url)
        repo_data = self._request_json(
            f"https://api.github.com/repos/{owner}/{repo_name}",
            access_token,
        )

        repository = Repository(
            repository_id=str(uuid4()),
            name=name or repo_data["name"],
            github_url=github_url,
            webhook_url=f"{github_url}/webhooks/code-review-assistant",
            owner=owner,
            repo_name=repo_name,
            access_token=access_token,
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

    def list_pull_requests(self, repository_id: str) -> list[dict]:
        repository = store.repositories[repository_id]
        pull_requests = self._request_json(
            f"https://api.github.com/repos/{repository.owner}/{repository.repo_name}/pulls?state=open",
            repository.access_token,
        )
        return [
            {
                "number": pull_request["number"],
                "title": pull_request["title"],
                "state": pull_request["state"],
                "author": (pull_request.get("user") or {}).get("login", "unknown"),
                "html_url": pull_request["html_url"],
            }
            for pull_request in pull_requests
        ]

    def fetch_pull_request_details(self, repository_id: str, pull_request_number: int) -> dict:
        repository = store.repositories[repository_id]
        pull_request = self._request_json(
            f"https://api.github.com/repos/{repository.owner}/{repository.repo_name}/pulls/{pull_request_number}",
            repository.access_token,
        )
        files = self._request_json(
            f"https://api.github.com/repos/{repository.owner}/{repository.repo_name}/pulls/{pull_request_number}/files",
            repository.access_token,
        )
        return {
            "number": pull_request["number"],
            "title": pull_request["title"],
            "description": pull_request.get("body") or "",
            "status": pull_request["state"],
            "files": [
                {
                    "filename": item["filename"].split("/")[-1],
                    "filepath": item["filename"],
                    "additions": item.get("additions", 0),
                    "deletions": item.get("deletions", 0),
                    "change_type": item.get("status", "modified"),
                    "patch": item.get("patch") or "",
                }
                for item in files
                if item.get("patch")
            ],
        }

    def parse_github_url(self, github_url: str) -> tuple[str, str]:
        parsed = urlparse(github_url)
        path_parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc not in {"github.com", "www.github.com"} or len(path_parts) < 2:
            raise ValueError("GitHub URL must look like https://github.com/owner/repository.")
        return path_parts[0], path_parts[1]

    def _request_json(self, url: str, access_token: str) -> dict | list:
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "code-review-automation-assistant",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            message = error.read().decode("utf-8", errors="ignore")
            raise ValueError(f"GitHub API request failed: {message or error.reason}") from error
        except URLError as error:
            raise ValueError(f"Unable to reach GitHub: {error.reason}") from error
