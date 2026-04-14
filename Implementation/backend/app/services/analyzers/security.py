from __future__ import annotations

import re

from app.models.domain import FileChange, Issue
from app.services.analyzers.base import Analyzer


class SecurityAnalyzer(Analyzer):
    issue_type = "security"
    severity = "high"

    def analyze(self, file_change: FileChange, config: dict | None = None) -> list[Issue]:
        issues: list[Issue] = []
        severity = (config or {}).get("severity")
        assignment_pattern = re.compile(
            r"\b(password|secret|api[_-]?key|token|access[_-]?key)\b\s*[:=]\s*[\"'][^\"']{4,}[\"']",
            re.IGNORECASE,
        )
        for line_number, line in file_change.parsed_lines():
            normalized_line = line.lower()
            if "os.getenv(" in normalized_line or "process.env." in normalized_line:
                continue

            if assignment_pattern.search(line):
                issue = self.build_issue(
                    file_change=file_change,
                    line_number=line_number,
                    message="Potential hard-coded secret detected.",
                    suggestion="Move secrets to environment variables or a secure secret manager.",
                )
                if severity:
                    issue.severity = severity
                issues.append(issue)
            elif "eval(" in normalized_line or "exec(" in normalized_line:
                issue = self.build_issue(
                    file_change=file_change,
                    line_number=line_number,
                    message="Dynamic code execution detected.",
                    suggestion="Avoid eval/exec where possible and validate untrusted input carefully.",
                )
                if severity:
                    issue.severity = severity
                issues.append(issue)
        return issues
