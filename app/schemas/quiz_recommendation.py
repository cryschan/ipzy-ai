"""
퀴즈 기반 추천 API 스키마
Java 백엔드와 통신하는 DTO 정의
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class QuizAnswerDto(BaseModel):
    """퀴즈 답변 DTO"""

    questionId: int = Field(..., description="질문 ID")
    questionText: str = Field(..., description="질문 텍스트")
    selectedOptions: List[str] = Field(..., description="선택한 옵션 값 리스트")


class QuizRecommendationRequest(BaseModel):
    """Java → Python 추천 요청"""

    sessionId: int = Field(..., description="퀴즈 세션 ID")
    answers: List[QuizAnswerDto] = Field(..., description="퀴즈 답변 리스트")
    exclude_combinations: List[List[int]] = Field(
        default=[],
        alias="excludeCombinations",
        description="제외할 상품 조합 리스트 (이전에 본 코디의 상품 ID 리스트)",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "sessionId": 123,
                "answers": [
                    {
                        "questionId": 1,
                        "questionText": "어디 가요?",
                        "selectedOptions": ["date"],
                    },
                    {
                        "questionId": 2,
                        "questionText": "어떻게 보이고 싶어요?",
                        "selectedOptions": ["stylish"],
                    },
                    {
                        "questionId": 3,
                        "questionText": "체형 고민?",
                        "selectedOptions": ["none"],
                    },
                    {
                        "questionId": 4,
                        "questionText": "예산은?",
                        "selectedOptions": ["300000"],
                    },
                ],
                "excludeCombinations": [[1, 2, 3, 4], [5, 6, 7, 8]],
            }
        }


class ItemPositionDto(BaseModel):
    """아이템 위치 정보 DTO - Java로 전송"""

    x: Optional[int] = Field(None, description="X 좌표 (px)")
    y: Optional[int] = Field(None, description="Y 좌표 (px)")
    width: Optional[int] = Field(None, description="너비 (px)")
    height: Optional[int] = Field(None, description="높이 (px)")


class RecommendedItemDto(BaseModel):
    """추천 아이템 DTO - Java로 전송"""

    product_id: int = Field(..., alias="productId", description="상품 ID")
    category: str = Field(
        ..., description="카테고리 (TOP, BOTTOM, OUTER, SHOES, ACCESSORY)"
    )
    name: str = Field(..., description="상품명")
    brand: str = Field(..., description="브랜드명")
    price: int = Field(..., description="가격")
    image_url: str = Field(..., alias="imageUrl", description="이미지 URL")
    link_url: str = Field(..., alias="linkUrl", description="구매 링크 URL")
    position: Optional[ItemPositionDto] = Field(
        None, description="합성 이미지 내 위치 정보"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "product_id": 123,
                "category": "TOP",
                "name": "오버핏 화이트 셔츠",
                "brand": "무신사 스탠다드",
                "price": 50000,
                "image_url": "https://s3.../product.png",
                "link_url": "https://musinsa.com/...",
                "position": {"x": 100, "y": 200, "width": 300, "height": 400},
            }
        }


class OutfitResultDto(BaseModel):
    """코디 추천 결과 DTO - OutfitRecommendationDto의 result 필드"""

    success: bool = Field(True, description="성공 여부")
    message: str = Field("추천 완료", description="상태 메시지")
    composite_image_url: Optional[str] = Field(
        None, alias="compositeImageUrl", description="합성 이미지 URL"
    )
    image_width: Optional[int] = Field(
        None, alias="imageWidth", description="이미지 너비 (px)"
    )
    image_height: Optional[int] = Field(
        None, alias="imageHeight", description="이미지 높이 (px)"
    )
    total_price: int = Field(..., alias="totalPrice", description="총 가격")
    items: List[RecommendedItemDto] = Field(..., description="추천 아이템 리스트")

    class Config:
        populate_by_name = True


class OutfitRecommendationDto(BaseModel):
    """개별 코디 추천 DTO - Java로 전송 (PR #30 신규 구조)"""

    displayOrder: int = Field(..., description="표시 순서 (1, 2, 3)")
    occasion: str = Field(..., description="상황 (회사, 데이트, 소개팅/모임, 외출)")
    season: str = Field(default="all", description="계절 (봄, 여름, 가을, 겨울, all)")
    style: str = Field(..., description="스타일 (미니멀, 스트릿 등)")
    reason: str = Field(..., description="추천 이유")
    status: str = Field(
        default="completed", description="작업 상태 (completed, pending, failed)"
    )
    job_id: Optional[str] = Field(None, alias="jobId", description="작업 ID (비동기용)")
    created_at: Optional[str] = Field(None, alias="createdAt", description="생성 시각")
    completed_at: Optional[str] = Field(
        None, alias="completedAt", description="완료 시각"
    )
    result: OutfitResultDto = Field(..., description="추천 결과")
    error: Optional[str] = Field(None, description="에러 메시지")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "displayOrder": 1,
                "occasion": "데이트",
                "season": "봄",
                "style": "미니멀",
                "reason": "깔끔하고 세련된 데이트 룩입니다.",
                "status": "completed",
                "jobId": None,
                "createdAt": None,
                "completedAt": None,
                "result": {
                    "success": True,
                    "message": "추천 완료",
                    "compositeImageUrl": "https://s3.../composite_123.png",
                    "imageWidth": 1200,
                    "imageHeight": 1600,
                    "totalPrice": 250000,
                    "items": [
                        {
                            "product_id": 1,
                            "category": "TOP",
                            "name": "오버핏 화이트 셔츠",
                            "brand": "무신사 스탠다드",
                            "price": 50000,
                            "image_url": "https://s3.../top.png",
                            "link_url": "https://musinsa.com/...",
                            "position": {
                                "x": 100,
                                "y": 200,
                                "width": 300,
                                "height": 400,
                            },
                        }
                    ],
                },
                "error": None,
            }
        }


class QuizRecommendationResponse(BaseModel):
    """Python → Java 추천 응답"""

    recommended_outfits: List[OutfitRecommendationDto] = Field(
        ..., alias="recommendedOutfits", description="추천 코디 리스트 (최대 3개)"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "recommendedOutfits": [
                    {
                        "displayOrder": 1,
                        "occasion": "데이트",
                        "season": "봄",
                        "style": "미니멀",
                        "reason": "깔끔하고 세련된 데이트 룩입니다.",
                        "status": "completed",
                        "jobId": None,
                        "createdAt": None,
                        "completedAt": None,
                        "result": {
                            "success": True,
                            "message": "추천 완료",
                            "compositeImageUrl": "https://s3.../composite_1.png",
                            "imageWidth": 1200,
                            "imageHeight": 1600,
                            "totalPrice": 250000,
                            "items": [
                                {
                                    "productId": 1,
                                    "category": "TOP",
                                    "name": "화이트 셔츠",
                                    "brand": "브랜드",
                                    "price": 50000,
                                    "imageUrl": "https://...",
                                    "linkUrl": "https://...",
                                    "position": {
                                        "x": 200,
                                        "y": 100,
                                        "width": 200,
                                        "height": 240,
                                    },
                                }
                            ],
                        },
                        "error": None,
                    }
                ]
            }
        }
