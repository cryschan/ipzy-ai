from pydantic import BaseModel, Field
from typing import Optional, List


class ProductBase(BaseModel):
    name: str
    category: str
    price: int
    brand: str
    image_url: str
    description: Optional[str] = None
    tags: List[str] = []


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    product_id: str

    class Config:
        from_attributes = True


class ProductSearchQuery(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    category: Optional[str] = Field(None, description="카테고리 필터")
    min_price: Optional[int] = Field(None, description="최소 가격")
    max_price: Optional[int] = Field(None, description="최대 가격")
    limit: int = Field(10, ge=1, le=100, description="결과 개수")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "클래식 셔츠",
                "category": "top",
                "min_price": 50000,
                "max_price": 150000,
                "limit": 10
            }
        }
