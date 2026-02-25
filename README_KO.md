# 주식 분석 대시보드

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/Tests-159%20passed-brightgreen.svg)](#%ED%85%8C%EC%8A%A4%ED%8A%B8)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> [English Documentation](README.md)

**기술분석**, **기본분석**, **감정분석**을 결합하여 KOSPI/KOSDAQ 종목의 투자 점수를 산출하는 종합 한국 주식 분석 시스템입니다.

**라이브 데모**: [https://frontend-pi-coral-73.vercel.app](https://frontend-pi-coral-73.vercel.app)

## 주요 기능

### 다차원 점수 분석 (100점 만점)
- **기술분석 (30점)** - 이평선 배열, 이격도, RSI, MACD, 거래량
- **기본분석 (50점)** - PER, PBR, PSR, ROE, 성장성, 안정성
- **감정분석 (20점)** - 뉴스 감정 분석 (OpenAI), 수동 평점 오버라이드

### AI 기반 기능
- **LLM 코멘터리**: GPT-4o-mini를 활용한 자동 한국어 투자 해설 생성
- **뉴스 감정 분석**: 금융 뉴스 자동 감정 분류
- **수동 오버라이드**: 사용자가 직접 뉴스를 평가하여 (-10 ~ +10) 자동 분석 대체

### 대시보드 페이지
| 페이지 | 설명 |
|--------|------|
| 대시보드 | 통계 카드, 종목 테이블, 업종 필터 |
| 종목 상세 | 3탭 분석 (기술분석 / 기본분석 / 감정분석) + 주가 차트 |
| 순위 | 점수 기반 상위/하위 종목 랭킹 |
| 비교 | 최대 4종목 나란히 비교 |
| 포트폴리오 | 포트폴리오 생성/관리, 비중 조절, 점수 산출 |
| 히스토리 | 점수 추이 추적 (7일 / 30일 / 90일 / 1년) |
| 백테스팅 | 기술 점수 기반 매수/매도 시뮬레이션 |
| 설정 | 테마 (라이트/다크/시스템), 이메일 알림, 데이터 내보내기 |

## 아키텍처

```
[Vercel]           [Cloud Run]           [Supabase]       [SQLite]
 React 앱     -->   FastAPI 백엔드  -->  PostgreSQL   +   시세 히스토리
 (프론트엔드)       (Docker)              (분석 데이터)     (로컬 OHLCV)

                    [GitHub Actions]
                     일일 시세 수집
                     분기 재무제표
                     감정분석
```

## 기술 스택

### 백엔드
| 기술 | 용도 |
|------|------|
| FastAPI | REST API 프레임워크 |
| Supabase | 클라우드 데이터베이스 (PostgreSQL) |
| SQLite + SQLAlchemy | 로컬 시세 저장 |
| pykrx | 한국 주식 데이터 (백업) |
| KIS API | 한국투자증권 (실시간 시세) |
| OpenAI API | 감정분석 & LLM 코멘터리 |
| pandas / numpy / ta | 데이터 처리 & 기술 지표 |
| pytest | 테스트 (159개) |

### 프론트엔드
| 기술 | 용도 |
|------|------|
| React 18 + TypeScript | UI 프레임워크 |
| Vite 6 | 빌드 도구 |
| TanStack Query | 서버 상태 관리 |
| Zustand | 클라이언트 상태 관리 |
| Tailwind CSS | 스타일링 (다크 모드 지원) |
| Recharts | 데이터 시각화 |
| Lightweight Charts | 인터랙티브 주가 차트 |
| React Router 6 | SPA 라우팅 |

### 데이터 소스
- **KIS API** (한국투자증권) - 실시간 시세
- **pykrx** - 과거 시세 데이터 (폴백)
- **네이버 금융** - 재무제표, 밸류에이션 지표, 업종 정보
- **구글 트렌드** - 검색 트렌드 데이터
- **네이버 뉴스** - 금융 뉴스 크롤링

## 프로젝트 구조

```
stock_analysis/
├── backend/
│   ├── app/
│   │   ├── api/                 # API 엔드포인트
│   │   │   ├── stocks.py        # 종목 목록, 상세, 통계, 업종
│   │   │   ├── analysis.py      # 분석, 코멘터리, 뉴스, 감정
│   │   │   ├── portfolios.py    # 포트폴리오 CRUD, 점수
│   │   │   ├── backtest.py      # 백테스팅 엔진
│   │   │   └── alerts.py        # 점수 변화 알림, 이메일
│   │   ├── collectors/          # 데이터 수집기
│   │   │   ├── kis_api.py       # KIS API (자동 토큰 갱신, 속도 제한)
│   │   │   ├── pykrx_collector.py
│   │   │   ├── naver_finance.py # 재무 데이터 & 업종 정보
│   │   │   ├── news_collector.py
│   │   │   └── google_trends.py
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── technical.py     # 기술분석 (30점)
│   │   │   ├── fundamental.py   # 기본분석 (50점)
│   │   │   ├── sentiment.py     # 감정분석 (20점)
│   │   │   ├── scoring.py       # 점수 통합 & 등급 산정
│   │   │   ├── commentary.py    # LLM 코멘터리 생성
│   │   │   ├── backtesting.py   # 백테스팅 엔진
│   │   │   └── email_service.py # SMTP 이메일 알림
│   │   ├── analyzers/           # 분석 모듈
│   │   │   ├── indicators.py    # MA, RSI, MACD, 거래량
│   │   │   └── openai_sentiment.py
│   │   ├── db/                  # 데이터베이스 레이어
│   │   │   ├── sqlite_db.py     # 시세 데이터 (로컬)
│   │   │   └── supabase_db.py   # 분석 데이터 (클라우드)
│   │   ├── models/              # Pydantic 모델
│   │   └── main.py              # FastAPI 앱 진입점
│   ├── scripts/                 # 데이터 수집 스크립트
│   ├── tests/                   # 159개 단위 테스트
│   ├── Dockerfile               # Cloud Run 컨테이너
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # 8개 페이지 컴포넌트
│   │   ├── components/          # dashboard, charts, analysis, common
│   │   ├── services/api.ts      # Axios API 클라이언트
│   │   ├── stores/              # Zustand (종목, 테마)
│   │   ├── types/               # TypeScript 인터페이스
│   │   └── lib/                 # 유틸리티
│   ├── vercel.json              # Vercel SPA 설정
│   └── package.json
├── .github/workflows/           # 3개 GitHub Actions 파이프라인
├── docker-compose.yml
└── docs/
```

## 빠른 시작

### 사전 요구사항
- Python 3.11+
- Node.js 18+
- Supabase 계정
- OpenAI API 키
- KIS API 자격증명 (선택사항)

### 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일에 자격증명 입력

# 서버 시작
uvicorn app.main:app --reload --port 8000
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

접속: `http://localhost:5173`

### 환경 변수

`backend/.env` 파일 생성:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key

# KIS API (선택사항 - 실시간 시세용)
KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret

# SMTP (선택사항 - 이메일 알림용)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-app-password

# 데이터베이스
SQLITE_DB_PATH=./data/price_history.db

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## API 엔드포인트

### 종목
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| GET | `/api/stocks` | 종목 목록 (필터, 정렬, 페이지네이션) |
| GET | `/api/stocks/{code}` | 종목 상세 |
| GET | `/api/stocks/{code}/history` | 시세 히스토리 |
| GET | `/api/stocks/overview` | 대시보드 통계 |
| GET | `/api/stocks/sectors` | 업종 목록 |
| GET | `/api/stocks/compare` | 종목 비교 |

### 분석
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| GET | `/api/analysis/{code}` | 분석 결과 |
| POST | `/api/analysis/{code}/run` | 새 분석 실행 |
| GET | `/api/analysis/{code}/commentary` | AI 코멘터리 |
| GET | `/api/analysis/{code}/news` | 뉴스 목록 |
| PUT | `/api/analysis/{code}/news/{id}/rate` | 뉴스 평점 (-10~+10) |
| PUT | `/api/analysis/{code}/news/rate-all` | 미평점 뉴스 일괄 평점 |
| GET | `/api/analysis/{code}/sentiment-score` | 감정 점수 |
| GET | `/api/analysis/{code}/history` | 점수 히스토리 |
| GET | `/api/analysis/ranking` | 점수 랭킹 |

### 포트폴리오
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| GET | `/api/portfolios` | 포트폴리오 목록 |
| POST | `/api/portfolios` | 포트폴리오 생성 |
| GET | `/api/portfolios/{id}` | 포트폴리오 상세 |
| PUT | `/api/portfolios/{id}` | 포트폴리오 수정 |
| DELETE | `/api/portfolios/{id}` | 포트폴리오 삭제 |
| POST | `/api/portfolios/{id}/stocks` | 종목 추가 |
| DELETE | `/api/portfolios/{id}/stocks/{code}` | 종목 제거 |
| PUT | `/api/portfolios/{id}/stocks/{code}/weight` | 비중 조절 |
| GET | `/api/portfolios/{id}/score` | 포트폴리오 점수 |

### 백테스트 & 알림
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| POST | `/api/backtest/{code}/run` | 백테스트 실행 |
| GET | `/api/backtest/{code}/date-range` | 가능 기간 조회 |
| GET | `/api/alerts/score-changes` | 점수 변화 알림 |
| POST | `/api/alerts/send-alert-email` | 알림 이메일 발송 |

## 점수 체계

### 등급표

| 등급 | 점수 | 설명 |
|------|------|------|
| A+ | 90-100 | 매우 우수 |
| A | 80-89 | 우수 |
| B+ | 70-79 | 양호 |
| B | 60-69 | 보통 이상 |
| C+ | 50-59 | 보통 |
| C | 40-49 | 보통 이하 |
| D | 30-39 | 미흡 |
| F | 0-29 | 매우 미흡 |

### 점수 구성

```
총점 (100) = 기술분석 (30) + 기본분석 (50) + 감정분석 (20)

기술분석 (30):             기본분석 (50):             감정분석 (20):
├── 이평선 배열: 6         ├── PER: 8                ├── 뉴스 감정: 10
├── 이평선 이격도: 6       ├── PBR: 7                ├── 뉴스 영향도: 6
├── RSI: 5                ├── PSR: 5                └── 뉴스량/관심도: 4
├── MACD: 5               ├── 매출액 증가율: 6
└── 거래량: 8              ├── 영업이익 증가율: 6
                          ├── ROE: 5
                          ├── 영업이익률: 5
                          ├── 부채비율: 4
                          └── 유동비율: 4
```

## 배포

### 프로덕션 구성

| 구성요소 | 플랫폼 | URL |
|---------|--------|-----|
| 프론트엔드 | Vercel | https://frontend-pi-coral-73.vercel.app |
| 백엔드 | Google Cloud Run (서울) | https://stock-analysis-backend-675597240676.asia-northeast3.run.app |
| 데이터베이스 | Supabase (PostgreSQL) | 클라우드 관리형 |
| CI/CD | GitHub Actions | 3개 자동화 파이프라인 |

### 백엔드 배포 (Cloud Run)

```bash
# Docker 이미지 빌드 & 푸시
gcloud builds submit --tag asia-northeast3-docker.pkg.dev/PROJECT_ID/stock-analysis/backend:latest \
  --region=asia-northeast3 ./backend

# Cloud Run 배포
gcloud run deploy stock-analysis-backend \
  --image=asia-northeast3-docker.pkg.dev/PROJECT_ID/stock-analysis/backend:latest \
  --region=asia-northeast3 --allow-unauthenticated --port=8080 \
  --memory=512Mi --cpu=1 --min-instances=0 --max-instances=3 \
  --env-vars-file=backend/env.yaml
```

### 프론트엔드 배포 (Vercel)

```bash
cd frontend
vercel --prod
# Vercel 대시보드에서 VITE_API_URL 환경변수를 Cloud Run URL로 설정
```

### Docker (로컬)

```bash
docker-compose up -d
# 프론트엔드: http://localhost:3000
# 백엔드:    http://localhost:8000
```

## GitHub Actions CI/CD

| 워크플로우 | 스케줄 | 설명 |
|-----------|--------|------|
| `collect-prices.yml` | 평일 20:30 KST | 시세 수집 + 기술 지표 + 점수 계산 |
| `collect-quarterly.yml` | 분기별 | 재무제표 & 밸류에이션 지표 |
| `collect-sentiment.yml` | 월/목 21:00 KST | 뉴스 수집 & 감정분석 |

## 데이터베이스 스키마

### Supabase (PostgreSQL) - 클라우드
| 테이블 | 설명 |
|--------|------|
| `stocks_anal` | 종목 마스터 (코드, 종목명, 업종, 시장, 재무지표) |
| `analysis_results_anal` | 분석 결과 (기술/기본/감정 점수, 총점, 등급) |
| `news_ratings_anal` | 뉴스 항목 및 수동 평점 (-10 ~ +10) |
| `portfolios_anal` | 포트폴리오 정의 |
| `portfolio_stocks_anal` | 포트폴리오 보유 종목 (비중 포함) |
| `sector_averages_anal` | 업종 평균 벤치마크 |

### SQLite - 로컬
| 테이블 | 설명 |
|--------|------|
| `price_history` | 일별 OHLCV 데이터 |
| `technical_indicators` | 사전 계산된 MA, RSI, MACD, 거래량비율 |

## 테스트

```bash
cd backend
pytest tests/ -v
# 159 passed
```

```bash
cd frontend
npx tsc --noEmit   # TypeScript 타입 체크
npx vite build      # 빌드 검증
```

## 스크린샷

### 1. 메인 대시보드
![메인 대시보드](docs/screenshots/dash_00.png)

통계 카드 (분석 종목, 평균 점수, 상승/하락 종목), 종목 테이블, 점수 분포 바, 등급 표시

### 2. 종목 상세 - AI 코멘터리
![종목 개요](docs/screenshots/stock_news_04.png)

AI가 생성한 한국어 투자 코멘터리, 점수 분석 카드, 핵심 인사이트 및 리스크 요인

### 3. 기술분석
![기술분석](docs/screenshots/stock_tech_02.png)

이동평균선 오버레이 주가 차트, RSI 게이지, MACD 지표, 거래량 분석

### 4. 기본분석
![기본분석](docs/screenshots/stock_basic_03.png)

밸류에이션, 수익성, 성장성, 안정성 카테고리별 재무 지표

### 5. 감정분석 & 뉴스 평점
![감정분석](docs/screenshots/stock_total_01.png)

수동 뉴스 평점 인터페이스 (-10 ~ +10), 실시간 점수 재계산

## 로드맵

- [x] Phase 1: 핵심 시스템 (1-4주차)
  - [x] 데이터 수집 인프라 (KIS, pykrx, 네이버 금융, 뉴스)
  - [x] 분석 엔진 (기술분석 + 기본분석 + 감정분석)
  - [x] React 대시보드 + 종목 테이블
  - [x] LLM 코멘터리 & 수동 뉴스 평점

- [x] Phase 2: 고급 기능 (5-8주차)
  - [x] 종목 비교 (최대 4종목)
  - [x] 분석 히스토리 추적
  - [x] 백테스팅 엔진 (200일 슬라이딩 윈도우)
  - [x] 알림 시스템 (토스트, 브라우저 알림, 이메일)
  - [x] 다크 모드 (라이트 / 다크 / 시스템)
  - [x] 포트폴리오 시뮬레이션 (CRUD, 비중 조절, 점수)
  - [x] Docker + Cloud Run + Vercel 배포
  - [x] GitHub Actions 자동 데이터 파이프라인

## 기여

기여를 환영합니다! Pull Request를 자유롭게 제출해 주세요.

1. 저장소를 Fork합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 면책 조항

이 소프트웨어는 교육 및 정보 제공 목적으로만 제작되었습니다. 투자 조언을 제공하기 위한 것이 아닙니다. 투자 결정을 내리기 전에 항상 직접 조사하고 자격을 갖춘 재무 상담사와 상담하시기 바랍니다.

## 감사의 말

- [pykrx](https://github.com/sharebook-kr/pykrx) - 한국 주식 데이터 라이브러리
- [FastAPI](https://fastapi.tiangolo.com/) - 현대적인 Python 웹 프레임워크
- [Supabase](https://supabase.com/) - 오픈소스 Firebase 대안
- [OpenAI](https://openai.com/) - 감정분석 & 코멘터리를 위한 GPT-4o-mini
- [TradingView Lightweight Charts](https://github.com/nicehash/lightweight-charts) - 인터랙티브 주가 차트
