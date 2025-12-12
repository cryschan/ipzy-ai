from pydantic import BaseModel, Field

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
    output_path: str | None = Field(None, description="Path to the output image with background removed")
    message: str | None = Field(None, description="Status message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "output_path": "https://fastcampus-finalproject-bucket.s3.ap-northeast-2.amazonaws.com/background-removed/1c0c614bb64dbd5a34d142230b96f287.png",
                    "message": "Background removed successfully"
                }
            ]
        }
    }
