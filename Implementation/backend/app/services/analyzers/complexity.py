from __future__ import annotations

from app.models.domain import FileChange, Issue
from app.services.analyzers.base import Analyzer


class ComplexityAnalyzer(Analyzer):
    issue_type = "complexity"
    severity = "medium"

    def analyze(self, file_change: FileChange) -> list[Issue]:
        issues: list[Issue] = []
        control_flow_terms = ("if ", "for ", "while ", "case ", "catch ", "elif ")
        complexity_score = sum(
            1
            for line in file_change.parse_code().splitlines()
            for token in control_flow_terms
            if token in line
        )
        if complexity_score > 15:
            issues.append(
                self.build_issue(
                    file_change=file_change,
                    line_number=1,
                    message=f"Estimated complexity score {complexity_score} exceeds the threshold.",
                    suggestion="Split the logic into smaller functions or simplify branching.",
                )
            )
        return issues
