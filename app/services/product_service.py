"""
상품 조회 서비스
퀴즈 답변 기반으로 DB에서 상품을 필터링하여 조회
"""

import logging
from typing import Dict, List

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Brand, Product
from app.services.style_mapping import get_mapped_styles, get_shoes_styles

logger = logging.getLogger(__name__)


class ProductService:
    """상품 조회 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_products_by_quiz_answers(
        self, occasion: str, style: str, budget: int, limit_per_category: int = 10
    ) -> Dict[str, List[Product]]:
        """
        퀴즈 답변 기반으로 상품을 카테고리별로 조회합니다.

        Args:
            occasion: 상황 (work, date, meeting, outdoor)
            style: 스타일 (clean, comfortable, stylish, hip)
            budget: 예산 (100000, 300000, 500000, unlimited)
            limit_per_category: 카테고리당 최대 상품 수

        Returns:
            카테고리별 상품 딕셔너리 {"TOP": [Product, ...], "BOTTOM": [...], ...}
        """
        # 1. 스타일 매핑
        mapped_styles = get_mapped_styles(occasion, style)
        logger.info(f"Mapped styles for {occasion} + {style}: {mapped_styles}")

        # 2. 신발 스타일 매핑 (신발은 별도 로직)
        shoes_styles = get_shoes_styles(occasion, style)
        logger.info(f"Mapped shoes styles for {occasion} + {style}: {shoes_styles}")

        # 3. 예산 처리
        max_price = self._parse_budget(budget)

        # 4. 카테고리별로 상품 조회
        categories = ["TOP", "BOTTOM", "OUTER", "SHOES"]
        result = {}

        for category in categories:
            # SHOES는 신발 스타일 사용, 나머지는 의류 스타일 사용
            category_styles = shoes_styles if category == "SHOES" else mapped_styles

            products = await self._get_products_by_category(
                category=category,
                styles=category_styles,
                max_price=max_price,
                limit=limit_per_category,
            )
            result[category] = products
            logger.info(f"Found {len(products)} products for category {category}")

        return result

    def _parse_budget(self, budget: int) -> int:
        """
        예산을 정수로 변환합니다.
        unlimited는 매우 큰 값으로 처리

        Args:
            budget: 예산 (100000, 300000, 500000, unlimited)

        Returns:
            최대 가격 (원)
        """
        if isinstance(budget, str) and budget.lower() == "unlimited":
            return 10_000_000  # 1000만원 (무제한)

        try:
            return int(budget)
        except (ValueError, TypeError):
            logger.warning(f"Invalid budget value: {budget}, using default 500000")
            return 500_000  # 기본값 50만원

    async def _get_products_by_category(
        self, category: str, styles: List[str], max_price: int, limit: int
    ) -> List[Product]:
        """
        특정 카테고리의 상품을 스타일과 가격으로 필터링하여 조회합니다.

        Args:
            category: 카테고리 (TOP, BOTTOM, OUTER, SHOES)
            styles: 스타일 리스트 (예: ["minimalist", "cityboy"])
            max_price: 최대 가격
            limit: 최대 조회 개수

        Returns:
            Product 리스트
        """
        # 기본 조건
        base_conditions = [
            Product.category == category,
            Product.is_active.is_(True),
            Product.deleted_at.is_(None),
            Product.removed_background_image_url.isnot(None),  # 누끼 이미지 필수
            Product.price <= max_price,
        ]

        # ACCESSORY만 스타일 필터 제외 (모든 스타일에 매칭)
        # SHOES는 신발 스타일 필터 사용
        if category != "ACCESSORY":
            base_conditions.append(
                or_(Product.primary_style.in_(styles), Brand.primary_style.in_(styles))
            )

        # 쿼리 구성 (brand relationship eager load)
        stmt = (
            select(Product)
            .join(Brand, Product.brand_id == Brand.id)
            .options(selectinload(Product.brand))  # Brand eager load
            .where(and_(*base_conditions))
            .order_by(Product.id.asc())  # 일단 ID 순, 나중에 인기순으로 변경 가능
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        products = result.scalars().all()

        return list(products)

    async def get_product_by_id(self, product_id: int) -> Product | None:
        """
        ID로 상품을 조회합니다.

        Args:
            product_id: 상품 ID

        Returns:
            Product 또는 None
        """
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
