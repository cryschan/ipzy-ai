# Docker 환경 설정 가이드

## 📋 사전 준비

### 1. Docker 네트워크 생성 (백엔드와 공유)

```bash
# ipzy-network 생성 (백엔드에서 이미 생성했다면 skip)
docker network create ipzy-network
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 수정 (필수!)
# - OPENAI_API_KEY
# - GOOGLE_API_KEY
# - BACKEND_API_KEY
```

---

## 🚀 실행 방법

### 옵션 1: AI 서버만 실행

```bash
# AI 서버 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f ipzy-ai

# 상태 확인
curl http://localhost:8000/health
```

### 옵션 2: 백엔드 + AI 서버 통합 실행

**백엔드와 AI 서버를 함께 관리하려면:**

```bash
# 백엔드 프로젝트 루트에서
cd /path/to/ipzy-backend

# docker-compose.yml에 AI 서버 추가 (아래 참고)
```

#### 통합 docker-compose.yml 예시

백엔드 `docker-compose.yml`에 추가:

```yaml
version: '3.8'

services:
  postgres:
    # ... 기존 설정 유지

  app:
    # ... 기존 설정 유지
    networks:
      - ipzy-network

  ipzy-ai:
    build:
      context: ../ipzy-ai  # AI 서버 경로
      dockerfile: Dockerfile
    container_name: ipzy-ai
    depends_on:
      - app
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BACKEND_API_URL=http://ipzy-app:8080
      - BACKEND_API_KEY=${BACKEND_API_KEY}
      - LLM_PROVIDER=gemini
      - LLM_MODEL=gemini-1.5-flash
    volumes:
      - ai_data:/app/data
      - ai_outputs:/app/outputs
    networks:
      - ipzy-network
    restart: on-failure

networks:
  ipzy-network:
    driver: bridge

volumes:
  postgres_data:
  ai_data:
  ai_outputs:
```

---

## 🔍 서비스 확인

### AI 서버 헬스 체크

```bash
curl http://localhost:8000/health
```

예상 응답:
```json
{
  "status": "healthy"
}
```

### API 문서 확인

브라우저에서 접속:
```
http://localhost:8000/api/v1/docs
```

---

## 🛠️ 개발 환경 설정

### 로컬에서 코드 수정 반영 (Hot Reload)

```yaml
# docker-compose.yml 수정
services:
  ipzy-ai:
    # ... 기존 설정
    volumes:
      - ./app:/app/app  # 코드 변경 즉시 반영
      - ai_data:/app/data
      - ai_outputs:/app/outputs
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# 재시작
docker-compose up -d
```

---

## 🧪 테스트

### 백엔드 → AI 서버 연동 테스트

```bash
# 1. 상품 이미지 분석 (배치)
curl -X POST http://localhost:8000/api/v1/analyze/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-backend-api-key" \
  -d '{
    "product_ids": ["prod_001", "prod_002"]
  }'

# 2. 퀴즈 분석
curl -X POST http://localhost:8000/api/v1/users/analyze-quiz \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "responses": [
      {"question": "선호 스타일", "answer": "캐주얼"}
    ]
  }'

# 3. 코디 추천
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "location": "office",
    "style": "classic",
    "body_type": "regular",
    "budget_min": 100000,
    "budget_max": 500000,
    "gender": "male"
  }'
```

---

## 📊 모니터링

### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f ipzy-ai

# 최근 100줄
docker-compose logs --tail=100 ipzy-ai
```

### 컨테이너 상태

```bash
docker-compose ps
```

### 리소스 사용량

```bash
docker stats ipzy-ai
```

---

## 🗑️ 정리

### 서비스 중지

```bash
docker-compose down
```

### 데이터까지 삭제 (초기화)

```bash
docker-compose down -v
```

### 이미지 재빌드

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 🐛 트러블슈팅

### 1. 네트워크 연결 안됨

```bash
# 네트워크 확인
docker network ls

# ipzy-network가 없으면 생성
docker network create ipzy-network

# 컨테이너를 네트워크에 연결
docker network connect ipzy-network ipzy-ai
docker network connect ipzy-network ipzy-app
```

### 2. 백엔드와 통신 안됨

```bash
# AI 컨테이너에서 백엔드 ping 테스트
docker exec -it ipzy-ai sh
apk add curl
curl http://ipzy-app:8080/actuator/health
```

### 3. ChromaDB 데이터 초기화 필요

```bash
# 볼륨 삭제
docker volume rm ipzy-ai_ai_data

# 재시작
docker-compose up -d
```

### 4. API 키 오류

```bash
# 환경변수 확인
docker exec ipzy-ai env | grep API_KEY

# .env 파일 다시 확인 후 재시작
docker-compose down
docker-compose up -d
```

---

## 📝 환경변수 우선순위

1. **docker-compose.yml의 environment**
2. **.env 파일**
3. **시스템 환경변수**

.env 파일을 수정했다면 반드시 재시작:
```bash
docker-compose down
docker-compose up -d
```
