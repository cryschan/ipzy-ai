from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fashion Coordination AI"
    API_PREFIX: str = "/api"

    ALLOWED_ORIGINS: List[str] = ["*"]

    OPENAI_API_KEY: str = ""

    BACKEND_API_URL: str = "http://ipzy-app:8080"
    BACKEND_API_KEY: str = ""

    MAX_PRODUCTS_PER_CATEGORY: int = 5
    MAX_RECOMMENDATIONS: int = 3

    LOG_LEVEL: str = "INFO"

    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-northeast-2"
    S3_IMAGE_PREFIX: str = "background-removed"
    S3_COMPOSITE_PREFIX: str = "composite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
