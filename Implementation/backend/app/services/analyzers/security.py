from __future__ import annotations

from app.models.domain import FileChange, Issue
from app.services.analyzers.base import Analyzer


class SecurityAnalyzer(Analyzer):
    issue_type = "security"
    severity = "high"

    def analyze(self, file_change: FileChange) -> list[Issue]:
        issues: list[Issue] = []
        risky_patterns = ("password =", "secret =", "api_key =", "token =")
        for index, line in enumerate(file_change.parse_code().splitlines(), start=1):
            if any(pattern in line.lower() for pattern in risky_patterns):
                issues.append(
                    self.build_issue(
                        file_change=file_change,
                        line_number=index,
                        message="Potential hard-coded secret detected.",
                        suggestion="Move secrets to environment variables or a secure secret manager.",
                    )
                )
        return issues
