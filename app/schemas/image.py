from pydantic import BaseModel, Field
from typing import List

IMAGE_URL = "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg?w=1200"

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
    success: bool = Field(..., description="Whether the background removal was successful")
    nobg_image_url: str | None = Field(None, description="Path to the output image with background removed")
    message: str | None = Field(None, description="Status message")

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


class CompositeImageItem(BaseModel):
    product_id: int = Field(..., description="Product ID")
    category: str = Field(..., description="Category (TOP, BOTTOM, SHOES, OUTER, ACCESSORY)")
    name: str = Field(..., description="Product name")
    brand: str = Field(..., description="Brand name")
    price: int = Field(..., description="Product price")
    image_url: str = Field(..., description="Original image URL")
    link_url: str = Field(..., description="Product link URL")
    nobg_image_url: str = Field(..., description="Background-removed image URL")

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
    items: List[CompositeImageItem] = Field(..., description="List of products to compose")

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


class CreateCompositeImageResponse(BaseModel):
    success: bool = Field(..., description="Whether the composite image creation was successful")
    composite_image_url: str | None = Field(None, description="URL of the composite image")
    message: str | None = Field(None, description="Status message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "composite_image_url": "https://example-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/composite/example.png",
                    "message": "Composite image created successfully"
                }
            ]
        }
    }
