from PIL import Image
from rembg import remove
from io import BytesIO
from typing import List
import uuid
import hashlib
import boto3
import httpx
from urllib.parse import quote
from botocore.exceptions import ClientError
from app.core.config import settings
from app.schemas.recommendation import ProductItem
from app.schemas.image import CompositeImageItem
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
            resp = getattr(e, "response", {}) or {}
            status_code = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = (resp.get("Error", {}) or {}).get("Code")

            # Treat "not found" and "forbidden" as object doesn't exist
            # 403/Forbidden can occur when we don't have permission to check, or object doesn't exist
            not_found_codes = {"404", "NoSuchKey", "NotFound", "403", "Forbidden"}
            if status_code in [404, 403] or (error_code in not_found_codes):
                if status_code == 403:
                    logger.warning(f"S3 permission denied for key={s3_key}. Treating as cache miss.")
                return False

            # Other errors should still be raised
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

    async def _download_image(self, image_url: str) -> Image.Image:
        """Download image from URL without background removal"""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                content_bytes = response.content

            image = Image.open(BytesIO(content_bytes))
            return image

        except Exception:
            logger.exception(f"Failed to download image from {image_url}")
            return None

    async def create_composite_image(self, items: List[CompositeImageItem]) -> dict:
        try:
            processed_images = []
            item_map = {}  # Map category to original item data

            # Enforce uniqueness: validate duplicate categories before building map
            categories_upper = [it.category.upper() for it in items]
            category_counts: dict[str, int] = {}
            for cat in categories_upper:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            duplicates = [cat for cat, count in category_counts.items() if count > 1]
            if duplicates:
                logger.error(f"Duplicate categories provided: {', '.join(duplicates)}. Each category must be unique.")
                return None

            for item in items:
                # Download from nobg_image_url (already background-removed)
                img = await self._download_image(item.nobg_image_url)
                if img:
                    processed_images.append({
                        'image': img,
                        'category': item.category,
                        'product_id': item.product_id
                    })
                    # Store original item data for later
                    item_map[item.category.upper()] = item
                else:
                    logger.warning(f"Failed to download image for product {item.product_id}")

            if not processed_images:
                logger.error("No images were successfully downloaded")
                return None

            composite, positions = self._compose_images(processed_images)

            filename = f"{uuid.uuid4()}.png"
            s3_key = f"{settings.S3_COMPOSITE_PREFIX}/{filename}"

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

            composite_url = self._get_s3_url(s3_key)

            # Combine position data with original item data
            items_with_positions = []
            total_price = 0

            for pos in positions:
                category = pos['category'].upper()
                if category in item_map:
                    original_item = item_map[category]
                    items_with_positions.append({
                        'product_id': original_item.product_id,
                        'category': original_item.category,
                        'name': original_item.name,
                        'brand': original_item.brand,
                        'price': original_item.price,
                        'link_url': original_item.link_url,
                        'position': {
                            'x': pos['x'],
                            'y': pos['y'],
                            'width': pos['width'],
                            'height': pos['height']
                        }
                    })
                    # Add to total price
                    total_price += original_item.price

            return {
                'composite_url': composite_url,
                'items': items_with_positions,
                'total_price': total_price,
                'image_width': 1200,
                'image_height': 1600
            }

        except ClientError:
            logger.exception("S3 upload error")
            return None
        except Exception:
            logger.exception("Image processing error")
            return None

    async def _download_and_remove_bg(self, image_url: str) -> Image.Image:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                content_bytes = response.content

            input_image = Image.open(BytesIO(content_bytes))

            output_image = remove(input_image)

            return output_image

        except Exception:
            logger.exception(f"Background removal error for {image_url}")
            return None

    def _compose_images(self, processed_images: List[dict]) -> tuple[Image.Image, List[dict]]:
        canvas_width = 1200
        canvas_height = 1600
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))

        # 2-column layout positions
        # LEFT: TOP (top), BOTTOM (bottom)
        # RIGHT: OUTER (top), ACCESSORY (middle), SHOES (bottom)
        category_positions = {
            'top': {'x': 'left', 'y': 100, 'scale': 0.4},           # 왼쪽 상단
            'outer': {'x': 'right', 'y': 100, 'scale': 0.4},        # 오른쪽 상단
            'bottom': {'x': 'left', 'y': 800, 'scale': 0.4},        # 왼쪽 하단
            'accessory': {'x': 'right', 'y': 600, 'scale': 0.3},    # 오른쪽 중간
            'shoes': {'x': 'right', 'y': 1100, 'scale': 0.35}       # 오른쪽 하단
        }

        positions = []  # Track positions for each item

        for item in processed_images:
            img = item['image']
            category = item['category'].lower()

            if category not in category_positions:
                category = 'accessory'

            position_info = category_positions[category]

            img_width, img_height = img.size
            scale = position_info['scale']
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Calculate x position based on left/right alignment
            if position_info['x'] == 'left':
                # Left column: align to left quarter of canvas
                x_position = (canvas_width // 4) - (new_width // 2)
            else:  # 'right'
                # Right column: align to right three-quarters of canvas
                x_position = (canvas_width * 3 // 4) - (new_width // 2)

            y_position = position_info['y']

            if img_resized.mode == 'RGBA':
                canvas.paste(img_resized, (x_position, y_position), img_resized)
            else:
                canvas.paste(img_resized, (x_position, y_position))

            # Store position data
            positions.append({
                'category': item['category'],
                'product_id': item.get('product_id'),
                'x': x_position,
                'y': y_position,
                'width': new_width,
                'height': new_height
            })

        return canvas, positions

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
