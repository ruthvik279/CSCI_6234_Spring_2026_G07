from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from app.models.domain import FileChange, Issue


class Analyzer(ABC):
    issue_type: str
    severity: str

    @abstractmethod
    def analyze(self, file_change: FileChange) -> list[Issue]:
        raise NotImplementedError

    def build_issue(
        self,
        *,
        file_change: FileChange,
        line_number: int,
        message: str,
        suggestion: str,
    ) -> Issue:
        return Issue(
            issue_id=str(uuid4()),
            issue_type=self.issue_type,
            line_number=line_number,
            severity=self.severity,
            message=message,
            suggestion=suggestion,
            detected_date=datetime.utcnow(),
            file_path=file_change.filepath,
        )
