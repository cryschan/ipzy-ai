from PIL import Image
from rembg import remove
from io import BytesIO
from typing import List, Dict
import uuid
import hashlib
import boto3
import httpx
import asyncio
from urllib.parse import quote
from botocore.exceptions import ClientError
from app.core.config import settings
from app.schemas.recommendation import ProductItem
from app.schemas.image import CompositeImageItem
import logging

logger = logging.getLogger(__name__)


class ImageProcessingService:
    def __init__(self):
        # 애플리케이션 시작 시 설정 오류를 빠르게 드러내기 위한 사전 검증
        if not settings.AWS_S3_BUCKET:
            raise RuntimeError(
                "AWS_S3_BUCKET is not configured. Set it in your environment or .env."
            )

        if (settings.AWS_ACCESS_KEY_ID and not settings.AWS_SECRET_ACCESS_KEY) or (
            settings.AWS_SECRET_ACCESS_KEY and not settings.AWS_ACCESS_KEY_ID
        ):
            raise RuntimeError(
                "Provide both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY together, or omit both to use the default credential chain."
            )

        # 명시적 키가 없는 경우, 기본 자격 증명 체인에서 자격 증명이 제공되는지 확인
        if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
            session = boto3.session.Session()
            if session.get_credentials() is None:
                raise RuntimeError(
                    "AWS credentials not found. Configure an IAM role (recommended) or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
                )

        # 검증 후 클라이언트를 생성하고, 초기화 오류를 포착
        s3_client_kwargs = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            s3_client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            s3_client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        try:
            self.s3_client = boto3.client("s3", **s3_client_kwargs)
        except Exception as exc:
            logger.exception("Failed to initialize S3 client")
            raise RuntimeError(
                "Failed to initialize S3 client. Verify AWS configuration and network connectivity."
            ) from exc

    def _get_url_hash(self, url: str) -> str:
        """캐싱을 위해 URL에서 MD5 해시를 생성"""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_s3_object_exists(self, s3_key: str) -> bool:
        """S3에 객체가 존재하는지 확인"""
        try:
            self.s3_client.head_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
            return True
        except ClientError as e:
            resp = getattr(e, "response", {}) or {}
            status_code = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = (resp.get("Error", {}) or {}).get("Code")

            # "없음(404)" 또는 "금지(403)"는 객체가 없다고 간주
            # 403/Forbidden은 권한 부족 또는 객체 부재 시 발생할 수 있음
            not_found_codes = {"404", "NoSuchKey", "NotFound", "403", "Forbidden"}
            if status_code in [404, 403] or (error_code in not_found_codes):
                if status_code == 403:
                    logger.warning(
                        f"S3 permission denied for key={s3_key}. Treating as cache miss."
                    )  # 권한 거부 발생 시 캐시 미스로 처리
                return False

            # 그 외 오류는 그대로 예외 전파
            logger.exception(f"S3 head_object failed for key={s3_key}")
            raise

    def _get_s3_url(self, s3_key: str) -> str:
        """
        주어진 객체 키에 대한 공개 S3 URL을 생성합니다.
        참고: 버킷 정책/ACL로 공개 읽기 가능하거나, 퍼블릭 배포(예: CloudFront)로 노출되어 있어야 합니다.
        """
        # 각 경로 세그먼트를 인코딩하여, 슬래시는 유지한 안전한 URL 경로 생성
        encoded_key = "/".join(quote(segment, safe="") for segment in s3_key.split("/"))
        return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{encoded_key}"

    async def _download_image(self, image_url: str) -> Image.Image:
        """배경 제거 없이 URL에서 이미지를 다운로드"""
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
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
            item_map = {}  # 카테고리를 원본 아이템 데이터에 매핑

            # 중복 방지: 맵을 만들기 전에 카테고리 중복 여부 검증
            categories_upper = [it.category.upper() for it in items]
            category_counts: dict[str, int] = {}
            for cat in categories_upper:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            duplicates = [cat for cat, count in category_counts.items() if count > 1]
            if duplicates:
                logger.error(
                    f"Duplicate categories provided: {', '.join(duplicates)}. Each category must be unique."
                )
                return None

            for item in items:
                # nobg_image_url에서 다운로드 (이미 배경 제거됨)
                img = await self._download_image(item.nobg_image_url)
                if img:
                    processed_images.append(
                        {
                            "image": img,
                            "category": item.category,
                            "product_id": item.product_id,
                        }
                    )
                    # 이후 결합을 위해 원본 아이템 데이터 저장
                    item_map[item.category.upper()] = item
                else:
                    logger.warning(
                        f"Failed to download image for product {item.product_id}"
                    )

            if not processed_images:
                logger.error("No images were successfully downloaded")
                return None

            composite, positions = self._compose_images(processed_images)

            filename = f"{uuid.uuid4()}.png"
            s3_key = f"{settings.S3_COMPOSITE_PREFIX}/{filename}"

            buffer = BytesIO()
            composite.save(buffer, format="PNG")
            buffer.seek(0)

            self.s3_client.upload_fileobj(
                buffer,
                settings.AWS_S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
            )

            composite_url = self._get_s3_url(s3_key)

            # 위치 정보와 원본 아이템 데이터를 결합
            items_with_positions = []
            total_price = 0

            for pos in positions:
                category = pos["category"].upper()
                if category in item_map:
                    original_item = item_map[category]
                    items_with_positions.append(
                        {
                            "product_id": original_item.product_id,
                            "category": original_item.category,
                            "name": original_item.name,
                            "brand": original_item.brand,
                            "price": original_item.price,
                            "link_url": original_item.link_url,
                            "position": {
                                "x": pos["x"],
                                "y": pos["y"],
                                "width": pos["width"],
                                "height": pos["height"],
                            },
                        }
                    )
                    # Add to total price
                    total_price += original_item.price

            return {
                "composite_url": composite_url,
                "items": items_with_positions,
                "total_price": total_price,
                "image_width": 600,
                "image_height": 800,
            }

        except ClientError:
            logger.exception("S3 upload error")
            return None
        except Exception:
            logger.exception("Image processing error")
            return None

    async def _download_and_remove_bg(self, image_url: str) -> tuple[Image.Image, str]:
        """
        이미지를 다운로드한 뒤 배경을 제거합니다.
        반환값: (image, error_message) - 실패 시 image는 None, 성공 시 error_message는 None
        """
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                content_bytes = response.content

            input_image = Image.open(BytesIO(content_bytes))

            output_image = remove(input_image)

            return output_image, None

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
            logger.error(f"HTTP error for {image_url}: {error_msg}")
            return None, error_msg
        except httpx.TimeoutException:
            error_msg = "Request timeout (>60s)"
            logger.error(f"Timeout error for {image_url}")
            return None, error_msg
        except httpx.RequestError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"Network error for {image_url}: {error_msg}")
            return None, error_msg
        except Exception as e:
            error_msg = f"Image processing error: {str(e)}"
            logger.exception(f"Unexpected error for {image_url}")
            return None, error_msg

    def _compose_images(
        self, processed_images: List[dict]
    ) -> tuple[Image.Image, List[dict]]:
        canvas_width = 600
        canvas_height = 800
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        # 2열 레이아웃 배치 (3:4 비율)
        # 왼쪽(LEFT): TOP(상단), BOTTOM(하단) - 200×300px
        # 오른쪽(RIGHT): OUTER(상단), ACCESSORY(중간), SHOES(하단) - 180×270px
        category_positions = {
            "top": {"x": "left", "y": 50, "width": 200, "height": 300},  # 왼쪽 상단
            "outer": {
                "x": "right",
                "y": 40,
                "width": 180,
                "height": 270,
            },  # 오른쪽 상단
            "bottom": {"x": "left", "y": 450, "width": 200, "height": 300},  # 왼쪽 하단
            "accessory": {
                "x": "right",
                "y": 340,
                "width": 180,
                "height": 270,
            },  # 오른쪽 중간
            "shoes": {
                "x": "right",
                "y": 510,
                "width": 180,
                "height": 270,
            },  # 오른쪽 하단
        }

        positions = []  # 각 아이템의 위치 정보를 기록

        for item in processed_images:
            img = item["image"]
            category = item["category"].lower()

            if category not in category_positions:
                category = "accessory"

            position_info = category_positions[category]

            # 카테고리별 목표 크기
            target_width = position_info["width"]
            target_height = position_info["height"]

            # 원본 비율 유지하면서 목표 박스에 맞춰 리사이즈
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            # 목표 박스에 맞춰 리사이즈 (비율 유지)
            if aspect_ratio > target_width / target_height:
                # 가로가 더 긴 경우: 폭 기준으로 리사이즈
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                # 세로가 더 긴 경우: 높이 기준으로 리사이즈
                new_height = target_height
                new_width = int(target_height * aspect_ratio)

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 투명 배경의 목표 크기 캔버스 생성
            item_canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))

            # 중앙에 배치
            paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2

            if img_resized.mode == "RGBA":
                item_canvas.paste(img_resized, (paste_x, paste_y), img_resized)
            else:
                item_canvas.paste(img_resized, (paste_x, paste_y))

            # 좌/우 정렬에 따라 x 위치 계산
            if position_info["x"] == "left":
                # 왼쪽 열: 캔버스의 1/4 지점에 정렬
                x_position = (canvas_width // 4) - (target_width // 2)
            else:  # 'right'
                # 오른쪽 열: 캔버스의 3/4 지점에 정렬
                x_position = (canvas_width * 3 // 4) - (target_width // 2)

            y_position = position_info["y"]

            # 최종 캔버스에 배치
            canvas.paste(item_canvas, (x_position, y_position), item_canvas)

            # 위치 정보 저장
            positions.append(
                {
                    "category": item["category"],
                    "product_id": item.get("product_id"),
                    "x": x_position,
                    "y": y_position,
                    "width": target_width,
                    "height": target_height,
                }
            )

        return canvas, positions

    async def remove_background(self, image_url: str) -> tuple[str, str]:
        """
        이미지의 배경을 제거합니다.
        반환값: (nobg_url, error_message) - 실패 시 nobg_url은 None, 성공 시 error_message는 None
        """
        try:
            # 캐시를 위한 해시 기반 S3 키 생성
            url_hash = self._get_url_hash(image_url)
            s3_key = f"{settings.S3_IMAGE_PREFIX}/{url_hash}.png"

            # S3에 이미 존재하는지 확인
            if self._check_s3_object_exists(s3_key):
                logger.info(f"Cache hit! Returning existing image for: {image_url}")
                return self._get_s3_url(s3_key), None

            # 캐시 미스 - 새로 처리
            logger.info(f"Cache miss. Processing new image: {image_url}")
            output_image, error_msg = await self._download_and_remove_bg(image_url)

            if not output_image:
                return None, error_msg

            # 해시 기반 파일명으로 S3에 업로드
            buffer = BytesIO()
            output_image.save(buffer, format="PNG")
            buffer.seek(0)

            self.s3_client.upload_fileobj(
                buffer,
                settings.AWS_S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
            )

            return self._get_s3_url(s3_key), None

        except ClientError as e:
            error_msg = f"S3 upload error: {str(e)}"
            logger.exception("S3 upload error")
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception("Remove background error")
            return None, error_msg

    async def _remove_background_single(self, image_url: str) -> Dict:
        """
        단일 이미지 배경 제거 (배치 처리용 헬퍼 메서드)
        결과 정보를 담은 dict를 반환
        """
        try:
            nobg_url, error_msg = await self.remove_background(image_url)
            if nobg_url:
                return {
                    "original_url": image_url,
                    "nobg_image_url": nobg_url,
                    "success": True,
                    "error": None,
                }
            else:
                return {
                    "original_url": image_url,
                    "nobg_image_url": None,
                    "success": False,
                    "error": error_msg or "Unknown error",
                }
        except Exception as e:
            logger.exception(f"Unexpected error processing {image_url}")
            return {
                "original_url": image_url,
                "nobg_image_url": None,
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    async def remove_background_batch(self, image_urls: List[str]) -> List[Dict]:
        """
        여러 이미지의 배경을 동시에 제거합니다.
        asyncio.gather를 사용하여 병렬 처리합니다.

        Args:
            image_urls: 처리할 이미지 URL 목록 (최대 15개)

        Returns:
            각 이미지의 처리 결과 리스트
        """
        logger.info(f"Starting batch background removal for {len(image_urls)} images")

        # 모든 이미지를 병렬로 처리
        tasks = [self._remove_background_single(url) for url in image_urls]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r["success"])
        logger.info(
            f"Batch processing completed: {success_count}/{len(results)} succeeded"
        )

        return list(results)
