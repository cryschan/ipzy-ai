import asyncio
from app.services.image_processing import ImageProcessingService

IMAGE_URL = "https://image.msscdn.net/thumbnails/images/goods_img/20250828/5373229/5373229_17563554907585_big.jpg?w=1200"

async def test_remove_background(image_url: str):
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
    result = asyncio.run(test_remove_background(IMAGE_URL))
