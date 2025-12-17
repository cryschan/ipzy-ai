"""
퀴즈 기반 추천 서비스
전체 추천 플로우를 통합 관리
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import HTTPException
from app.schemas.quiz_recommendation import (
    QuizRecommendationRequest,
    QuizRecommendationResponse,
    OutfitRecommendationDto,
    OutfitResultDto,
    RecommendedItemDto
)
from app.services.product_service import ProductService
from app.services.llm_coordinator import LLMCoordinatorService
from app.services.style_mapping import OCCASION_KR, STYLE_KR
from app.models.product import Product
import logging

logger = logging.getLogger(__name__)


class QuizRecommendationService:
    """퀴즈 기반 추천 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
        self.llm_service = LLMCoordinatorService()

    async def generate_recommendations(
        self,
        request: QuizRecommendationRequest
    ) -> QuizRecommendationResponse:
        """
        퀴즈 답변을 기반으로 코디를 추천합니다.

        Args:
            request: 퀴즈 답변 요청

        Returns:
            코디 추천 응답
        """
        logger.info(f"Generating recommendations for session {request.sessionId}")

        # 1. 퀴즈 답변 파싱
        quiz_data = self._parse_quiz_answers(request.answers)
        logger.info(f"Parsed quiz data: {quiz_data}")

        # 2. DB에서 상품 후보 조회
        candidates = await self.product_service.get_products_by_quiz_answers(
            occasion=quiz_data["occasion"],
            style=quiz_data["style"],
            budget=quiz_data["budget"],
            limit_per_category=10
        )

        # 후보가 없으면 404 에러
        total_candidates = sum(len(products) for products in candidates.values())
        if total_candidates == 0:
            logger.error("No product candidates found")
            raise HTTPException(
                status_code=404,
                detail="해당 조건에 맞는 상품이 없습니다. 다른 옵션을 선택해주세요."
            )

        logger.info(f"Found {total_candidates} total product candidates")

        # 3. LLM으로 최적 조합 선택
        selected_outfits = await self.llm_service.select_outfit_combinations(
            candidates=candidates,
            occasion=quiz_data["occasion"],
            style=quiz_data["style"],
            body_type=quiz_data["body_type"],
            budget=quiz_data["budget"],
            num_outfits=3  # 3개 추천
        )

        logger.info(f"LLM selected {len(selected_outfits)} outfits")

        # 4. DTO로 변환
        outfit_dtos = []
        for i, outfit in enumerate(selected_outfits, 1):
            outfit_dto = self._convert_to_outfit_dto(
                outfit=outfit,
                display_order=i,
                occasion=quiz_data["occasion"],
                style=quiz_data["style"]
            )
            outfit_dtos.append(outfit_dto)

        return QuizRecommendationResponse(recommended_outfits=outfit_dtos)

    def _parse_quiz_answers(self, answers: List) -> dict:
        """
        퀴즈 답변을 파싱하여 필요한 정보를 추출합니다.

        Args:
            answers: QuizAnswerDto 리스트

        Returns:
            파싱된 데이터 {"occasion": "date", "style": "stylish", ...}
        """
        result = {
            "occasion": "outdoor",  # 기본값
            "style": "comfortable",  # 기본값
            "body_type": "none",  # 기본값
            "budget": 300000  # 기본값 30만원
        }

        for answer in answers:
            question_text = answer.questionText
            selected = answer.selectedOptions[0] if answer.selectedOptions else None

            if not selected:
                continue

            # 질문 텍스트로 분류
            if "어디" in question_text or "가요" in question_text:
                # 1번 질문: 상황
                result["occasion"] = selected
            elif "보이고" in question_text or "어떻게" in question_text:
                # 2번 질문: 스타일
                result["style"] = selected
            elif "체형" in question_text:
                # 3번 질문: 체형
                result["body_type"] = selected
            elif "예산" in question_text:
                # 4번 질문: 예산
                try:
                    result["budget"] = int(selected)
                except (ValueError, TypeError):
                    result["budget"] = 300000  # 기본값

        return result

    def _convert_to_outfit_dto(
        self,
        outfit: dict,
        display_order: int,
        occasion: str,
        style: str
    ) -> OutfitRecommendationDto:
        """
        선택된 코디를 OutfitRecommendationDto로 변환합니다 (PR #30 신규 구조).

        Args:
            outfit: {"reason": "...", "items": {"TOP": Product, ...}}
            display_order: 표시 순서
            occasion: 상황
            style: 스타일

        Returns:
            OutfitRecommendationDto (중첩 구조)
        """
        items_dto = []
        total_price = 0

        # 카테고리 순서 정의
        category_order = ["TOP", "BOTTOM", "OUTER", "SHOES", "ACCESSORY"]

        for category in category_order:
            product = outfit["items"].get(category)
            if product:
                item_dto = self._product_to_item_dto(product)
                items_dto.append(item_dto)
                total_price += product.price

        # 한글 변환
        occasion_kr = OCCASION_KR.get(occasion, occasion)
        style_kr = self._get_style_kr(style)

        # OutfitResultDto 생성 (중첩 구조)
        result = OutfitResultDto(
            success=True,
            message="추천 완료",
            composite_image_url=None,  # 이미지 합성은 나중에 추가
            image_width=None,
            image_height=None,
            total_price=total_price,
            items=items_dto
        )

        # OutfitRecommendationDto 생성 (최상위)
        return OutfitRecommendationDto(
            displayOrder=display_order,
            occasion=occasion_kr,
            season="all",  # 계절은 일단 all로 고정
            style=style_kr,
            reason=outfit["reason"],
            status="completed",  # 동기 처리이므로 항상 completed
            job_id=None,         # 동기 처리이므로 None
            created_at=None,     # 동기 처리이므로 None
            completed_at=None,   # 동기 처리이므로 None
            result=result,
            error=None
        )

    def _product_to_item_dto(self, product: Product) -> RecommendedItemDto:
        """
        Product 모델을 RecommendedItemDto로 변환합니다 (PR #30 신규 구조).

        Args:
            product: Product 모델

        Returns:
            RecommendedItemDto
        """
        return RecommendedItemDto(
            product_id=product.id,
            category=product.category,
            name=product.name,
            brand=product.brand.name if product.brand else "Unknown",
            price=product.price,
            image_url=product.removed_background_image_url,
            link_url=product.purchase_url if product.purchase_url else "",
            position=None  # 이미지 합성 후 좌표 정보 추가 예정
        )

    def _get_style_kr(self, style: str) -> str:
        """스타일 영문을 한글로 변환"""
        style_kr_map = {
            "clean": "깔끔",
            "comfortable": "편안",
            "stylish": "세련",
            "hip": "힙"
        }
        return style_kr_map.get(style.lower(), style)
