# IPZY AI Server

## WHY

패션 선택에 어려움을 겪는 사용자를 위한 **AI 기반 코디 추천 서비스**.
**유튜버 패션 전문가들의 코디 정보**를 임베딩하여 벡터 검색 기반 추천을 제공합니다.

## 기술 스택

- Python 3.11, FastAPI 0.109, Uvicorn
- PostgreSQL 16 + pgvector (벡터 검색)
- OpenAI GPT-4o / Google Gemini (LLM)
- SQLAlchemy 2.0 + asyncpg (비동기 DB)
- rembg (이미지 배경 제거)

## 빠른 시작

```bash
cp .env.example .env              # 환경변수 설정
docker compose up -d              # 컨테이너 실행
# 또는 로컬 실행
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 패키지 구조

```text
app/
├── main.py                  # FastAPI 앱 진입점
├── core/
│   ├── config.py           # 설정 관리 (Pydantic Settings)
│   └── database.py         # SQLAlchemy 엔진/세션
├── api/
│   ├── router.py           # API 라우터
│   └── endpoints/          # 엔드포인트 모듈
├── models/                  # SQLAlchemy 모델 (DB 테이블)
├── schemas/                 # Pydantic 스키마 (Request/Response)
├── services/               # 비즈니스 로직
└── utils/                  # 유틸리티
```

**핵심 진입점:**
- `app/main.py` - FastAPI 앱, 미들웨어, 라우터
- `app/core/config.py` - 환경변수 설정
- `app/core/database.py` - DB 연결 관리

## 주요 명령어

```bash
uvicorn app.main:app --reload     # 개발 서버 실행
pytest                            # 테스트 실행
docker compose up -d              # Docker 실행
docker compose logs -f ipzy-ai    # 로그 확인
```

## 저장소 관례

- 브랜치: `feature/*`, `hotfix/*` → `dev` → `main`
- 커밋: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)

## API 문서

- Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- ReDoc: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

## 백엔드 연동

- 백엔드 프로젝트: `/Users/chan/workspace/ipzy-backend`
- 동일한 PostgreSQL DB 공유 (ipzy_db, 포트 5432)
- 백엔드가 퀴즈 응답을 Python API로 전송
- AI 서버가 직접 접근하는 테이블:
  - `products`, `brands` - 상품/브랜드 조회
  - `youtuber_embeddings` - 유튜버 코디 벡터 검색 (pgvector)

## 추천 흐름

```text
백엔드 → Python: POST /api/recommend {
    "location": "office",
    "style": "classic",
    "body_type": "regular",
    "budget_min": 100000,
    "budget_max": 500000,
    "gender": "male"
}
                         ↓
Python: 1) 퀴즈 응답을 텍스트로 변환 → 임베딩 생성
        2) youtuber_embeddings에서 유사 스타일 벡터 검색
        3) 매칭된 스타일로 products 상품 조회
        4) 코디 세트 구성하여 반환
                         ↓
백엔드 ← Python: { "recommendations": [...] }
```

## 핵심 테이블

| 테이블 | 역할 | 관리 주체 |
|--------|------|----------|
| products | 상품 정보 | Java 백엔드 |
| brands | 브랜드 정보 | Java 백엔드 |
| youtuber_embeddings | 유튜버 코디 임베딩 (pgvector) | **Python AI** |
