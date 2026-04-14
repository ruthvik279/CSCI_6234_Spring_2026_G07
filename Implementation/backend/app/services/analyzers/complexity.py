from __future__ import annotations

from app.models.domain import FileChange, Issue
from app.services.analyzers.base import Analyzer


class ComplexityAnalyzer(Analyzer):
    issue_type = "complexity"
    severity = "medium"

    def analyze(self, file_change: FileChange, config: dict | None = None) -> list[Issue]:
        issues: list[Issue] = []
        control_flow_terms = ("if ", "for ", "while ", "case ", "catch ", "elif ", "switch ")
        threshold = int((config or {}).get("threshold") or 15)
        severity = (config or {}).get("severity")
        complexity_score = 1
        hottest_line = 1
        hottest_line_score = 0

        for line_number, line in file_change.parsed_lines():
            normalized_line = line.strip().lower()
            branch_score = sum(normalized_line.count(token.strip()) for token in control_flow_terms)
            branch_score += normalized_line.count(" and ")
            branch_score += normalized_line.count(" or ")
            branch_score += normalized_line.count("&&")
            branch_score += normalized_line.count("||")
            complexity_score += branch_score

            if branch_score > hottest_line_score:
                hottest_line_score = branch_score
                hottest_line = line_number

        if complexity_score > threshold:
            issue = self.build_issue(
                file_change=file_change,
                line_number=hottest_line,
                message=f"Estimated complexity score {complexity_score} exceeds the threshold of {threshold}.",
                suggestion="Split the logic into smaller functions or simplify branching.",
            )
            if severity:
                issue.severity = severity
            issues.append(issue)
        return issues
