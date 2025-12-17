from pydantic import BaseModel, Field
from typing import List

IMAGE_URL = "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg"

class ImageRemoveBackgroundRequest(BaseModel):
    image_url: str = Field(
        ...,
        description="URL of the image to remove background from",
        examples=[
            IMAGE_URL
        ]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "image_url": IMAGE_URL
                }
            ]
        }
    }

class ImageRemoveBackgroundResponse(BaseModel):
    success: bool = Field(..., description="배경 제거 성공 여부")
    nobg_image_url: str | None = Field(None, description="배경이 제거된 이미지의 URL")
    message: str | None = Field(None, description="상태 메시지")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "nobg_image_url": "https://example-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/example.png",
                    "message": "Background removed successfully"
                }
            ]
        }
    }


class BatchRemoveBackgroundRequest(BaseModel):
    image_urls: List[str] = Field(
        ...,
        description="배경을 제거할 이미지 URL 목록 (최대 10개)",
        min_length=1,
        max_length=10
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "image_urls": [
                        "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20240515/4073073/4073073_16848382344714_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20240412/3987654/3987654_17128901234567_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20240310/3876543/3876543_17091234567890_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20240205/3765432/3765432_17083456789012_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20240115/3654321/3654321_17075678901234_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20231220/3543210/3543210_17067890123456_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20231105/3432109/3432109_17059012345678_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20231001/3321098/3321098_17051234567890_big.jpg",
                        "https://image.msscdn.net/thumbnails/images/goods_img/20230820/3210987/3210987_17043456789012_big.jpg"
                    ]
                }
            ]
        }
    }


class BatchRemoveBackgroundItem(BaseModel):
    original_url: str = Field(..., description="원본 이미지 URL")
    nobg_image_url: str | None = Field(None, description="배경이 제거된 이미지의 URL")
    success: bool = Field(..., description="처리 성공 여부")
    error: str | None = Field(None, description="실패 시 에러 메시지")


class BatchRemoveBackgroundResponse(BaseModel):
    success: bool = Field(..., description="전체 배치 처리 성공 여부")
    results: List[BatchRemoveBackgroundItem] = Field(..., description="각 이미지별 처리 결과")
    total_count: int = Field(..., description="전체 이미지 개수")
    success_count: int = Field(..., description="성공한 이미지 개수")
    failed_count: int = Field(..., description="실패한 이미지 개수")
    processing_time: float = Field(..., description="총 처리 시간(초)")
    message: str | None = Field(None, description="상태 메시지")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "results": [
                        {
                            "original_url": IMAGE_URL,
                            "nobg_image_url": "https://example-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/abc123.png",
                            "success": True,
                            "error": None
                        },
                        {
                            "original_url": "https://invalid-url.com/image.jpg",
                            "nobg_image_url": None,
                            "success": False,
                            "error": "Failed to download image"
                        }
                    ],
                    "total_count": 2,
                    "success_count": 1,
                    "failed_count": 1,
                    "processing_time": 3.5,
                    "message": "Batch processing completed: 1 succeeded, 1 failed"
                }
            ]
        }
    }


class CompositeImageItem(BaseModel):
    product_id: int = Field(..., description="상품 ID")
    category: str = Field(..., description="카테고리 (TOP, BOTTOM, SHOES, OUTER, ACCESSORY)")
    name: str = Field(..., description="상품명")
    brand: str = Field(..., description="브랜드명")
    price: int = Field(..., description="상품 가격")
    image_url: str = Field(..., description="원본 이미지 URL")
    link_url: str = Field(..., description="상품 링크 URL")
    nobg_image_url: str = Field(..., description="배경 제거된 이미지 URL")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": 118,
                    "category": "TOP",
                    "name": "오버핏 옥스포드 셔츠",
                    "brand": "무신사 스탠다드",
                    "price": 59000,
                    "image_url": "https://example.com/image4.jpg",
                    "link_url": "https://example.com/product4",
                    "nobg_image_url": "https://example-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/28f359d51c0584bad37b333181e0aa1b.png"
                }
            ]
        }
    }


class CreateCompositeImageRequest(BaseModel):
    items: List[CompositeImageItem] = Field(..., description="합성에 사용할 상품 목록")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "product_id": 118,
                            "category": "TOP",
                            "name": "오버핏 옥스포드 셔츠",
                            "brand": "무신사 스탠다드",
                            "price": 59000,
                            "image_url": "https://example.com/image4.jpg",
                            "link_url": "https://example.com/product4",
                            "nobg_image_url": "https://fastcampus-finalproject-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/28f359d51c0584bad37b333181e0aa1b.png"
                        },
                        {
                            "product_id": 220,
                            "category": "BOTTOM",
                            "name": "와이드 슬랙스 팬츠",
                            "brand": "커버낫",
                            "price": 79000,
                            "image_url": "https://example.com/image5.jpg",
                            "link_url": "https://example.com/product5",
                            "nobg_image_url": "https://fastcampus-finalproject-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/c6927aeabf58ddc09925ca0945b67509.png"
                        },
                        {
                            "product_id": 315,
                            "category": "SHOES",
                            "name": "운동화",
                            "brand": "나이키",
                            "price": 100000,
                            "image_url": "https://example.com/image6.jpg",
                            "link_url": "https://example.com/product6",
                            "nobg_image_url": "https://fastcampus-finalproject-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/2f0927359e4d862f7313d4350f27deed.png"
                        },
                        {
                            "product_id": 415,
                            "category": "OUTER",
                            "name": "패딩",
                            "brand": "나이키",
                            "price": 100000,
                            "image_url": "https://example.com/image6.jpg",
                            "link_url": "https://example.com/product6",
                            "nobg_image_url": "https://fastcampus-finalproject-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/1c0c614bb64dbd5a34d142230b96f287.png"
                        },
                        {
                            "product_id": 515,
                            "category": "ACCESSORY",
                            "name": "목도리",
                            "brand": "나이키",
                            "price": 100000,
                            "image_url": "https://example.com/image6.jpg",
                            "link_url": "https://example.com/product6",
                            "nobg_image_url": "https://fastcampus-finalproject-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/0fab2b1f957f14e60be7f53fa2bf483a.png"
                        }
                    ]
                }
            ]
        }
    }


class ItemPosition(BaseModel):
    x: int = Field(..., description="X 좌표(좌측 상단, px)")
    y: int = Field(..., description="Y 좌표(좌측 상단, px)")
    width: int = Field(..., description="너비(px)")
    height: int = Field(..., description="높이(px)")


class CompositeImageItemWithPosition(BaseModel):
    product_id: int = Field(..., description="상품 ID")
    category: str = Field(..., description="카테고리")
    name: str = Field(..., description="상품명")
    brand: str = Field(..., description="브랜드명")
    price: int = Field(..., description="상품 가격")
    link_url: str = Field(..., description="상품 링크 URL")
    position: ItemPosition = Field(..., description="합성 이미지 내 배치 좌표")


class CreateCompositeImageResponse(BaseModel):
    success: bool = Field(..., description="합성 이미지 생성 성공 여부")
    message: str | None = Field(None, description="상태 메시지")
    composite_image_url: str | None = Field(None, description="합성 이미지 URL")
    image_width: int = Field(1200, description="합성 이미지 가로(px)")
    image_height: int = Field(1600, description="합성 이미지 세로(px)")
    total_price: int = Field(0, description="모든 상품의 총가격")
    items: List[CompositeImageItemWithPosition] | None = Field(None, description="이미지 내 각 상품의 배치 정보")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Composite image created successfully",
                    "composite_image_url": "https://example-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/composite/example.png",
                    "image_width": 1200,
                    "image_height": 1600,
                    "total_price": 59000,
                    "items": [
                        {
                            "product_id": 118,
                            "category": "TOP",
                            "name": "오버핏 옥스포드 셔츠",
                            "brand": "무신사 스탠다드",
                            "price": 59000,
                            "link_url": "https://example.com/product4",
                            "position": {
                                "x": 150,
                                "y": 100,
                                "width": 480,
                                "height": 640
                            }
                        }
                    ]
                }
            ]
        }
    }


class CreateCompositeJobResponse(BaseModel):
    success: bool = Field(..., description="작업 생성 성공 여부")
    job_id: str = Field(..., description="합성 이미지 생성 작업 추적용 Job ID")
    message: str | None = Field(None, description="상태 메시지")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "job_id": "abc123-def456-ghi789",
                    "message": "Composite image creation job started"
                }
            ]
        }
    }


class CompositeJobStatus(BaseModel):
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="작업 상태: pending, processing, completed, failed")
    created_at: str = Field(..., description="작업 생성 시각")
    completed_at: str | None = Field(None, description="작업 완료 시각")
    result: CreateCompositeImageResponse | None = Field(None, description="완료 시 결과 데이터")
    error: str | None = Field(None, description="실패 시 오류 메시지")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "abc123-def456-ghi789",
                    "status": "completed",
                    "created_at": "2024-01-15T10:30:00Z",
                    "completed_at": "2024-01-15T10:30:05Z",
                    "result": {
                        "success": True,     
                        "message": "Composite image created successfully",
                        "composite_image_url": "https://example.com/composite/abc.png",
                        "image_width": 1200,
                        "image_height": 1600,
                        "total_price": 438000,
                        "items": [],
                    },
                    "error": None
                }
            ]
        }
    }
