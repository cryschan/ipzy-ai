from PIL import Image
from rembg import remove
import requests
from io import BytesIO
from typing import List
import uuid
import hashlib
import boto3
from urllib.parse import quote
from botocore.exceptions import ClientError
from app.core.config import settings
from app.schemas.recommendation import ProductItem
import logging

logger = logging.getLogger(__name__)


class ImageProcessingService:
    def __init__(self):
        # Early validation for clearer startup errors (surface misconfig at boot)
        if not settings.AWS_S3_BUCKET:
            raise RuntimeError("AWS_S3_BUCKET is not configured. Set it in your environment or .env.")

        if (settings.AWS_ACCESS_KEY_ID and not settings.AWS_SECRET_ACCESS_KEY) or \
           (settings.AWS_SECRET_ACCESS_KEY and not settings.AWS_ACCESS_KEY_ID):
            raise RuntimeError("Provide both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY together, or omit both to use the default credential chain.")

        # If explicit keys weren't provided, ensure some credentials are available via the default chain
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
            session = boto3.session.Session()
            if session.get_credentials() is None:
                raise RuntimeError(
                    "AWS credentials not found. Configure an IAM role (recommended) or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
                )

        # Build client after validation; catch initialization errors
        s3_client_kwargs = {
            'region_name': settings.AWS_REGION
        }
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            s3_client_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
            s3_client_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
        try:
            self.s3_client = boto3.client('s3', **s3_client_kwargs)
        except Exception as exc:
            logger.exception("Failed to initialize S3 client")
            raise RuntimeError("Failed to initialize S3 client. Verify AWS configuration and network connectivity.") from exc

    def _get_url_hash(self, url: str) -> str:
        """Generate MD5 hash from URL for caching"""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_s3_object_exists(self, s3_key: str) -> bool:
        """Check if object exists in S3"""
        try:
            self.s3_client.head_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
            return True
        except ClientError as e:
            # Only treat "not found" as False; bubble up other errors
            resp = getattr(e, "response", {}) or {}
            status_code = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = (resp.get("Error", {}) or {}).get("Code")
            not_found_codes = {"404", "NoSuchKey", "NotFound"}
            if status_code == 404 or (error_code in not_found_codes):
                return False
            logger.exception(f"S3 head_object failed for key={s3_key}")
            raise

    def _get_s3_url(self, s3_key: str) -> str:
        """
        Generate a public S3 URL for the given object key.
        Note: This relies on objects being publicly readable (bucket policy/ACL) or fronted by a public distribution.
        """
        # Encode each path segment to produce a safe URL path without encoding slashes
        encoded_key = "/".join(quote(segment, safe="") for segment in s3_key.split("/"))
        return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{encoded_key}"

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

            return self._get_s3_url(s3_key)

        except ClientError:
            logger.exception("S3 upload error")
            return None
        except Exception:
            logger.exception("Image processing error")
            return None

    async def _download_and_remove_bg(self, image_url: str) -> Image.Image:
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            input_image = Image.open(BytesIO(response.content))

            output_image = remove(input_image)

            return output_image

        except Exception:
            logger.exception(f"Background removal error for {image_url}")
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
                logger.info(f"Cache hit! Returning existing image for: {image_url}")
                return self._get_s3_url(s3_key)

            # Cache miss - process image
            logger.info(f"Cache miss. Processing new image: {image_url}")
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

        except ClientError:
            logger.exception("S3 upload error")
            return None
        except Exception:
            logger.exception("Remove background error")
            return None
