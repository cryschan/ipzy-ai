from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fashion Coordination AI"
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = ["*"]

    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    BACKEND_API_URL: str = "http://ipzy-app:8080"
    BACKEND_API_KEY: str = ""

    VECTOR_DB_PATH: str = "./data/vector_db"

    CHROMA_COLLECTION_NAME: str = "fashion_products"

    IMAGE_OUTPUT_DIR: str = "./outputs/composites"

    MAX_PRODUCTS_PER_CATEGORY: int = 5
    MAX_RECOMMENDATIONS: int = 3

    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-1.5-flash"

    LOG_LEVEL: str = "INFO"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-northeast-2"
    S3_IMAGE_PREFIX: str = "background-removed"

    class Config:
        env_file = ".env" # .env 파일의 환경 변수 사용
        case_sensitive = True


settings = Settings()
