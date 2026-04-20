from __future__ import annotations

import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from app.config import settings
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
        webhook_secret = secrets.token_hex(24)
        webhook_url = settings.public_webhook_url.rstrip("/") if settings.public_webhook_url else ""
        webhook_status = "not_configured"
        if webhook_url:
            webhook_status = self.ensure_webhook(owner, repo_name, access_token, webhook_url, webhook_secret)

        repository = Repository(
            repository_id=str(uuid4()),
            name=name or repo_data["name"],
            github_url=github_url,
            webhook_url=webhook_url or f"{github_url}/webhooks/code-review-assistant",
            webhook_secret=webhook_secret,
            owner=owner,
            repo_name=repo_name,
            access_token=access_token,
        )
        store.repositories[repository.repository_id] = repository
        store.rules[repository.repository_id] = self.default_rules()
        repository.webhook_url = webhook_url or repository.webhook_url
        repository.is_active = True
        repository.webhook_status = webhook_status
        return repository

    def default_rules(self) -> list[CodeReviewRule]:
        return [
            CodeReviewRule(rule_id=str(uuid4()), name="line-length", severity="low", threshold=100),
            CodeReviewRule(
                rule_id=str(uuid4()),
                name="complexity",
                severity="medium",
                threshold=settings.default_complexity_threshold,
            ),
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
                "updated_at": pull_request.get("updated_at"),
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
            "head_sha": pull_request["head"]["sha"],
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

    def find_repository_by_owner_and_name(self, owner: str, repo_name: str) -> Repository | None:
        for repository in store.repositories.values():
            if repository.owner == owner and repository.repo_name == repo_name:
                return repository
        return None

    def post_pull_request_summary_comment(self, repository_id: str, pull_request_number: int, analysis: dict) -> dict:
        repository = store.repositories[repository_id]
        severity_mix = analysis["issues_by_severity"] or {}
        top_findings = analysis["comments"][:5]
        lines = [
            "## Code Review Automation Assistant",
            "",
            f"PR #{analysis['pull_request_number']}: **{analysis['pull_request_title']}**",
            "",
            "### Review Summary",
            f"- Issues found: **{analysis['issues_found']}**",
            f"- Quality score: **{analysis['metrics'].code_quality_score}**",
            f"- Average complexity: **{analysis['metrics'].avg_complexity}**",
        ]

        if severity_mix:
            lines.append("- Severity mix: " + ", ".join(
                f"**{severity.title()}** {count}" for severity, count in severity_mix.items()
            ))
        else:
            lines.append("- Severity mix: No issues detected.")

        if top_findings:
            lines.extend(
                [
                    "",
                    "### Top Findings",
                ]
            )
            for comment in top_findings:
                lines.append(
                    f"- `{comment.file_path}:{comment.line_number}` {comment.body}"
                )
        else:
            lines.extend(
                [
                    "",
                    "### Top Findings",
                    "- No actionable findings were generated for this pull request.",
                ]
            )

        lines.extend(
            [
                "",
                "_Generated automatically by the Code Review Automation Assistant._",
            ]
        )

        payload = json.dumps({"body": "\n".join(lines)}).encode("utf-8")
        return self._request_json(
            f"https://api.github.com/repos/{repository.owner}/{repository.repo_name}/issues/{pull_request_number}/comments",
            repository.access_token,
            method="POST",
            data=payload,
        )

    def post_pull_request_inline_comments(
        self,
        repository_id: str,
        pull_request_number: int,
        github_pull_request: dict,
        analysis: dict,
    ) -> dict:
        repository = store.repositories[repository_id]
        comment_payloads = self._build_inline_comment_payloads(github_pull_request, analysis)
        if not comment_payloads:
            return {"posted": 0}

        payload = json.dumps(
            {
                "body": "Inline findings from the Code Review Automation Assistant.",
                "event": "COMMENT",
                "commit_id": github_pull_request["head_sha"],
                "comments": comment_payloads,
            }
        ).encode("utf-8")
        return self._request_json(
            f"https://api.github.com/repos/{repository.owner}/{repository.repo_name}/pulls/{pull_request_number}/reviews",
            repository.access_token,
            method="POST",
            data=payload,
        )

    def ensure_webhook(
        self,
        owner: str,
        repo_name: str,
        access_token: str,
        webhook_url: str,
        webhook_secret: str,
    ) -> str:
        if "localhost" in webhook_url or "127.0.0.1" in webhook_url:
            return "local_only"

        existing_hooks = self._request_json(
            f"https://api.github.com/repos/{owner}/{repo_name}/hooks",
            access_token,
        )
        for hook in existing_hooks:
            if ((hook.get("config") or {}).get("url")) == webhook_url:
                return "already_registered"

        payload = json.dumps(
            {
                "name": "web",
                "active": True,
                "events": ["pull_request"],
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "insecure_ssl": "0",
                    "secret": webhook_secret,
                },
            }
        ).encode("utf-8")
        self._request_json(
            f"https://api.github.com/repos/{owner}/{repo_name}/hooks",
            access_token,
            method="POST",
            data=payload,
        )
        return "registered"

    def parse_github_url(self, github_url: str) -> tuple[str, str]:
        parsed = urlparse(github_url)
        path_parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc not in {"github.com", "www.github.com"} or len(path_parts) < 2:
            raise ValueError("GitHub URL must look like https://github.com/owner/repository.")
        return path_parts[0], path_parts[1]

    def _build_inline_comment_payloads(self, github_pull_request: dict, analysis: dict) -> list[dict]:
        available_files = {item["filepath"]: item for item in github_pull_request.get("files", [])}
        payloads: list[dict] = []
        seen_targets: set[tuple[str, int, str]] = set()

        for comment in analysis["comments"]:
            file_data = available_files.get(comment.file_path)
            if not file_data:
                continue
            target = (comment.file_path, comment.line_number, comment.body)
            if target in seen_targets:
                continue
            seen_targets.add(target)
            payloads.append(
                {
                    "path": comment.file_path,
                    "line": comment.line_number,
                    "side": "RIGHT",
                    "body": comment.body,
                }
            )
            if len(payloads) >= 8:
                break

        return payloads

    def _request_json(self, url: str, access_token: str, method: str = "GET", data: bytes | None = None) -> dict | list:
        request = Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
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
