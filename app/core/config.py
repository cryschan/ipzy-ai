from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fashion Coordination AI"
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = ["*"]

    OPENAI_API_KEY: str = ""

    VECTOR_DB_PATH: str = "./data/vector_db"

    CHROMA_COLLECTION_NAME: str = "fashion_products"

    IMAGE_OUTPUT_DIR: str = "./outputs/composites"

    MAX_PRODUCTS_PER_CATEGORY: int = 5
    MAX_RECOMMENDATIONS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
