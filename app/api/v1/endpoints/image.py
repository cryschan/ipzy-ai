from fastapi import APIRouter, HTTPException
from app.schemas.image import ImageRemoveBackgroundRequest, ImageRemoveBackgroundResponse
from app.services.image_processing import ImageProcessingService

router = APIRouter()
image_service = ImageProcessingService()

@router.post("/remove-background", response_model=ImageRemoveBackgroundResponse)
async def remove_background(request: ImageRemoveBackgroundRequest):
    try:
        output_path = await image_service.remove_background(request.image_url)

        if not output_path:
            raise HTTPException(
                status_code=500,
                detail="Failed to remove background from image"
            )

        return ImageRemoveBackgroundResponse(
            success=True,
            output_path=output_path,
            message="Background removed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        ) from e
