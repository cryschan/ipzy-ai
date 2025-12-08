from openai import AsyncOpenAI
from typing import List
import json
import uuid
from app.core.config import settings
from app.schemas.recommendation import RecommendationRequest, CoordinationSet, ProductItem
from app.schemas.product import Product


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def create_coordination_sets(
        self,
        products: List[Product],
        request: RecommendationRequest
    ) -> List[CoordinationSet]:
        products_json = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "brand": p.brand,
                "image_url": p.image_url,
                "description": p.description
            }
            for p in products
        ]

        prompt = f"""
당신은 패션 스타일리스트입니다. 아래 조건에 맞는 코디 세트를 {settings.MAX_RECOMMENDATIONS}개 추천해주세요.

조건:
- 장소: {request.location}
- 스타일: {request.style}
- 체형: {request.body_type}
- 성별: {request.gender}
- 예산: {request.budget_min:,}원 ~ {request.budget_max:,}원
- 추가 선호사항: {request.additional_preferences or '없음'}

사용 가능한 상품:
{json.dumps(products_json, ensure_ascii=False, indent=2)}

응답 형식 (JSON):
{{
  "coordination_sets": [
    {{
      "products": ["product_id1", "product_id2", ...],
      "reasoning": "이 조합을 추천하는 이유"
    }}
  ]
}}

규칙:
1. 각 코디 세트는 상의, 하의, 신발을 포함해야 합니다 (외투, 액세서리는 선택)
2. 총 가격이 예산 범위 내에 있어야 합니다
3. 장소와 스타일에 적합해야 합니다
4. 체형에 어울리는 아이템을 선택해야 합니다
5. 색상과 디자인이 조화로워야 합니다
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "당신은 전문 패션 스타일리스트입니다."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            result = json.loads(response.choices[0].message.content)
            coordination_sets = []

            product_dict = {p.product_id: p for p in products}

            for coord_data in result.get('coordination_sets', [])[:settings.MAX_RECOMMENDATIONS]:
                selected_products = []
                total_price = 0

                for product_id in coord_data.get('products', []):
                    if product_id in product_dict:
                        product = product_dict[product_id]
                        selected_products.append(ProductItem(
                            product_id=product.product_id,
                            name=product.name,
                            category=product.category,
                            price=product.price,
                            brand=product.brand,
                            image_url=product.image_url,
                            description=product.description
                        ))
                        total_price += product.price

                if selected_products:
                    coordination_sets.append(CoordinationSet(
                        set_id=str(uuid.uuid4()),
                        products=selected_products,
                        total_price=total_price,
                        reasoning=coord_data.get('reasoning', ''),
                        composite_image_url=None
                    ))

            return coordination_sets

        except Exception as e:
            print(f"LLM service error: {str(e)}")

            fallback_set = self._create_fallback_coordination(products, request)
            return [fallback_set] if fallback_set else []

    def _create_fallback_coordination(
        self,
        products: List[Product],
        request: RecommendationRequest
    ) -> CoordinationSet:
        filtered_products = [
            p for p in products
            if request.budget_min <= p.price <= request.budget_max
        ]

        if not filtered_products:
            return None

        categories = {}
        for product in filtered_products:
            if product.category not in categories:
                categories[product.category] = []
            categories[product.category].append(product)

        selected_products = []
        total_price = 0

        for category in ['top', 'bottom', 'shoes']:
            if category in categories and categories[category]:
                product = categories[category][0]
                selected_products.append(ProductItem(
                    product_id=product.product_id,
                    name=product.name,
                    category=product.category,
                    price=product.price,
                    brand=product.brand,
                    image_url=product.image_url,
                    description=product.description
                ))
                total_price += product.price

        if selected_products:
            return CoordinationSet(
                set_id=str(uuid.uuid4()),
                products=selected_products,
                total_price=total_price,
                reasoning="기본 추천 세트입니다.",
                composite_image_url=None
            )

        return None
