import asyncio
from app.services.image_processing import ImageProcessingService

# Manual smoke test: this hits real network and AWS S3.
# Run from project root:
#   - As a pytest test:    pytest -q tests/integration/test_remove_bg_smoke.py -s
#   - Direct execution:    python tests/integration/test_remove_bg_smoke.py
# Requires valid AWS credentials and AWS_S3_BUCKET; do NOT run in CI.
IMAGE_URL = "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg"


async def run(image_url: str):
    service = ImageProcessingService()
    print(f"Processing image: {image_url}")

    result = await service.remove_background(image_url)

    if result:
        print(f"Success! Output saved to: {result}")
        return result
    else:
        print("Failed to remove background")
        return None


if __name__ == "__main__":
    asyncio.run(run(IMAGE_URL))


