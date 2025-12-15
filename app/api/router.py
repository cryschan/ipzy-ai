from fastapi import APIRouter
from app.api.endpoints import image

api_router = APIRouter()

api_router.include_router(
    image.router,
    prefix="/image",
    tags=["image"]
)
