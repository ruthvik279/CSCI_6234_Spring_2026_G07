from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Code Review Automation Assistant"
    default_complexity_threshold: int = 15


settings = Settings()
