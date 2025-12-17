"""
퀴즈 기반 추천 API 엔드포인트
Java 백엔드로부터 퀴즈 답변을 받아 코디를 추천합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.quiz_recommendation import (
    QuizRecommendationRequest,
    QuizRecommendationResponse
)
from app.services.quiz_recommendation_service import QuizRecommendationService
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recommend", response_model=QuizRecommendationResponse)
async def recommend(
    request: QuizRecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    퀴즈 답변 기반 코디 추천 (Java 백엔드 호출용)

    Java 백엔드로부터 퀴즈 세션 ID와 답변을 받아서
    사용자에게 최적의 코디 조합을 3개 추천합니다.

    **플로우:**
    1. 퀴즈 답변 파싱 (상황, 스타일, 체형, 예산)
    2. 스타일 매핑 (occasion + style → primary_style)
    3. DB에서 상품 후보 조회 (카테고리별 10개씩)
    4. LLM으로 최적 조합 선택 (3개)
    5. DTO 변환하여 반환

    **Args:**
    - request: 퀴즈 답변 요청 (sessionId, answers)

    **Returns:**
    - 추천 코디 리스트 (recommendedOutfits)
    """
    try:
        logger.info(f"Received recommendation request for session {request.sessionId}")

        # 추천 서비스 생성
        service = QuizRecommendationService(db)

        # 추천 생성
        response = await service.generate_recommendations(request)

        logger.info(f"Successfully generated {len(response.recommended_outfits)} recommendations")

        return response

    except Exception as e:
        logger.exception(f"Failed to generate recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"추천 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health/recommendation")
async def health_check():
    """
    추천 서비스 헬스 체크
    """
    return {
        "status": "healthy",
        "service": "quiz-recommendation"
    }
