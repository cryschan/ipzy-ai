"""
PostgreSQL 데이터베이스 연결 관리
"""

import logging

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# PostgreSQL 연결 URL 구성
# ipzy-backend와 같은 DB를 사용 (ipzy_db)
# Docker: postgres 호스트 / Local: localhost
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ipzy_db")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # SQL 로깅 (개발 시 True로 변경 가능)
    pool_size=5,
    max_overflow=10,
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base 모델 (SQLAlchemy ORM용)
Base = declarative_base()


async def get_db():
    """
    FastAPI dependency로 사용할 DB 세션 생성기

    Usage:
        @app.get("/products")
        async def get_products(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """
    데이터베이스 초기화 (테이블 생성 등)
    참고: 실제로는 Alembic 마이그레이션 사용 권장
    """
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")


async def close_db():
    """
    데이터베이스 연결 종료
    """
    await engine.dispose()
    logger.info("Database connection closed")
