from __future__ import annotations

from app.models.domain import FileChange, Issue
from app.services.analyzers.base import Analyzer


class StyleAnalyzer(Analyzer):
    issue_type = "style"
    severity = "low"
    rules: list[str] = ["line-length", "trailing-whitespace"]

    def analyze(self, file_change: FileChange, config: dict | None = None) -> list[Issue]:
        issues: list[Issue] = []
        threshold = int((config or {}).get("threshold") or 100)
        severity = (config or {}).get("severity")
        for line_number, line in file_change.parsed_lines():
            if len(line) > threshold:
                issue = self.build_issue(
                    file_change=file_change,
                    line_number=line_number,
                    message=f"Line exceeds {threshold} characters.",
                    suggestion="Wrap the statement or extract part of the expression.",
                )
                if severity:
                    issue.severity = severity
                issues.append(issue)
            if line.rstrip() != line:
                issue = self.build_issue(
                    file_change=file_change,
                    line_number=line_number,
                    message="Trailing whitespace detected.",
                    suggestion="Remove trailing spaces to keep diffs cleaner.",
                )
                if severity:
                    issue.severity = severity
                issues.append(issue)
        return issues

    def checkStyle(self, file_change: FileChange, config: dict | None = None) -> list[Issue]:
        return self.analyze(file_change, config)
