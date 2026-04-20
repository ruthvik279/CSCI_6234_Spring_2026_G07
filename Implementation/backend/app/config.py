import os

from pydantic import BaseModel, Field


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings(BaseModel):
    app_name: str = "Code Review Automation Assistant"
    default_complexity_threshold: int = 15
    public_webhook_url: str = ""
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )
    cors_origin_regex: str | None = None

settings = Settings(
    app_name=os.getenv("APP_NAME", "Code Review Automation Assistant"),
    default_complexity_threshold=_get_int("DEFAULT_COMPLEXITY_THRESHOLD", 15),
    public_webhook_url=os.getenv("PUBLIC_WEBHOOK_URL", "").strip(),
    cors_origins=_split_csv(os.getenv("CORS_ORIGINS", ""))
    or [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    cors_origin_regex=os.getenv("CORS_ORIGIN_REGEX", "").strip() or None,
)
