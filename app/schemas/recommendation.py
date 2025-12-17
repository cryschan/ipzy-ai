from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class LocationEnum(str, Enum):
    OFFICE = "office"
    CASUAL = "casual"
    DATE = "date"
    SPORT = "sport"
    PARTY = "party"
    OUTDOOR = "outdoor"


class StyleEnum(str, Enum):
    CLASSIC = "classic"
    MODERN = "modern"
    STREET = "street"
    MINIMAL = "minimal"
    ROMANTIC = "romantic"
    SPORTY = "sporty"


class BodyTypeEnum(str, Enum):
    SLIM = "slim"
    REGULAR = "regular"
    ATHLETIC = "athletic"
    PLUS = "plus"


class RecommendationRequest(BaseModel):
    location: LocationEnum = Field(..., description="장소 (예: office, casual, date)")
    style: StyleEnum = Field(..., description="스타일 (예: classic, modern, street)")
    body_type: BodyTypeEnum = Field(
        ..., description="체형 (예: slim, regular, athletic)"
    )
    budget_min: int = Field(..., ge=0, description="최소 예산 (원)")
    budget_max: int = Field(..., ge=0, description="최대 예산 (원)")
    gender: str = Field(..., description="성별 (male/female/unisex)")
    additional_preferences: Optional[str] = Field(None, description="추가 선호 사항")

    class Config:
        json_schema_extra = {
            "example": {
                "location": "office",
                "style": "classic",
                "body_type": "regular",
                "budget_min": 100000,
                "budget_max": 500000,
                "gender": "male",
                "additional_preferences": "편안한 착용감 선호",
            }
        }


class ProductItem(BaseModel):
    product_id: str
    name: str
    category: str
    price: int
    brand: str
    image_url: str
    description: Optional[str] = None


class CoordinationSet(BaseModel):
    set_id: str
    products: List[ProductItem]
    total_price: int
    reasoning: str
    composite_image_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    request_summary: str
    recommendations: List[CoordinationSet]
    processing_time: float

    class Config:
        json_schema_extra = {
            "example": {
                "request_summary": "오피스룩, 클래식 스타일, 10만원~50만원 예산",
                "recommendations": [
                    {
                        "set_id": "coord_001",
                        "products": [
                            {
                                "product_id": "prod_123",
                                "name": "클래식 화이트 셔츠",
                                "category": "top",
                                "price": 89000,
                                "brand": "Brand A",
                                "image_url": "https://example.com/shirt.jpg",
                            }
                        ],
                        "total_price": 450000,
                        "reasoning": "클래식한 오피스룩을 위한 기본 아이템 조합",
                        "composite_image_url": "https://example.com/composite_001.jpg",
                    }
                ],
                "processing_time": 2.5,
            }
        }
