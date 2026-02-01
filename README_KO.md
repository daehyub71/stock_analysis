# 주식 분석 대시보드

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🇺🇸 [English Documentation](README.md)

**기술분석**, **기본분석**, **감정분석**을 결합하여 KOSPI/KOSDAQ 종목의 투자 점수를 산출하는 종합 한국 주식 분석 시스템입니다.

## 주요 기능

### 📊 다차원 분석
- **기술분석 (30점 만점)**
  - 이동평균선 배열 (MA5/20/60/120)
  - 이평선 이격도 분석
  - RSI (14일)
  - MACD (12, 26, 9)
  - 거래량 분석

- **기본분석 (50점 만점)**
  - 밸류에이션: PER, PBR, PSR
  - 성장성: 매출액 증가율, 영업이익 증가율
  - 수익성: ROE, 영업이익률
  - 재무 안정성: 부채비율, 유동비율

- **감정분석 (20점 만점)**
  - 뉴스 감정 분석 (OpenAI GPT-4o-mini)
  - 구글 트렌드 연동
  - **수동 뉴스 평점 시스템** (-10 ~ +10)

### 🤖 AI 기반 기능
- **LLM 코멘터리**: GPT-4o-mini를 활용한 자동 한국어 투자 해설 생성
- **뉴스 감정 분석**: 금융 뉴스 자동 감정 분류
- **수동 오버라이드**: 사용자가 직접 뉴스를 평가하여 자동 분석 대체 가능

### 📈 대시보드 기능
- 실시간 주가 표시
- 이동평균선 오버레이가 포함된 인터랙티브 차트
- 종목 비교 (최대 4종목)
- 분석 히스토리 추적
- 점수 기반 종목 랭킹
- 업종, 점수, 시장별 고급 필터링

## 기술 스택

### 백엔드
| 기술 | 용도 |
|------|------|
| FastAPI | REST API 프레임워크 |
| SQLAlchemy | SQLite ORM (시세 데이터) |
| Supabase | 클라우드 데이터베이스 (분석 데이터) |
| pykrx | 한국 주식 데이터 수집 |
| OpenAI API | 감정 분석 & 코멘터리 |
| pandas/numpy | 데이터 처리 |
| ta (Technical Analysis) | 기술 지표 계산 |

### 프론트엔드
| 기술 | 용도 |
|------|------|
| React 18 | UI 프레임워크 |
| TypeScript | 타입 안정성 |
| Vite | 빌드 도구 |
| TanStack Query | 서버 상태 관리 |
| Zustand | 클라이언트 상태 관리 |
| Tailwind CSS | 스타일링 |
| Recharts | 데이터 시각화 |
| Lightweight Charts | 주가 차트 |

### 데이터 소스
- **KIS API** (한국투자증권): 실시간 시세
- **pykrx**: 과거 시세 데이터 (백업)
- **네이버 금융**: 재무제표, 밸류에이션 지표
- **구글 트렌드**: 검색 트렌드 데이터
- **네이버 뉴스**: 금융 뉴스 크롤링

## 프로젝트 구조

```
stock_analysis/
├── backend/
│   ├── app/
│   │   ├── api/              # API 엔드포인트
│   │   │   ├── analysis.py   # 분석 API
│   │   │   ├── stocks.py     # 종목 API
│   │   │   └── portfolios.py # 포트폴리오 API
│   │   ├── collectors/       # 데이터 수집기
│   │   │   ├── kis_api.py    # KIS API 클라이언트
│   │   │   ├── pykrx_collector.py
│   │   │   ├── naver_finance.py
│   │   │   ├── news_collector.py
│   │   │   └── google_trends.py
│   │   ├── services/         # 비즈니스 로직
│   │   │   ├── technical.py  # 기술분석
│   │   │   ├── fundamental.py # 기본분석
│   │   │   ├── sentiment.py  # 감정분석
│   │   │   ├── scoring.py    # 점수 계산
│   │   │   └── commentary.py # LLM 코멘터리
│   │   ├── analyzers/        # 분석 모듈
│   │   │   ├── indicators.py # 기술 지표
│   │   │   └── openai_sentiment.py
│   │   ├── db/               # 데이터베이스
│   │   │   ├── sqlite_db.py  # 시세 데이터 (로컬)
│   │   │   └── supabase_db.py # 분석 데이터 (클라우드)
│   │   ├── models/           # Pydantic 모델
│   │   └── main.py           # FastAPI 앱
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # 페이지 컴포넌트
│   │   │   ├── Dashboard.tsx
│   │   │   ├── StockDetailPage.tsx
│   │   │   ├── ComparePage.tsx
│   │   │   └── HistoryPage.tsx
│   │   ├── components/       # UI 컴포넌트
│   │   │   ├── dashboard/
│   │   │   ├── charts/
│   │   │   ├── analysis/
│   │   │   └── common/
│   │   ├── services/         # API 클라이언트
│   │   ├── stores/           # Zustand 스토어
│   │   └── types/            # TypeScript 타입
│   └── package.json
├── scripts/                  # 자동화 스크립트
│   ├── collect_daily_prices.py
│   ├── run_daily_analysis.py
│   └── collect_news.py
├── docs/                     # 문서
└── .github/workflows/        # GitHub Actions
```

## 설치

### 사전 요구사항
- Python 3.11+
- Node.js 18+
- Supabase 계정
- OpenAI API 키
- KIS API 자격증명 (선택사항)

### 백엔드 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/stock_analysis.git
cd stock_analysis

# 가상환경 생성
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일에 자격증명 입력
```

### 프론트엔드 설정

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```

### 환경 변수

`backend/.env` 파일 생성:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key

# KIS API (선택사항)
KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret
KIS_ACCOUNT_TYPE=VIRTUAL  # 또는 REAL

# 데이터베이스
SQLITE_DB_PATH=./data/stock_prices.db
```

## 사용 방법

### 애플리케이션 시작

```bash
# 터미널 1: 백엔드
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 터미널 2: 프론트엔드
cd frontend
npm run dev
```

대시보드 접속: `http://localhost:3000`

### API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| GET | `/api/stocks` | 종목 목록 조회 (필터 지원) |
| GET | `/api/stocks/{code}` | 종목 상세 조회 |
| GET | `/api/stocks/{code}/history` | 시세 히스토리 조회 |
| GET | `/api/stocks/compare` | 종목 비교 |
| GET | `/api/analysis/{code}` | 분석 결과 조회 |
| POST | `/api/analysis/{code}/run` | 새 분석 실행 |
| GET | `/api/analysis/{code}/commentary` | AI 코멘터리 조회 |
| GET | `/api/analysis/{code}/news` | 뉴스 목록 조회 |
| PUT | `/api/analysis/{code}/news/{id}/rate` | 뉴스 평점 업데이트 |

### 자동 데이터 수집

```bash
# 일일 시세 수집 (GitHub Actions 또는 cron)
python scripts/collect_daily_prices.py

# 전체 종목 분석 실행
python scripts/run_daily_analysis.py

# 뉴스 수집
python scripts/collect_news.py
```

## 점수 체계

### 등급 산정

| 등급 | 점수 범위 | 설명 |
|------|----------|------|
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

기술분석 (30):
├── 이평선 배열: 6
├── 이평선 이격도: 6
├── RSI: 5
├── MACD: 5
└── 거래량: 8

기본분석 (50):
├── PER: 8
├── PBR: 7
├── PSR: 5
├── 매출액 증가율: 6
├── 영업이익 증가율: 6
├── ROE: 5
├── 영업이익률: 5
├── 부채비율: 4
└── 유동비율: 4

감정분석 (20):
├── 뉴스 감정: 10
├── 뉴스 영향도: 6
└── 뉴스량/관심도: 4
```

## 스크린샷

### 1. 메인 대시보드
모든 종목의 점수, 등급, 점수 분포를 표시하는 메인 대시보드입니다. 업종, 시장(KOSPI/KOSDAQ), 다양한 기준으로 필터링 및 정렬할 수 있습니다.

![메인 대시보드](docs/screenshots/dash_00.png)

**주요 기능:**
- 포트폴리오 요약 (총 종목 수, 평균 점수, 상승/하락 종목)
- 실시간 가격 및 등락률이 포함된 종목 테이블
- 점수 분포 시각화 바 (기술분석/기본분석/감정분석)
- 등급 표시 (A+, A, B+, B, C+, C, D, F)

---

### 2. 종목 상세 - 개요 & AI 코멘터리
AI가 생성한 투자 코멘터리와 함께 종합 분석을 보여주는 종목 상세 페이지입니다.

![종목 개요](docs/screenshots/stock_news_04.png)

**주요 기능:**
- 현재가와 등락률이 표시된 종목 헤더
- 등급 배지와 함께 표시되는 종합 점수
- 점수 분석 카드 (기술분석 23.0/30, 기본분석 27.0/50, 감정분석 15.0/20)
- AI가 생성한 한국어 투자 코멘터리 (핵심 인사이트 및 리스크 요인)

---

### 3. 기술분석 탭
이동평균선 오버레이가 포함된 인터랙티브 주가 차트와 상세 기술 지표를 표시합니다.

![기술분석](docs/screenshots/stock_tech_02.png)

**주요 기능:**
- MA5, MA20, MA60, MA120 이동평균선이 표시된 주가 차트
- 기술 점수 카드 (이평선 배열, 이평선 이격도, RSI, MACD, 거래량)
- 상세 지표 값 및 해석
- RSI 게이지 시각화 (과매도/중립/과매수 구간)

---

### 4. 기본분석 탭
카테고리별로 정리된 종합 재무 지표와 시각적 점수를 표시합니다.

![기본분석](docs/screenshots/stock_basic_03.png)

**주요 기능:**
- 밸류에이션 지표: PER (9.7), PBR (1.60), PSR (4.44)
- 수익성 지표: ROE (21.1%), 영업이익률 (43.6%)
- 성장성 지표: 매출성장률 (+41.8%), 영업이익성장률 (+54.0%)
- 안정성 지표: 부채비율 (16.0%), 유동비율 (231.2%)

---

### 5. 감정분석 & 뉴스 평점
자동 감정분석을 사용자가 직접 오버라이드할 수 있는 수동 뉴스 평점 시스템입니다.

![감정분석](docs/screenshots/stock_total_01.png)

**주요 기능:**
- 수동/자동 표시가 포함된 현재 시장 감정 상태
- 사용자 평점 적용 시 수동 평점 알림 표시
- -10 ~ +10 척도의 뉴스 평점 인터페이스
- 평점 버튼이 포함된 개별 뉴스 항목
- 사용자 평점 기반 실시간 점수 재계산

## 로드맵

- [x] Phase 1: MVP (1-4주차)
  - [x] 데이터 수집 인프라
  - [x] 분석 엔진
  - [x] React 대시보드
  - [x] LLM 코멘터리
  - [x] 수동 뉴스 평점

- [x] Phase 2: 5주차
  - [x] 종목 비교
  - [x] 분석 히스토리

- [ ] Phase 2: 6-8주차
  - [ ] 백테스팅 모듈
  - [ ] 알림 시스템
  - [ ] 다크 모드
  - [ ] 포트폴리오 시뮬레이션

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
- [OpenAI](https://openai.com/) - 감정 분석을 위한 GPT-4o-mini
