from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## 뭐입지? AI 추천 서버

    20-40대 남성을 위한 **퀴즈 기반 패션 코디 추천 API**

    ### 주요 기능
    - 🎯 퀴즈 답변 기반 개인화 추천
    - 🤖 OpenAI GPT-3.5-turbo 기반 스타일 매칭
    - 🖼️ 자동 이미지 합성 (배경 제거 + 레이어 합성)
    - 💰 예산, 체형, 스타일 고려

    ### 기술 스택
    - FastAPI + PostgreSQL + pgvector
    - OpenAI GPT-3.5-turbo
    - AWS S3 (이미지 저장)
    - rembg (배경 제거)
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,
    contact={
        "name": "IPZY Team",
        "url": "https://github.com/cryschan/ipzy-ai",
    },
    license_info={"name": "Private"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get(
    "/",
    summary="API 루트",
    tags=["Root"],
    responses={
        200: {
            "description": "API 정보",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Fashion Coordination AI API",
                        "version": "1.0.0",
                        "docs": "/api/docs",
                    }
                }
            },
        }
    },
)
async def root():
    """
    API 루트 엔드포인트

    **Returns:**
    - message: API 이름
    - version: API 버전
    - docs: Swagger 문서 URL
    """
    return {
        "message": "Fashion Coordination AI API",
        "version": "1.0.0",
        "docs": f"{settings.API_PREFIX}/docs",
    }


@app.get(
    "/health",
    summary="헬스 체크",
    tags=["Health Check"],
    responses={
        200: {
            "description": "서비스 정상",
            "content": {
                "application/json": {"example": {"status": "healthy"}}
            },
        }
    },
)
async def health_check():
    """
    전체 서비스 헬스 체크

    **Returns:**
    - status: 서비스 상태 (healthy)
    """
    return {"status": "healthy"}
