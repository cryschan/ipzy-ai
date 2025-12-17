"""
LLM 기반 코디 조합 선택 서비스
상품 후보들 중에서 최적의 조합을 LLM이 선택합니다.
"""

from typing import List, Dict
from fastapi import HTTPException
from app.models.product import Product
from app.services.style_mapping import format_for_llm
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class LLMCoordinatorService:
    """LLM 기반 코디 조합 선택 서비스"""

    def __init__(self):
        # OpenAI GPT-3.5-turbo 사용 (가성비 픽)
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"  # 가성비 좋은 모델
        logger.info(f"LLM Coordinator initialized with model: {self.model}")

    async def select_outfit_combinations(
        self,
        candidates: Dict[str, List[Product]],
        occasion: str,
        style: str,
        body_type: str,
        budget: int,
        num_outfits: int = 3
    ) -> List[Dict]:
        """
        상품 후보들 중에서 LLM이 최적의 코디 조합을 선택합니다.

        Args:
            candidates: 카테고리별 상품 후보 {"TOP": [Product, ...], ...}
            occasion: 상황
            style: 스타일
            body_type: 체형
            budget: 예산
            num_outfits: 추천할 코디 개수 (기본 3개)

        Returns:
            선택된 코디 리스트 [{"TOP": Product, "BOTTOM": Product, ...}, ...]
        """
        # 1. 프롬프트 생성
        prompt = self._create_selection_prompt(
            candidates, occasion, style, body_type, budget, num_outfits
        )

        # 2. LLM 호출 (OpenAI GPT-3.5-turbo)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            result_text = response.choices[0].message.content

            logger.info(f"LLM response received: {len(result_text)} characters")

            # 3. 응답 파싱
            selected_outfits = self._parse_llm_response(result_text, candidates)

            return selected_outfits

        except Exception as e:
            logger.exception("LLM selection failed")
            # LLM 실패 시 503 에러
            raise HTTPException(
                status_code=503,
                detail="AI 추천 서비스 일시 장애. 잠시 후 다시 시도해주세요."
            ) from e

    def _create_selection_prompt(
        self,
        candidates: Dict[str, List[Product]],
        occasion: str,
        style: str,
        body_type: str,
        budget: int,
        num_outfits: int
    ) -> str:
        """LLM에게 보낼 프롬프트를 생성합니다."""

        # 사용자 컨텍스트
        user_context = format_for_llm(occasion, style, body_type)

        # 예산 정보
        budget_str = "무제한" if budget >= 10_000_000 else f"{budget:,}원"

        # 상품 후보 포맷팅
        candidates_text = ""
        for category, products in candidates.items():
            candidates_text += f"\n## {category} 후보:\n"
            for i, product in enumerate(products, 1):
                candidates_text += (
                    f"{i}. [{product.id}] {product.name} - {product.brand.name if product.brand else 'Unknown'} "
                    f"(가격: {product.price:,}원, 스타일: {product.primary_style})\n"
                )

        prompt = f"""당신은 패션 스타일리스트입니다. 사용자의 요구사항에 맞는 최적의 코디 조합을 {num_outfits}개 추천해주세요.

## 사용자 정보:
{user_context}
예산: {budget_str}

## 상품 후보:
{candidates_text}

## 요구사항:
1. 총 {num_outfits}개의 서로 다른 코디 조합을 추천하세요.
2. 각 코디는 TOP, BOTTOM, OUTER, SHOES 카테고리에서 각각 1개씩 선택하세요.
   - 후보가 없는 카테고리는 선택하지 마세요.
3. 각 코디의 총 가격이 예산({budget_str})을 초과하지 않도록 하세요.
4. 색상 조화, 스타일 통일성을 고려하세요.
5. 체형 고민을 고려하여 적합한 핏을 선택하세요.
6. {num_outfits}개의 코디는 서로 다양한 느낌을 주도록 구성하세요.

## 응답 형식 (JSON):
```json
[
  {{
    "outfit_number": 1,
    "reason": "추천 이유 (한글, 1-2문장)",
    "selected_items": {{
      "TOP": <상품ID>,
      "BOTTOM": <상품ID>,
      "OUTER": <상품ID>,
      "SHOES": <상품ID>
    }}
  }},
  ...
]
```

**반드시 위 JSON 형식으로만 응답하세요. 다른 설명은 추가하지 마세요.**
"""
        return prompt

    def _parse_llm_response(
        self,
        response_text: str,
        candidates: Dict[str, List[Product]]
    ) -> List[Dict]:
        """
        LLM 응답을 파싱하여 선택된 상품 조합을 반환합니다.

        Args:
            response_text: LLM 응답 텍스트 (JSON)
            candidates: 원본 상품 후보

        Returns:
            선택된 코디 리스트
        """
        try:
            # JSON 추출 (```json ... ``` 형식일 수 있음)
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()

            # JSON 파싱
            outfits_data = json.loads(json_text)

            # 상품 ID → Product 객체 매핑
            id_to_product = {}
            for category, products in candidates.items():
                for product in products:
                    id_to_product[product.id] = product

            # 결과 구성
            selected_outfits = []
            for outfit_data in outfits_data:
                outfit = {
                    "reason": outfit_data.get("reason", "추천 코디입니다."),
                    "items": {}
                }

                selected_items = outfit_data.get("selected_items", {})
                for category, product_id in selected_items.items():
                    if product_id in id_to_product:
                        outfit["items"][category] = id_to_product[product_id]
                    else:
                        logger.warning(f"Product ID {product_id} not found in candidates")

                # 최소 1개 이상 아이템이 있으면 추가
                if outfit["items"]:
                    selected_outfits.append(outfit)

            logger.info(f"Parsed {len(selected_outfits)} outfits from LLM response")
            return selected_outfits

        except Exception as e:
            logger.exception("Failed to parse LLM response")
            logger.debug(f"Response text: {response_text}")
            raise

    def _fallback_selection(
        self,
        candidates: Dict[str, List[Product]],
        num_outfits: int
    ) -> List[Dict]:
        """
        LLM 실패 시 폴백: 각 카테고리의 첫 번째 상품으로 조합

        Args:
            candidates: 카테고리별 상품 후보
            num_outfits: 추천할 코디 개수

        Returns:
            폴백 코디 리스트
        """
        logger.warning("Using fallback selection (first items from each category)")

        outfits = []
        for i in range(num_outfits):
            outfit = {
                "reason": f"추천 코디 {i + 1}번입니다.",
                "items": {}
            }

            for category, products in candidates.items():
                if products and i < len(products):
                    outfit["items"][category] = products[i]
                elif products:
                    outfit["items"][category] = products[0]

            if outfit["items"]:
                outfits.append(outfit)

        return outfits
