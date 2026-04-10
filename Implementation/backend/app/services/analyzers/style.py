from __future__ import annotations

from app.models.domain import FileChange, Issue
from app.services.analyzers.base import Analyzer


class StyleAnalyzer(Analyzer):
    issue_type = "style"
    severity = "low"

    def analyze(self, file_change: FileChange) -> list[Issue]:
        issues: list[Issue] = []
        for index, line in enumerate(file_change.parse_code().splitlines(), start=1):
            if len(line) > 100:
                issues.append(
                    self.build_issue(
                        file_change=file_change,
                        line_number=index,
                        message="Line exceeds 100 characters.",
                        suggestion="Wrap the statement or extract part of the expression.",
                    )
                )
        return issues
