from fastapi import APIRouter, HTTPException
from app.schemas.image import (
    ImageRemoveBackgroundRequest,
    ImageRemoveBackgroundResponse,
    CreateCompositeImageRequest,
    CreateCompositeImageResponse
)
from app.services.image_processing import ImageProcessingService

router = APIRouter()
image_service = ImageProcessingService()

@router.post("/remove-background", response_model=ImageRemoveBackgroundResponse)
async def remove_background(request: ImageRemoveBackgroundRequest):
    try:
        nobg_image_url = await image_service.remove_background(request.image_url)

        if not nobg_image_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to remove background from image"
            )

        return ImageRemoveBackgroundResponse(
            success=True,
            nobg_image_url=nobg_image_url,
            message="Background removed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        ) from e


@router.post("/create-composite", response_model=CreateCompositeImageResponse)
async def create_composite(request: CreateCompositeImageRequest):
    try:
        if not request.items or len(request.items) == 0:
            raise HTTPException(
                status_code=400,
                detail="Items list cannot be empty"
            )

        # Validate: Check for duplicate categories
        categories = [item.category.upper() for item in request.items]
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1

        duplicates = [cat for cat, count in category_counts.items() if count > 1]
        if duplicates:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate categories found: {', '.join(duplicates)}. Each category can only appear once."
            )

        # Validate: Check for valid categories
        valid_categories = {"TOP", "BOTTOM", "SHOES", "OUTER", "ACCESSORY"}
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid categories found: {', '.join(invalid_categories)}. Valid categories are: {', '.join(valid_categories)}"
            )

        composite_image_url = await image_service.create_composite_image(request.items)

        if not composite_image_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to create composite image"
            )

        return CreateCompositeImageResponse(
            success=True,
            composite_image_url=composite_image_url,
            message="Composite image created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating composite image: {str(e)}"
        ) from e
