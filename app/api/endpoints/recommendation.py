"""
퀴즈 기반 추천 API 엔드포인트
Java 백엔드로부터 퀴즈 답변을 받아 코디를 추천합니다.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.quiz_recommendation import (
    QuizRecommendationRequest,
    QuizRecommendationResponse,
)
from app.services.quiz_recommendation_service import QuizRecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/recommend",
    response_model=QuizRecommendationResponse,
    summary="퀴즈 기반 코디 추천",
    tags=["Quiz Recommendation"],
    responses={
        200: {
            "description": "추천 성공",
            "content": {
                "application/json": {
                    "example": {
                        "recommendedOutfits": [
                            {
                                "displayOrder": 1,
                                "occasion": "데이트",
                                "season": "all",
                                "style": "세련",
                                "reason": "깔끔하고 세련된 데이트 룩입니다.",
                                "status": "completed",
                                "jobId": None,
                                "createdAt": None,
                                "completedAt": None,
                                "result": {
                                    "success": True,
                                    "message": "추천 완료",
                                    "compositeImageUrl": "https://s3.amazonaws.com/composite/abc123.png",
                                    "imageWidth": 600,
                                    "imageHeight": 800,
                                    "totalPrice": 250000,
                                    "items": [
                                        {
                                            "productId": 1,
                                            "category": "TOP",
                                            "name": "오버핏 화이트 셔츠",
                                            "brand": "무신사 스탠다드",
                                            "price": 50000,
                                            "imageUrl": "https://s3.../top.png",
                                            "linkUrl": "https://musinsa.com/...",
                                            "position": {
                                                "x": 200,
                                                "y": 100,
                                                "width": 200,
                                                "height": 240,
                                            },
                                        },
                                        {
                                            "productId": 2,
                                            "category": "BOTTOM",
                                            "name": "슬림 블랙진",
                                            "brand": "리바이스",
                                            "price": 80000,
                                            "imageUrl": "https://s3.../bottom.png",
                                            "linkUrl": "https://musinsa.com/...",
                                            "position": {
                                                "x": 200,
                                                "y": 800,
                                                "width": 200,
                                                "height": 240,
                                            },
                                        },
                                    ],
                                },
                                "error": None,
                            }
                        ]
                    }
                }
            },
        },
        404: {
            "description": "상품 없음",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "해당 조건에 맞는 상품이 없습니다. 다른 옵션을 선택해주세요."
                    }
                }
            },
        },
        503: {
            "description": "AI 서비스 일시 장애",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "AI 추천 서비스 일시 장애. 잠시 후 다시 시도해주세요."
                    }
                }
            },
        },
        500: {
            "description": "서버 에러",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "추천 생성 중 오류가 발생했습니다: Internal Server Error"
                    }
                }
            },
        },
    },
)
async def recommend(
    request: QuizRecommendationRequest, db: AsyncSession = Depends(get_db)
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
    5. 이미지 합성 및 DTO 변환하여 반환

    **Args:**
    - request: 퀴즈 답변 요청 (sessionId, answers)

    **Returns:**
    - 추천 코디 리스트 (recommendedOutfits) - 각 코디는 상의/하의/아우터/신발 조합 + 합성 이미지 포함
    """
    try:
        logger.info(f"Received recommendation request for session {request.sessionId}")

        # 추천 서비스 생성
        service = QuizRecommendationService(db)

        # 추천 생성
        response = await service.generate_recommendations(request)

        logger.info(
            f"Successfully generated {len(response.recommended_outfits)} recommendations"
        )

        return response

    except HTTPException:
        raise  # HTTPException은 그대로 전파 (503, 404 등)
    except Exception as e:
        logger.exception("Failed to generate recommendations")
        raise HTTPException(
            status_code=500,
            detail="추천 생성 중 오류가 발생했습니다: Internal Server Error",
        ) from e


@router.get(
    "/health/recommendation",
    summary="추천 서비스 헬스 체크",
    tags=["Health Check"],
    responses={
        200: {
            "description": "서비스 정상",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "service": "quiz-recommendation"}
                }
            },
        }
    },
)
async def health_check():
    """
    추천 서비스 헬스 체크

    **Returns:**
    - status: 서비스 상태 (healthy)
    - service: 서비스 이름
    """
    return {"status": "healthy", "service": "quiz-recommendation"}
