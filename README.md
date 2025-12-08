# 뭐입지?

패션 코디 추천 AI 서버 - FastAPI 기반

## 주요 기능

- **사용자 입력 기반 추천**: 장소, 스타일, 체형, 예산 등을 고려한 맞춤형 코디 추천
- **벡터 검색**: ChromaDB를 활용한 효율적인 상품 검색
- **LLM 기반 조합**: OpenAI GPT를 사용한 지능형 코디 조합
- **이미지 합성**: 상품 이미지 누끼 제거 및 합성 이미지 생성

## 주요 기술 스택

- **FastAPI**: 고성능 웹 프레임워크
- **ChromaDB**: 벡터 데이터베이스
- **OpenAI GPT**: 코디 조합 생성
- **Pillow**: 이미지 처리
- **rembg**: 배경 제거
- **Pydantic**: 데이터 검증

## 요구사항

- Python 3.11 이상

## 설치 및 실행

### 0. Python 설치

#### pyenv 사용 (권장)

```bash
# pyenv 설치 (macOS)
brew install pyenv

# pyenv 설치 (Linux)
curl https://pyenv.run | bash

# Python 3.11 설치
pyenv install 3.11

# 프로젝트 디렉토리에서 Python 3.11 사용 (.python-version 파일이 이미 있으므로 자동 전환됨)
# 또는 수동으로 설정: pyenv local 3.11
```

#### 직접 설치

- **macOS**: [python.org](https://www.python.org/downloads/) 또는 `brew install python@3.11`
- **Windows**: [python.org](https://www.python.org/downloads/)에서 다운로드

설치 후 버전 확인:
```bash
python3 --version  # Python 3.11.x 확인
```

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 OpenAI API 키 등을 설정
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소에서 확인할 수 있습니다:

- API 문서: http://localhost:8000/api/v1/docs
- 헬스 체크: http://localhost:8000/health

## 프로젝트 구조

```
ipzy-ai/
├── app/
│   ├── main.py                         # FastAPI 메인 애플리케이션
│   ├── api/
│   │   └── v1/
│   │       ├── router.py               # API 라우터
│   │       └── endpoints/
│   │           ├── recommendations.py  # 코디 추천 엔드포인트
│   │           └── products.py         # 상품 관리 엔드포인트
│   ├── core/
│   │   └── config.py                   # 설정 관리
│   ├── models/                         # 데이터베이스 모델
│   ├── schemas/
│   │   ├── recommendation.py           # 추천 관련 스키마
│   │   └── product.py                  # 상품 관련 스키마
│   ├── services/
│   │   ├── vector_search.py            # 벡터 검색 서비스
│   │   ├── llm_service.py              # LLM 서비스
│   │   └── image_processing.py         # 이미지 처리 서비스
│   └── utils/                          # 유틸리티 함수
├── data/                               # 벡터 DB 저장소
├── outputs/                            # 생성된 이미지 저장소
├── requirements.txt                    # Python 의존성
├── .env.example                        # 환경변수 예시
└── README.md
```
