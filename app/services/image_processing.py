from PIL import Image
from rembg import remove
import requests
from io import BytesIO
from typing import List
import uuid
import hashlib
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from app.schemas.recommendation import ProductItem


class ImageProcessingService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

    def _get_url_hash(self, url: str) -> str:
        """Generate MD5 hash from URL for caching"""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_s3_object_exists(self, s3_key: str) -> bool:
        """Check if object exists in S3"""
        try:
            self.s3_client.head_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
            return True
        except ClientError:
            return False

    def _get_s3_url(self, s3_key: str) -> str:
        """Generate S3 public URL"""
        return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

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

            filename = f"{uuid.uuid4()}.png"
            s3_key = f"{settings.S3_IMAGE_PREFIX}/composite/{filename}"

            buffer = BytesIO()
            composite.save(buffer, format='PNG')
            buffer.seek(0)

            self.s3_client.upload_fileobj(
                buffer,
                settings.AWS_S3_BUCKET,
                s3_key,
                ExtraArgs={
                    'ContentType': 'image/png'
                }
            )

            s3_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

            return s3_url

        except ClientError as e:
            print(f"S3 upload error: {str(e)}")
            return None
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
            # Generate hash-based S3 key for caching
            url_hash = self._get_url_hash(image_url)
            s3_key = f"{settings.S3_IMAGE_PREFIX}/{url_hash}.png"

            # Check if already exists in S3
            if self._check_s3_object_exists(s3_key):
                print(f"Cache hit! Returning existing image for: {image_url}")
                return self._get_s3_url(s3_key)

            # Cache miss - process image
            print(f"Cache miss. Processing new image: {image_url}")
            output_image = await self._download_and_remove_bg(image_url)

            if not output_image:
                return None

            # Upload to S3 with hash-based filename
            buffer = BytesIO()
            output_image.save(buffer, format='PNG')
            buffer.seek(0)

            self.s3_client.upload_fileobj(
                buffer,
                settings.AWS_S3_BUCKET,
                s3_key,
                ExtraArgs={
                    'ContentType': 'image/png'
                }
            )

            return self._get_s3_url(s3_key)

        except ClientError as e:
            print(f"S3 upload error: {str(e)}")
            return None
        except Exception as e:
            print(f"Remove background error: {str(e)}")
            return None
