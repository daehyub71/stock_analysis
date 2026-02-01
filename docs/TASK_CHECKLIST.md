# 📋 종목분석시스템 Task Checklist

**프로젝트**: Stock Analysis Dashboard
**작성일**: 2025년 1월 31일
**총 예상 기간**: 8주 (Phase 1: 4주, Phase 2: 4주)

---

## Phase 1: MVP (4주)

### Week 1: 프로젝트 셋업 & 기본 구조

#### 1.1 개발 환경 설정
- [x] Python 가상환경 생성 (venv)
- [x] `requirements.txt` 작성 (FastAPI, SQLAlchemy, supabase-py, pykrx 등)
- [x] `.env.example` 작성 및 환경변수 설정
- [x] `.gitignore` 설정
- [x] Git 저장소 초기화

#### 1.2 데이터베이스 설정
- [x] **SQLite 설정 (시세 데이터)**
  - [x] `sqlite_db.py` - 연결 및 세션 관리
  - [x] `price_history` 테이블 생성
  - [x] `technical_indicators` 테이블 생성
  - [x] 인덱스 생성
- [x] **Supabase 설정 (분석 데이터)**
  - [ ] Supabase 프로젝트 생성 *(대시보드에서 수동 실행)*
  - [x] `supabase_db.py` - 클라이언트 연결
  - [x] `stocks` 테이블 생성 *(SQL 작성완료: docs/supabase_schema.sql)*
  - [x] `portfolios` 테이블 생성
  - [x] `portfolio_stocks` 테이블 생성
  - [x] `sector_averages` 테이블 생성
  - [x] `analysis_results` 테이블 생성
  - [x] RLS 정책 설정

#### 1.3 기본 모델 정의
- [x] `models/stock.py` - Stock Pydantic 모델
- [x] `models/portfolio.py` - Portfolio 모델
- [x] `models/analysis.py` - AnalysisResult 모델

#### 1.4 FastAPI 기본 구조
- [x] `main.py` - FastAPI 앱 초기화
- [x] `config.py` - 환경변수 로드 (pydantic-settings)
- [x] CORS 설정
- [x] 기본 health check 엔드포인트

---

### Week 2: 데이터 수집기 개발

#### 2.1 KIS API 수집기 (`collectors/kis_api.py`)
- [x] KIS API 인증 토큰 발급 (자동 갱신)
- [x] 주가 조회 함수 (`get_current_price`)
- [x] 일별 시세 조회 함수 (`get_daily_prices`)
- [x] 거래량 조회 함수
- [x] API 에러 핸들링 및 재시도 로직 (3회)
- [x] Rate limit 처리 (50ms 간격)

#### 2.2 pykrx 백업 수집기 (`collectors/pykrx_collector.py`)
- [x] pykrx를 이용한 주가 조회 (백업)
- [x] KIS API 실패 시 자동 fallback
- [x] 통합 수집기 (`collectors/price_collector.py`)

#### 2.3 네이버금융 크롤러 (`collectors/naver_finance.py`)
- [x] 종목 기본 정보 크롤링 (PER, PBR, PSR)
- [x] 재무제표 크롤링 (매출, 영업이익, ROE)
- [x] 업종평균 데이터 크롤링
- [x] 배당정보 크롤링
- [x] 부채비율, 유동비율 크롤링
- [x] 요청 딜레이 및 캐싱 적용
- [x] User-Agent 로테이션

#### 2.4 구글 트렌드 수집기 (`collectors/google_trends.py`)
- [x] pytrends 설정
- [x] 종목명 검색 트렌드 조회
- [x] 최근 30일 트렌드 데이터 수집
- [x] 데이터 부족 시 중립(50%) 처리
- [x] 트렌드 점수 계산 (8점 만점)

#### 2.5 뉴스 수집기 (`collectors/news_collector.py`)
- [x] 네이버 증권 뉴스 크롤링 (iframe)
- [x] 종목별 최근 뉴스 수집
- [x] 종목명 기반 관련성 필터링
- [x] 주가 영향 키워드 필터링 (긍/부정/영향도)
- [x] `.env` 기반 키워드 설정 (`NEWS_KEYWORDS`)
- [x] OpenAI 감정분석 연동 (gpt-4o-mini)
- [x] 뉴스 점수 계산 (12점 만점)

#### 2.6 데이터 동기화 (`db/sync.py`)
- [x] SQLite ↔ Supabase 종목코드 매핑
- [x] 시세 데이터 → 분석 결과 동기화 함수
- [x] 동기화 상태 조회 함수
- [x] 동기화 필요 종목 탐지

---

### Week 3: 분석 엔진 개발

#### 3.1 기술지표 계산 (`analyzers/indicators.py`)
- [x] 이동평균 계산 (MA5, MA20, MA60, MA120)
- [x] RSI(14) 계산
- [x] MACD 계산 (12, 26, 9)
- [x] 거래량 비율 계산
- [x] 기술지표 SQLite 캐싱

#### 3.2 기술분석 서비스 (`services/technical.py`)
- [x] `calc_ma_arrangement()` - MA 배열 점수 (6점)
- [x] `calc_ma_divergence()` - MA 이격도 점수 (6점)
- [x] `calc_rsi_score()` - RSI 점수 (5점)
- [x] `calc_macd_score()` - MACD 점수 (5점)
- [x] `calc_volume_score()` - 거래량 점수 (8점)
- [x] `calculate_technical_score()` - 기술분석 총점 (30점)

#### 3.3 기본분석 서비스 (`services/fundamental.py`)
- [x] `calc_per_score()` - PER 점수 (8점, 적자 0점)
- [x] `calc_pbr_score()` - PBR 점수 (7점)
- [x] `calc_psr_score()` - PSR 점수 (5점)
- [x] `calc_growth_score()` - 성장률 점수 (6점 x 2)
- [x] `calc_roe_score()` - ROE 점수 (5점)
- [x] `calc_margin_score()` - 영업이익률 점수 (5점)
- [x] `calc_debt_ratio_score()` - 부채비율 점수 (4점)
- [x] `calc_current_ratio_score()` - 유동비율 점수 (4점)
- [x] `calculate_fundamental_score()` - 기본분석 총점 (50점)

#### 3.4 감정분석 서비스 (`services/sentiment.py`)
- [x] 뉴스 감정 점수 계산 (10점)
- [x] 뉴스 영향도 점수 계산 (6점)
- [x] 뉴스 양 점수 계산 (4점)
- [x] 데이터 부족 시 중립 처리

#### 3.5 OpenAI 감정분석 (`analyzers/openai_sentiment.py`)
- [x] OpenAI API 클라이언트 설정
- [x] 뉴스 감정분석 프롬프트 작성
- [x] 감정 → 점수 변환
- [x] API 비용 최적화 (gpt-4o-mini)
- [x] 뉴스 종합 요약 분석

#### 3.6 유동성 리스크 계산 (`services/liquidity.py`)
- [x] `calc_trading_value_penalty()` - 거래대금 감점 (-3점)
- [x] `calc_volatility_penalty()` - 거래량 변동성 감점 (-2점)
- [x] `calculate_liquidity_penalty()` - 유동성 총 감점 (-5점)

#### 3.7 점수 통합 서비스 (`services/scoring.py`)
- [x] `calculate_total_score()` - 종합 점수 계산
- [x] 등급 판정 (A+, A, B+, B, C+, C, D, F)
- [x] 분석 결과 Supabase 저장
- [x] 분석 이력 관리

---

### Week 4: React 대시보드 MVP

#### 4.1 프로젝트 초기 설정
- [x] Vite + React + TypeScript 프로젝트 생성
- [x] Tailwind CSS 설정
- [x] Zustand 상태관리 설정
- [x] React Query 설정
- [x] Axios API 클라이언트 설정

#### 4.2 공통 컴포넌트 (`components/common/`)
- [x] `Layout.tsx` - 레이아웃 래퍼
- [x] `Header.tsx` - 헤더 네비게이션
- [x] `Sidebar.tsx` - 사이드바 메뉴
- [x] `Loading.tsx` - 로딩 스피너
- [x] `ErrorBoundary.tsx` - 에러 처리

#### 4.3 대시보드 컴포넌트 (`components/dashboard/`)
- [x] `StockTable.tsx` - 종목 리스트 테이블
  - [x] 정렬 기능 (점수, 이름, 업종)
  - [x] 페이지네이션
- [x] `ScoreCard.tsx` - 점수 카드 컴포넌트
- [x] `FilterPanel.tsx` - 필터 패널
  - [x] 업종 필터
  - [x] 점수대 필터
  - [x] 적자기업 제외 옵션

#### 4.4 상세 페이지 컴포넌트
- [x] `StockDetailPage.tsx` - 종목 상세 페이지
  - [x] 종목 정보 표시
  - [x] 점수 breakdown 표시
  - [x] 기술지표 표시

#### 4.5 차트 컴포넌트
- [x] Recharts 연동 (ScoreCard에 내장)
- [x] `PriceChart.tsx` - 주가 차트 (SQLite 가격 데이터 기반)
  - [x] 일별/주별/월별 시세 표시
  - [x] 이동평균선 (MA5, MA20, MA60, MA120) 오버레이
  - [x] 기간 선택 (1개월/3개월/6개월/1년)
- [ ] `CandlestickChart.tsx` - 캔들스틱 차트 *(Phase 2로 이동)*

#### 4.6 페이지 (`pages/`)
- [x] `Dashboard.tsx` - 메인 대시보드
- [x] `StockDetailPage.tsx` - 종목 상세 페이지
  - [x] 기술지표 상세 표시 (MA, RSI, MACD)
  - [x] 지표별 툴팁 설명 추가
  - [x] 탭 기반 분석 상세 (기술/기본/감정)

#### 4.7 API 연동 (`services/api.ts`)
- [x] 종목 리스트 조회 API
- [x] 종목 상세 조회 API
- [x] 분석 결과 조회 API
- [x] 뉴스 목록/수집/평점 API

#### 4.8 Backend API 엔드포인트
- [x] `GET /api/stocks` - 종목 리스트 (필터, 정렬, 페이징)
- [x] `GET /api/stocks/{code}` - 종목 상세
- [x] `GET /api/stocks/{code}/history` - 주가 히스토리
- [x] `GET /api/stocks/sectors` - 업종 목록
- [x] `GET /api/stocks/compare` - 종목 비교
- [x] `GET /api/analysis/{code}` - 종목별 분석 상세
- [x] `GET /api/analysis/ranking` - 점수 순위
- [x] `POST /api/analysis/{code}/run` - 분석 실행
- [x] `POST /api/analysis/batch` - 일괄 분석
- [x] `GET /api/analysis/{code}/commentary` - LLM 분석 코멘터리

---

### Week 4+: 고급 기능 확장

#### 4.9 LLM 분석 코멘터리 (`services/commentary.py`)
- [x] OpenAI gpt-4o-mini 연동
- [x] 분석 결과 기반 한국어 해설 생성
- [x] 기술/기본/감정분석 종합 요약
- [x] 투자 의견 및 리스크 요인 생성
- [x] `AnalysisCommentary.tsx` - 코멘터리 표시 컴포넌트

#### 4.10 수동 뉴스 평점 시스템 (Manual News Rating)
- [x] **Supabase 스키마 (`news_ratings_anal` 테이블)**
  - [x] 테이블 생성 (id, stock_id, title, link, press, news_date)
  - [x] 평점 필드 (rating: -10 ~ +10, is_rated)
  - [x] 자동 감정 필드 (auto_sentiment, auto_impact)
  - [x] RLS 정책 설정 (public read/write, service_role full)
- [x] **Backend 뉴스 평점 API**
  - [x] `GET /api/analysis/{code}/news` - 뉴스 목록 조회
  - [x] `POST /api/analysis/{code}/news/collect` - 네이버 뉴스 수집 (30일, 50건)
  - [x] `PUT /api/analysis/{code}/news/{id}/rate` - 평점 업데이트
  - [x] `GET /api/analysis/{code}/sentiment-score` - 평점 기반 감정 점수
- [x] **수동 평점 → 감정분석 점수 변환**
  - [x] `supabase_db.calculate_sentiment_from_ratings()` - 평균 평점 계산
  - [x] 점수 변환 로직: -10~+10 → 0~20점
  - [x] 0점(무관 뉴스) 제외 처리
- [x] **Frontend 뉴스 평점 UI (`NewsRating.tsx`)**
  - [x] 뉴스 목록 표시 (자동 감정/영향도 배지)
  - [x] 평점 버튼 (-10, -7, -5, -3, 0, +3, +5, +7, +10)
  - [x] 실시간 점수 업데이트 (React Query mutation)
  - [x] 평점 완료/미완료 건수 표시
  - [x] 뉴스 수집 버튼

#### 4.11 수동 평점 기반 점수 통합
- [x] **Scoring Service 수정 (`services/scoring.py`)**
  - [x] `get_manual_sentiment_score()` - 수동 평점 조회 함수
  - [x] 수동 평점 우선 사용 로직 (rated_count > 0)
  - [x] `sentiment_source` 필드 추가 (manual/auto)
- [x] **Analysis API 수정 (`api/analysis.py`)**
  - [x] `_get_sentiment_source()` - 출처 확인 함수
  - [x] DB 결과 포맷팅 시 수동 평점 확인
  - [x] 총점 재계산 (수동 평점 사용 시)
  - [x] API 응답에 `sentimentSource`, `manualRating` 포함
- [x] **Frontend 출처 표시**
  - [x] `TotalScoreCard` - 감정분석 "수동" 배지
  - [x] `ScoreCard` - 제목에 "(수동)" 표시
  - [x] `SentimentAnalysisTab` - 수동/자동 출처 배지
  - [x] 수동 평점 적용 시 안내 메시지
  - [x] TypeScript 타입 업데이트 (`sentimentSource`, `manualRating`)

---

## Phase 2: 확장 (4주)

### Week 5: 종목 비교 & 히스토리

#### 5.1 종목 비교 기능 (`ComparePage.tsx`)
- [x] 비교 대상 종목 선택 UI (최대 4개)
  - [x] 종목 검색 드롭다운
  - [x] 선택 종목 태그 표시/삭제
- [x] 비교 테이블 컴포넌트
  - [x] 현재가, 등락률
  - [x] 총점, 등급
  - [x] 기술/기본/감정분석 점수 (ScoreBar)
  - [x] 세부 항목별 점수 (MA배열, RSI, MACD, PER, PBR, ROE)
- [x] `GET /api/stocks/compare` API

#### 5.2 분석 히스토리 조회 (`HistoryPage.tsx`)
- [x] 과거 분석 결과 조회 API (`GET /api/analysis/{code}/history`)
- [x] 기간 선택 (7일/30일/90일/1년)
- [x] 포트폴리오 전체 점수 추이 차트 (평균/최고/최저)
- [x] 종목 선택 패널 (검색 기능)
- [x] 개별 종목 점수 추이 차트
- [x] 통계 카드 (현재점수, 기간변화, 평균, 최고/최저)
- [x] 히스토리 테이블 (날짜, 점수, 변화)

---

### Week 6: 백테스팅 모듈

#### 6.1 백테스팅 엔진
- [ ] 과거 데이터 기반 점수 재계산
- [ ] 점수 기반 매수/매도 시뮬레이션
- [ ] 수익률 계산

#### 6.2 백테스팅 UI
- [ ] 기간 선택 UI
- [ ] 전략 파라미터 설정
- [ ] 결과 차트 (수익률 곡선)
- [ ] 성과 지표 표시 (샤프비율, MDD 등)

---

### Week 7: 알림 & 다크모드

#### 7.1 알림 기능
- [ ] 점수 변동 알림 설정
- [ ] 이메일 알림 (선택)
- [ ] 브라우저 푸시 알림

#### 7.2 다크모드
- [ ] Tailwind 다크모드 설정
- [ ] 테마 토글 버튼
- [ ] 차트 다크모드 스타일

---

### Week 8: 포트폴리오 시뮬레이션 & 최적화

#### 8.1 포트폴리오 시뮬레이션
- [ ] 가상 포트폴리오 생성
- [ ] 종목 추가/제거
- [ ] 비중 조절
- [ ] 포트폴리오 점수 계산

#### 8.2 성능 최적화
- [ ] Redis 캐싱 적용
- [ ] API 응답 최적화
- [ ] 프론트엔드 번들 최적화
- [ ] 이미지/자산 최적화

#### 8.3 배포 준비
- [ ] Docker 이미지 빌드
- [ ] docker-compose 설정
- [ ] 환경별 설정 분리 (dev/prod)
- [ ] CI/CD 파이프라인 (선택)

---

## 데이터 수집 태스크 (초기 1회)

### 포트폴리오 데이터 입력
- [ ] VIP한국형가치투자 종목 44개 입력
  - [ ] 종목코드 매핑
  - [ ] 보유수량, 평가금액, 비중 입력
  - [ ] 발행주식수 대비 보유비율 계산
- [ ] 미분류 업종 수동 매핑
  - [ ] 달바글로벌 → (화장품/소비재)
  - [ ] 동방메디컬 → (헬스케어/의료기기)
  - [ ] 에스엠씨지 → (미디어/엔터)
- [ ] 우선주(현대차우) 제외 처리

### 업종평균 데이터 수집
- [ ] 네이버금융 업종별 평균 크롤링
- [ ] sector_averages 테이블 초기 데이터 입력

---

## 테스트 태스크

### 단위 테스트
- [ ] 기술분석 점수 계산 테스트
- [ ] 기본분석 점수 계산 테스트
- [ ] 감정분석 점수 계산 테스트
- [ ] 유동성 감점 계산 테스트
- [ ] 총점 계산 테스트

### 통합 테스트
- [ ] API 엔드포인트 테스트
- [ ] 데이터 수집 → 분석 → 저장 플로우 테스트
- [ ] SQLite ↔ Supabase 동기화 테스트

### E2E 테스트 (선택)
- [ ] 대시보드 렌더링 테스트
- [ ] 필터/정렬 기능 테스트
- [ ] 상세 페이지 테스트

---

## 문서화 태스크

- [ ] README.md 작성
- [ ] API 문서 (Swagger/OpenAPI)
- [ ] 환경 설정 가이드
- [ ] 배포 가이드

---

## 진행 상황 요약

| Phase | 주차 | 상태 | 완료율 |
|-------|------|------|--------|
| Phase 1 | Week 1 | ✅ 완료 | 100% |
| Phase 1 | Week 2 | ✅ 완료 | 100% |
| Phase 1 | Week 3 | ✅ 완료 | 100% |
| Phase 1 | Week 4 | ✅ 완료 | 100% |
| Phase 1 | Week 4+ | ✅ 완료 | 100% |
| Phase 2 | Week 5 | ✅ 완료 | 100% |
| Phase 2 | Week 6 | ⬜ 대기 | 0% |
| Phase 2 | Week 7 | ⬜ 대기 | 0% |
| Phase 2 | Week 8 | ⬜ 대기 | 0% |

---

## 최근 완료 내역 (2025.02.01)

### LLM 분석 코멘터리
- OpenAI gpt-4o-mini를 활용한 한국어 분석 해설 생성
- 기술/기본/감정분석 종합 요약 및 투자 의견 제공

### 수동 뉴스 평점 시스템
- 자동 감정분석 대신 사용자가 직접 뉴스를 평가하는 시스템
- -10(매우 부정) ~ +10(매우 긍정) 평점 부여
- 무관한 뉴스는 0점으로 제외 처리

### 수동 평점 기반 점수 통합
- 수동 평점이 1건 이상 있으면 자동분석 대체
- 총점에 수동 감정분석 점수 반영
- UI에서 "수동"/"자동" 출처 구분 표시

### 종목 비교 기능 (Week 5)
- 최대 4개 종목 동시 비교 UI (`ComparePage.tsx`)
- 가격, 등락률, 총점, 등급 비교 테이블
- 기술/기본/감정분석 점수 ScoreBar 시각화
- 세부 항목별 점수 비교 (MA배열, RSI, MACD, PER, PBR, ROE)

### 분석 히스토리 조회 (Week 5)
- 기간별 분석 히스토리 조회 (7일/30일/90일/1년)
- 포트폴리오 전체 점수 추이 차트 (평균/최고/최저)
- 개별 종목 점수 추이 차트 및 통계 카드
- 히스토리 테이블 (날짜, 점수, 변화)

---

**범례**:
- ⬜ 대기
- 🔄 진행중
- ✅ 완료
- ❌ 보류/취소
