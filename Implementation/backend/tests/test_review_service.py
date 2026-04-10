from app.schemas.api import FileChangePayload, PullRequestWebhookPayload
from app.services.review_service import ReviewService


def test_process_pull_request_generates_findings():
    service = ReviewService()
    payload = PullRequestWebhookPayload(
        repository_id="repo-1",
        number=1,
        title="Test PR",
        files=[
            FileChangePayload(
                filename="app.py",
                filepath="src/app.py",
                patch="password = '123'\nif x:\n    pass\n" + ("a" * 101),
            )
        ],
    )

    result = service.process_pull_request(payload)

    assert result["issues_found"] >= 2
    assert result["metrics"].total_issues_count == result["issues_found"]
