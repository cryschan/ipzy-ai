from PIL import Image
from rembg import remove
import requests
from io import BytesIO
from typing import List
import os
import uuid
from app.core.config import settings
from app.schemas.recommendation import ProductItem


class ImageProcessingService:
    def __init__(self):
        os.makedirs(settings.IMAGE_OUTPUT_DIR, exist_ok=True)

    async def create_composite_image(self, products: List[ProductItem]) -> str:
        try:
            processed_images = []

            for product in products:
                img = await self._download_and_remove_bg(product.image_url)
                if img:
                    processed_images.append({
                        'image': img,
                        'category': product.category
                    })

            if not processed_images:
                return None

            composite = self._compose_images(processed_images)

            output_filename = f"{uuid.uuid4()}.png"
            output_path = os.path.join(settings.IMAGE_OUTPUT_DIR, output_filename)

            composite.save(output_path, format='PNG')

            return f"/outputs/composites/{output_filename}"

        except Exception as e:
            print(f"Image processing error: {str(e)}")
            return None

    async def _download_and_remove_bg(self, image_url: str) -> Image.Image:
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            input_image = Image.open(BytesIO(response.content))

            output_image = remove(input_image)

            return output_image

        except Exception as e:
            print(f"Background removal error for {image_url}: {str(e)}")
            return None

    def _compose_images(self, processed_images: List[dict]) -> Image.Image:
        canvas_width = 1200
        canvas_height = 1600
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))

        category_positions = {
            'top': {'y': 100, 'scale': 0.4},
            'bottom': {'y': 600, 'scale': 0.4},
            'shoes': {'y': 1100, 'scale': 0.3},
            'outer': {'y': 50, 'scale': 0.45},
            'accessory': {'y': 1400, 'scale': 0.2}
        }

        for item in processed_images:
            img = item['image']
            category = item['category']

            if category not in category_positions:
                category = 'accessory'

            position_info = category_positions[category]

            img_width, img_height = img.size
            scale = position_info['scale']
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            x_position = (canvas_width - new_width) // 2
            y_position = position_info['y']

            if img_resized.mode == 'RGBA':
                canvas.paste(img_resized, (x_position, y_position), img_resized)
            else:
                canvas.paste(img_resized, (x_position, y_position))

        return canvas

    async def remove_background(self, image_url: str) -> str:
        try:
            output_image = await self._download_and_remove_bg(image_url)

            if not output_image:
                return None

            output_filename = f"{uuid.uuid4()}.png"
            output_path = os.path.join(settings.IMAGE_OUTPUT_DIR, output_filename)

            output_image.save(output_path, format='PNG')

            return f"/outputs/composites/{output_filename}"

        except Exception as e:
            print(f"Remove background error: {str(e)}")
            return None
