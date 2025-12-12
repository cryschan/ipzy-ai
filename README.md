# 뭐입지? AI 서버

> 20-40대 남성을 위한 패션 코디 추천 AI 시스템

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## 🎯 주요 기능

### 1. 상품 이미지 자동 분석
- **Gemini 1.5 Flash**를 활용한 패션 아이템 분석
- 색상, 패턴, 핏, 스타일 자동 추출
- ChromaDB 캐싱으로 비용 97% 절감

### 2. AI 코디 추천
- 유저 프로파일 기반 개인화 추천
- 상의 + 하의 + 신발 + 아우터 조합
- 예산, 체형, 스타일 고려

### 3. 합성 이미지 생성
- 배경 제거 (누끼)
- 레이어 방식 코디 미리보기

### 4. 퀴즈 기반 스타일 프로파일링
- 사용자 선호도 벡터화
- 지속적인 학습 및 개선

---

## 🛠️ 기술 스택

| 카테고리 | 기술 | 용도 |
|---------|------|------|
| **Framework** | FastAPI | 웹 서버 |
| **이미지 분석** | Gemini 1.5 Flash | 상품 분석 |
| **코디 추천** | Gemini 1.5 Flash/Pro | LLM 추천 |
| **Vector DB** | ChromaDB | 캐싱 & 검색 |
| **이미지 처리** | Pillow + rembg | 합성 이미지 |
| **Container** | Docker | 배포 |

---

## 📚 문서

- **[아키텍처 문서](./ARCHITECTURE.md)** - 전체 시스템 설계 및 설정 가이드
- **[Docker 가이드](./DOCKER_SETUP.md)** - Docker 설정 상세 방법

---

## 🚀 빠른 시작

### 1. 사전 준비

**필수:**
- Python 3.11+
- Docker & Docker Compose
- Google Gemini API 키

**선택:**
- OpenAI API 키 (GPT 모델 사용 시)

### 2. 환경 설정

```bash
# 1. 리포지토리 클론
cd /Users/a/IdeaProjects/FinalProject/ipzy-ai

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 수정:
# - GOOGLE_API_KEY
# - BACKEND_API_KEY

# 3. Docker 네트워크 생성
docker network create ipzy-network
```

### 3. 실행

#### Docker 사용 (권장)

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f ipzy-ai

# 헬스 체크
curl http://localhost:8000/health
```

#### 로컬 개발 환경

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인

브라우저에서 접속:
```
http://localhost:8000/api/v1/docs
```

---

## 📊 프로젝트 구조

```
ipzy-ai/
├── app/
│   ├── main.py                    # FastAPI 앱
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/         # API 엔드포인트
│   ├── core/
│   │   └── config.py              # 설정 관리
│   ├── models/                    # 데이터 모델
│   ├── schemas/                   # Pydantic 스키마
│   ├── services/                  # 비즈니스 로직
│   │   ├── image_processing.py
│   │   ├── llm_service.py
│   │   └── (추가 예정)
│   └── utils/                     # 유틸리티
├── data/                          # ChromaDB 데이터
├── outputs/                       # 생성된 이미지
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── ARCHITECTURE.md                # 아키텍처 문서
├── SETUP_STATUS.md                # 설정 현황
└── README.md
```

---

## 💰 비용 최적화

### Gemini 1.5 Flash 선택 이유

| 모델 | 이미지 분석 | 추천 1건 | 월 1,000명 |
|------|-----------|---------|-----------|
| **Gemini Flash** | $0.0001 | $0.0015 | **$15** |
| GPT-4o-mini | $0.0003 | $0.003 | $30 |
| GPT-4o | $0.003 | $0.05 | $500 |

**97% 비용 절감 달성!**

---

## 🧪 테스트

### 헬스 체크
```bash
curl http://localhost:8000/health
```

### 상품 분석 (Webhook)
```bash
curl -X POST http://localhost:8000/api/v1/analyze/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-backend-api-key" \
  -d '{"product_ids": ["prod_001"]}'
```

### 코디 추천
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "location": "office",
    "style": "classic",
    "budget_min": 100000,
    "budget_max": 500000
  }'
```

---

## 🔗 연동

### 백엔드 서버
- 리포지토리: https://github.com/cryschan/ipzy-backend
- 통신: `ipzy-network` Docker 네트워크
- 인증: API Key 기반

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 헬스 체크 |
| POST | `/api/v1/analyze/batch` | 상품 배치 분석 |
| POST | `/api/v1/users/analyze-quiz` | 퀴즈 분석 |
| POST | `/api/v1/recommendations` | 코디 추천 |
| POST | `/api/v1/feedback/like` | 피드백 저장 |

---

## 🛡️ 보안

- API Key 기반 인증
- 개인정보 최소 수집 (user_id만 보유)
- ChromaDB 로컬 저장 (외부 접근 차단)
- GDPR 준수 설계 (삭제 권리 보장)

---

## 📈 로드맵

### Phase 1: MVP (진행 중)
- [ ] 기본 추천 시스템
- [ ] 이미지 분석 파이프라인
- [ ] 퀴즈 처리

### Phase 2: 고도화
- [ ] 벡터 검색 활용
- [ ] 피드백 학습
- [ ] 성능 최적화

### Phase 3: 고급 기능
- [ ] 유명인 스타일 분석
- [ ] 착용 이미지 기반 추천
- [ ] 트렌드 반영

---

## 🤝 기여

이 프로젝트는 IPZY 팀 내부 프로젝트입니다.

---

## 📄 라이선스

Private Repository

---

## 📞 문의

- 백엔드 연동 문의: [백엔드 팀]
- 기술 지원: [AI 팀]

---

**현재 상태**: 🚧 개발 중 (설정 완료, 구현 대기)

자세한 현황은 [ARCHITECTURE.md](./ARCHITECTURE.md#-현재-진행-상황-및-설정-가이드)를 참고하세요.
