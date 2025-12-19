from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.image import (
    ImageRemoveBackgroundRequest,
    ImageRemoveBackgroundResponse,
    BatchRemoveBackgroundRequest,
    BatchRemoveBackgroundResponse,
    CreateCompositeImageRequest,
    CreateCompositeJobResponse,
    CompositeJobStatus,
)
from app.services.image_processing import ImageProcessingService
from app.services.job_manager import job_manager
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()
image_service = ImageProcessingService()


@router.post("/remove-background", response_model=ImageRemoveBackgroundResponse)
async def remove_background(request: ImageRemoveBackgroundRequest):
    try:
        nobg_image_url, error_msg = await image_service.remove_background(
            request.image_url
        )

        if not nobg_image_url:
            raise HTTPException(
                status_code=500,
                detail=error_msg or "Failed to remove background from image",
            )

        return ImageRemoveBackgroundResponse(
            success=True,
            nobg_image_url=nobg_image_url,
            message="Background removed successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing image: {str(e)}"
        ) from e


@router.post("/remove-background/batch", response_model=BatchRemoveBackgroundResponse)
async def remove_background_batch(request: BatchRemoveBackgroundRequest):
    """
    여러 이미지의 배경을 한 번에 제거합니다 (최대 15개).
    모든 이미지를 병렬로 처리하여 처리 시간을 최소화합니다.
    """
    try:
        start_time = time.time()

        # 배치 처리 실행
        results = await image_service.remove_background_batch(request.image_urls)

        # 처리 시간 계산
        processing_time = time.time() - start_time

        # 통계 계산
        total_count = len(results)
        success_count = sum(1 for r in results if r["success"])
        failed_count = total_count - success_count

        # 전체 성공 여부 (하나라도 성공하면 True)
        overall_success = success_count > 0

        message = f"Batch processing completed: {success_count} succeeded, {failed_count} failed"

        return BatchRemoveBackgroundResponse(
            success=overall_success,
            results=results,
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            processing_time=round(processing_time, 2),
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch background removal error")
        raise HTTPException(
            status_code=500, detail=f"Error processing batch: {str(e)}"
        ) from e


async def _process_composite_job(job_id: str, items):
    """합성 이미지 생성 작업을 백그라운드에서 처리합니다."""
    try:
        job_manager.update_job_status(job_id, "processing")

        result = await image_service.create_composite_image(items)

        if not result:
            job_manager.fail_job(job_id, "Failed to create composite image")
            return

        response_data = {
            "success": True,
            "composite_image_url": result["composite_url"],
            "image_width": result["image_width"],
            "image_height": result["image_height"],
            "items": result["items"],
            "total_price": result["total_price"],
            "message": "Composite image created successfully",
        }

        job_manager.complete_job(job_id, response_data)

    except Exception as e:
        logger.exception(f"Error processing composite job {job_id}")
        job_manager.fail_job(job_id, str(e))


@router.post("/composite/create", response_model=CreateCompositeJobResponse)
async def create_composite(
    request: CreateCompositeImageRequest, background_tasks: BackgroundTasks
):
    """
    합성 이미지를 비동기로 생성합니다.
    생성된 작업을 추적할 수 있도록 즉시 job_id를 반환합니다.
    """
    try:
        if not request.items or len(request.items) == 0:
            raise HTTPException(status_code=400, detail="Items list cannot be empty")

        # Validate: Check for duplicate categories
        categories = [item.category.upper() for item in request.items]
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1

        duplicates = [cat for cat, count in category_counts.items() if count > 1]
        if duplicates:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate categories found: {', '.join(duplicates)}. Each category can only appear once.",
            )

        # Validate: Check for valid categories
        valid_categories = {"TOP", "BOTTOM", "SHOES", "OUTER", "ACCESSORY"}
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid categories found: {', '.join(invalid_categories)}. Valid categories are: {', '.join(valid_categories)}",
            )

        # Create job
        job_id = job_manager.create_job()

        # Add background task
        background_tasks.add_task(_process_composite_job, job_id, request.items)

        return CreateCompositeJobResponse(
            success=True, job_id=job_id, message="Composite image creation job started"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating composite job: {str(e)}"
        ) from e


@router.get("/composite/{job_id}", response_model=CompositeJobStatus)
async def get_composite_status(job_id: str):
    """
    합성 이미지 생성 작업의 상태와 결과를 조회합니다.
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return CompositeJobStatus(**job)
