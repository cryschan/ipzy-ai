# 백엔드 연동 가이드 & TODO

> 백엔드 PR #22 기반 통합 문서

---

## 📡 백엔드 → AI 서버 통신

### 엔드포인트
```
POST /api/v1/recommend
```

### 요청 구조
```json
{
  "sessionId": "uuid",
  "answers": [
    {
      "questionId": 1,
      "questionText": "선호 스타일은?",
      "selectedOptions": ["캐주얼", "미니멀"]
    }
  ],
  "availableProducts": [
    {
      "productId": "prod_001",
      "name": "옥스포드 셔츠",
      "category": "TOP",
      "brand": "무신사",
      "price": 49000,
      "imageUrl": "https://...",
      "linkUrl": "https://...",
      "description": "...",
      "tags": ["캐주얼"]
    }
  ]
}
```

### 응답 구조
```json
{
  "recommendedOutfits": [
    {
      "displayOrder": 1,
      "occasion": "출근",
      "season": "봄",
      "style": "캐주얼",
      "reason": "심플한 출근룩",
      "totalPrice": 350000,
      "styleBoardUrl": null,
      "items": [
        {
          "productId": "prod_001",
          "category": "TOP",
          "name": "셔츠",
          "brand": "무신사",
          "price": 49000,
          "imageUrl": "https://...",
          "linkUrl": "https://..."
        }
      ]
    }
  ]
}
```

### 카테고리 값 (대문자 필수)
- `TOP` - 상의
- `BOTTOM` - 하의
- `SHOES` - 신발
- `OUTER` - 아우터
- `ACCESSORY` - 액세서리

---

## ✅ 확정 사항

- **유저 예산**: 퀴즈 답변에 포함
- **상품 정보**: 백엔드가 `availableProducts`로 전달
- **합성 이미지**: 우선 대기 (`styleBoardUrl = None`)

---

## 📋 TODO

### 백엔드 작업 (당신 담당)
- [ ] `ProductDto.java` 추가
- [ ] `RecommendationRequest.java`에 `availableProducts` 필드 추가
- [ ] `RecommendationService`에서 상품 필터링 로직 추가
  - 퀴즈에서 예산 추출
  - DB에서 상품 조회 (price, category 필터)
- [ ] `ProductRepository.findByPriceRangeAndCategories()` 추가
- [ ] 테스트 (preview-request로 확인)

### AI 서버 작업
- [ ] Pydantic 스키마 작성 (`app/schemas/backend.py`)
  - `ProductDto`
  - `QuizAnswer`
  - `RecommendationRequest`
  - `RecommendedItem`
  - `OutfitRecommendation`
  - `RecommendationResponse`
- [ ] `/api/v1/recommend` 엔드포인트 구현
  - API Key 인증
  - 빈 상품 체크
- [ ] 추천 서비스 구현 (`app/services/recommendation_service.py`)
  - 퀴즈 분석
  - Gemini로 추천 생성
  - 응답 포맷팅
- [ ] 통합 테스트

### 나중에 (보류)
- [ ] 배치 분석 엔드포인트 (`/api/v1/analyze/batch`)
- [ ] 합성 이미지 생성 통합
- [ ] 피드백 저장 (`/api/v1/feedback/like`)

---

## ⚠️ 주의사항

### 백엔드
1. ProductDto.from() null 처리
2. 상품 최대 100개 제한
3. 예산 파싱 로직 견고하게

### AI 서버
1. `availableProducts` 빈 배열 체크
2. 카테고리 대문자 유지
3. `styleBoardUrl`은 일단 None
4. 에러 응답 명확하게 (4xx/5xx + JSON)

---

## 🔧 백엔드 코드 예시

### ProductDto.java
```java
@Getter
@Builder
public class ProductDto {
    private String productId;
    private String name;
    private String category;
    private String brand;
    private Integer price;
    private String imageUrl;
    private String linkUrl;
    private String description;
    private List<String> tags;

    public static ProductDto from(Product product) {
        return ProductDto.builder()
            .productId(product.getId().toString())
            .name(product.getName())
            .category(product.getCategory().name())
            .brand(product.getBrand())
            .price(product.getPrice())
            .imageUrl(product.getImageUrl())
            .linkUrl(product.getLinkUrl())
            .description(product.getDescription())
            .tags(product.getTags())
            .build();
    }
}
```

### RecommendationService 수정
```java
// 상품 조회 추가
BudgetInfo budget = extractBudgetFromQuiz(answers);

List<Product> products = productRepository
    .findByPriceRangeAndCategories(
        budget.getMin(),
        budget.getMax(),
        List.of("TOP", "BOTTOM", "SHOES", "OUTER")
    );

List<ProductDto> productDtos = products.stream()
    .map(ProductDto::from)
    .limit(100)
    .collect(Collectors.toList());

RecommendationRequest request = RecommendationRequest.builder()
    .sessionId(sessionId.toString())
    .answers(answers)
    .availableProducts(productDtos)  // ← 추가
    .build();
```

---

## 🐍 AI 서버 코드 예시

### 스키마 (app/schemas/backend.py)
```python
from pydantic import BaseModel
from typing import List, Optional

class ProductDto(BaseModel):
    productId: str
    name: str
    category: str
    brand: str
    price: int
    imageUrl: str
    linkUrl: str
    description: Optional[str] = None
    tags: List[str] = []

class QuizAnswer(BaseModel):
    questionId: int
    questionText: str
    selectedOptions: List[str]

class RecommendationRequest(BaseModel):
    sessionId: str
    answers: List[QuizAnswer]
    availableProducts: List[ProductDto]

class RecommendedItem(BaseModel):
    productId: str
    category: str
    name: str
    brand: str
    price: int
    imageUrl: str
    linkUrl: str

class OutfitRecommendation(BaseModel):
    displayOrder: int
    occasion: str
    season: str
    style: str
    reason: str
    totalPrice: int
    styleBoardUrl: Optional[str] = None
    items: List[RecommendedItem]

class RecommendationResponse(BaseModel):
    recommendedOutfits: List[OutfitRecommendation]
```

### 엔드포인트 (app/api/v1/endpoints/recommendations.py)
```python
from fastapi import APIRouter, Header, HTTPException
from app.schemas.backend import RecommendationRequest, RecommendationResponse
from app.core.config import settings

router = APIRouter()

@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(
    request: RecommendationRequest,
    x_api_key: str = Header(...)
):
    # API Key 검증
    if x_api_key != settings.BACKEND_API_KEY:
        raise HTTPException(403, "Invalid API Key")

    # 빈 상품 체크
    if not request.availableProducts:
        raise HTTPException(400, "No products available")

    # TODO: 추천 로직 구현

    return RecommendationResponse(recommendedOutfits=[])
```

---

## 🧪 테스트

### 백엔드 preview 확인
```bash
curl http://localhost:8080/api/recommendations/sessions/{id}/preview-request
```

### AI 서버 직접 호출
```bash
curl -X POST http://localhost:8000/api/v1/recommend \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test",
    "answers": [],
    "availableProducts": []
  }'
```
