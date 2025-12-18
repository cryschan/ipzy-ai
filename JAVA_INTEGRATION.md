# Java 백엔드 통합 가이드

## Python API 엔드포인트 변경

**변경 사항:**

- ❌ 기존: `POST /api/v1/recommend`
- ✅ 신규: `POST /api/recommend`

**Java 쪽 수정 필요:**

- `PythonAiClient.java`의 `.uri("/api/v1/recommend")` → `.uri("/api/recommend")`로 변경

---

## 전체 호출 플로우

```
[프론트엔드]
    ↓
POST /api/recommendations/sessions/{sessionId}/generate (Java)
    ↓
[Java Backend - RecommendationController.generateRecommendation()]
    ↓
[Java Backend - RecommendationService.generateRecommendation()]
    ↓
[Java Backend - PythonAiClient.requestRecommendation()]
    ↓ HTTP 통신
POST /api/recommend (Python)  ← **여기서 Python 호출**
    ↓
[Python - QuizRecommendationService.generate_recommendations()]
    1. 퀴즈 답변 파싱 (occasion, style, body_type, budget)
    2. 스타일 매핑 (occasion + style → primary_style 리스트)
    3. DB 상품 조회 (PostgreSQL, 카테고리별 최대 10개)
    4. LLM (OpenAI GPT-3.5-turbo) 코디 선택 (3개)
    5. Java DTO 형식으로 응답
    ↓ HTTP 응답 (JSON)
[Java Backend - RecommendationService]
    - Recommendation 엔티티로 변환
    - DB 저장
    - 응답 반환
    ↓
[프론트엔드]
```

---

## Request DTO (Java → Python)

**Endpoint:** `POST /api/recommend`

**Request Body:**

```json
{
  "sessionId": 123,
  "answers": [
    {
      "questionId": 1,
      "questionText": "어디 가요?",
      "selectedOptions": ["date"]
    },
    {
      "questionId": 2,
      "questionText": "어떻게 보이고 싶어요?",
      "selectedOptions": ["stylish"]
    },
    {
      "questionId": 3,
      "questionText": "체형 고민?",
      "selectedOptions": ["none"]
    },
    {
      "questionId": 4,
      "questionText": "예산은?",
      "selectedOptions": ["300000"]
    }
  ]
}
```

**Java DTO:** `RecommendationRequest.java` (이미 구현됨)

---

## Response DTO (Python → Java)

**⚠️ PR #30 신규 구조 반영 (중첩 구조)**

**Response Body:**

```json
{
  "recommendedOutfits": [
    {
      "displayOrder": 1,
      "occasion": "데이트",
      "season": "all",
      "style": "세련",
      "reason": "데이트에 멋있게 보일 수 있는 깔끔한 코디입니다.",
      "status": "completed",
      "jobId": null,
      "createdAt": null,
      "completedAt": null,
      "result": {
        "success": true,
        "message": "추천 완료",
        "compositeImageUrl": null,
        "imageWidth": null,
        "imageHeight": null,
        "totalPrice": 250000,
        "items": [
          {
            "product_id": 1,
            "category": "TOP",
            "name": "오버핏 화이트 셔츠",
            "brand": "무신사 스탠다드",
            "price": 50000,
            "image_url": "https://s3.../removed-bg.png",
            "link_url": "https://musinsa.com/...",
            "position": null
          },
          {
            "product_id": 2,
            "category": "BOTTOM",
            "name": "슬림 블랙 슬랙스",
            "brand": "브랜드명",
            "price": 80000,
            "image_url": "https://s3.../removed-bg.png",
            "link_url": "https://musinsa.com/...",
            "position": null
          }
        ]
      },
      "error": null
    },
    {
      "displayOrder": 2,
      "occasion": "데이트",
      "season": "all",
      "style": "세련",
      "reason": "...",
      "status": "completed",
      "jobId": null,
      "createdAt": null,
      "completedAt": null,
      "result": {
        "success": true,
        "message": "추천 완료",
        "compositeImageUrl": null,
        "totalPrice": 280000,
        "items": [...]
      },
      "error": null
    }
  ]
}
```

**Java DTO:** `RecommendationResponse.java`, `OutfitRecommendationDto.java`, `OutfitResultDto.java`, `ItemPositionDto.java` (PR #30 구현됨)

---

## Python 내부 로직

### 1. 퀴즈 답변 파싱

```python
{
  "occasion": "date",      # 1번 질문
  "style": "stylish",      # 2번 질문
  "body_type": "none",     # 3번 질문
  "budget": 300000         # 4번 질문
}
```

### 2. 스타일 매핑

`occasion` + `style` 조합을 DB의 `primary_style`로 매핑:

```python
("date", "stylish") → ["cityboy", "minimalist"]
```

**전체 매핑 (16가지 조합 → 6가지 스타일):**

- `hip_hop`, `minimalist`, `street`, `gorpcore`, `amekaji`, `cityboy`

**참고:**

- 스타일 정의는 `ipzy-backend/docs/product/brand-by-style.md` 문서 기준
- 현재 `primary_style`은 String 타입 (enum은 프로토타입 테스트 후 결정)

### 3. DB 상품 조회

PostgreSQL `products` 테이블에서:

- 카테고리: TOP, BOTTOM, OUTER, SHOES
- 필터: `primary_style` IN (매핑된 스타일), `price` <= 예산
- 정렬: ID 순 (나중에 인기순으로 변경 가능)
- 개수: 카테고리당 최대 10개

### 4. LLM 코디 선택

OpenAI GPT-3.5-turbo에게 상품 후보를 전달:

- 각 카테고리에서 1개씩 선택
- 색상 조화, 스타일 통일성 고려
- 체형 고민 반영
- 총 3개 코디 세트 반환

### 5. DTO 변환

Python 내부 데이터 → Java DTO 형식 (camelCase)

---

## Java 쪽 수정 사항

### PythonAiClient.java

**변경 전:**

```java
RecommendationResponse response = pythonAiRestClient.post()
    .uri("/api/v1/recommend")  // ❌ 기존
    .body(request)
    .retrieve()
    .body(RecommendationResponse.class);
```

**변경 후:**

```java
RecommendationResponse response = pythonAiRestClient.post()
    .uri("/api/recommend")  // ✅ 신규
    .body(request)
    .retrieve()
    .body(RecommendationResponse.class);
```

---

## 테스트 방법

### 1. Python 서버 실행

```bash
cd ipzy-ai
docker compose up -d
# 또는
uvicorn app.main:app --reload
```

### 2. 엔드포인트 테스트

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": 123,
    "answers": [
      {"questionId": 1, "questionText": "어디 가요?", "selectedOptions": ["date"]},
      {"questionId": 2, "questionText": "어떻게 보이고 싶어요?", "selectedOptions": ["stylish"]},
      {"questionId": 3, "questionText": "체형 고민?", "selectedOptions": ["none"]},
      {"questionId": 4, "questionText": "예산은?", "selectedOptions": ["300000"]}
    ]
  }'
```

### 3. Java 통합 테스트

Java 백엔드에서 `POST /api/recommendations/sessions/{sessionId}/generate` 호출

---

## 환경 변수 (.env)

**필수:**

```bash
OPENAI_API_KEY=sk-proj-...  # OpenAI GPT-3.5-turbo API 키
```

**선택 (AWS 설정 없어도 동작):**

```bash
# IAM 계정 사용 권장 (Root 계정 X)
# 권장: aws configure 사용 (환경변수 불필요)
AWS_S3_BUCKET=...
```

---

## 주의 사항

1. **PostgreSQL 연결**: Python과 Java가 같은 DB(`ipzy_db`) 공유
2. **상품 데이터**: `products`, `brands` 테이블에 데이터가 있어야 함
3. **LLM API 키**: OpenAI API 키 필수 (GPT-3.5-turbo 사용)
4. **중복 제거 로직**: 현재 미구현 (향후 추가 예정)
