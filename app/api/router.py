from fastapi import APIRouter
from app.api.endpoints import image, recommendation

api_router = APIRouter()

api_router.include_router(
    image.router,
    prefix="/image",
    tags=["image"]
)

api_router.include_router(
    recommendation.router,
    tags=["recommendations"]
)
