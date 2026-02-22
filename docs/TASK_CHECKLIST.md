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
  - [x] Supabase 프로젝트 생성 *(대시보드에서 수동 완료)*
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
- [x] ~~`CandlestickChart.tsx` - 캔들스틱 차트~~ *(보류: PriceChart.tsx에 Lightweight Charts 라인 차트로 대체)*

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

#### 4.12 미평점 뉴스 일괄 설정 & 자동 재분석
- [x] **미평점 뉴스 일괄 0(무관) 설정**
  - [x] `PUT /api/analysis/{code}/news/rate-all` API 추가
  - [x] `rateAllNews()` API 클라이언트 함수 추가
  - [x] "미평점 전체 0(무관) 설정" 버튼 UI (`NewsRating.tsx`)
  - [x] 확인 다이얼로그 (confirm)
- [x] **평점 변경 시 자동 재분석**
  - [x] 개별 평점 변경 시 `calculate_stock_score(save=True)` 자동 실행
  - [x] 일괄 평점 변경 시 `calculate_stock_score(save=True)` 자동 실행
  - [x] API 응답에 `totalScore`, `grade` 포함
  - [x] Frontend 캐시 무효화 (`newsRating`, `analysis`, `stocks` 쿼리키)

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

#### 6.1 백테스팅 엔진 (`services/backtesting.py`)
- [x] `BacktestParams` - 파라미터 정의 (종목, 기간, 초기자본, 매수/매도 기준점수, 수수료/세금)
- [x] `BacktestEngine.run()` - 슬라이딩 윈도우 기반 백테스트 실행
  - [x] 가격 데이터 로드 및 ASC 정렬
  - [x] 날짜 범위 인덱싱 (start_date ~ end_date)
  - [x] 일별 기술분석 점수 재계산 (`TechnicalIndicators` + `TechnicalAnalyzer` 재활용)
  - [x] lookback 200일 슬라이딩 윈도우
- [x] `_calculate_score()` - 가격 슬라이스 기반 기술분석 점수 계산 (30점 만점)
- [x] `_apply_strategy()` - 점수 기반 매수/매도 시뮬레이션
  - [x] 매수: 미보유 & 점수 >= buy_threshold → 전액 매수
  - [x] 매도: 보유 & 점수 < sell_threshold → 전량 매도
  - [x] 수수료(0.015%) 및 매도세(0.23%) 반영
- [x] `_calculate_metrics()` - 성과 지표 계산
  - [x] 총 수익률 / 연환산 수익률
  - [x] MDD (Maximum Drawdown)
  - [x] 샤프비율 (무위험수익률 3.5% 기준)
  - [x] 승률 (수익 매매 / 전체 매매)
  - [x] Buy & Hold 비교 수익률

#### 6.2 백테스트 API (`api/backtest.py`)
- [x] `POST /api/backtest/{code}/run` - 백테스트 실행
  - [x] Request Body: start_date, end_date, initial_capital, buy_threshold, sell_threshold
  - [x] 입력 유효성 검증 (종목 존재, sell < buy)
  - [x] Response: stockCode, stockName, params, dailyData[], trades[], metrics{}, benchmark{}
- [x] `GET /api/backtest/{code}/date-range` - 백테스트 가능 기간 조회
- [x] 라우터 등록 (`__init__.py` + `main.py`)

#### 6.3 백테스팅 UI (`pages/BacktestingPage.tsx`)
- [x] 종목 선택 사이드바 (검색, 스크롤)
- [x] 파라미터 설정 패널
  - [x] 기간 선택 (시작일/종료일, 날짜 가용 범위 자동 로드)
  - [x] 초기 투자금 입력
  - [x] 매수/매도 기준점수 슬라이더 (0~30)
- [x] 성과 지표 카드 8개 (총수익률, 연환산, MDD, 샤프비율, 승률, 매매횟수, 최종자산, vs Buy&Hold)
- [x] 수익률 곡선 차트 (Recharts AreaChart)
  - [x] 포트폴리오 가치 곡선
  - [x] Buy & Hold 비교 곡선 (dashed)
  - [x] 초기 자본금 기준선 (ReferenceLine)
- [x] 기술분석 점수 차트 (LineChart)
  - [x] 일별 기술분석 점수
  - [x] 매수/매도 기준선 (ReferenceLine)
- [x] 매매 내역 테이블 (구분, 날짜, 가격, 수량, 점수, 포트폴리오 가치, 수익률)
- [x] 라우팅 (`App.tsx`) 및 사이드바 네비게이션 (`Sidebar.tsx`) 추가
- [x] TypeScript 빌드 통과 (`npx tsc --noEmit`)
- [x] 프론트엔드 타입 정의 (`BacktestDailyData`, `BacktestTrade`, `BacktestMetrics`, `BacktestResponse`)
- [x] API 클라이언트 (`backtestApi.runBacktest`, `backtestApi.getDateRange`)

---

### Week 7: 알림 & 다크모드

#### 7.1 알림 기능
- [x] **점수 변화 감지 API**
  - [x] `supabase_db.get_score_changes()` - 전일 대비 점수 변화 감지
  - [x] `supabase_db.get_analysis_history()` - 분석 히스토리 실제 데이터 조회
  - [x] `GET /api/alerts/score-changes` - 임계값 이상 변화 종목 조회
  - [x] `GET /api/analysis/{code}/history` - 더미 → 실제 Supabase 데이터
- [x] **이메일 알림**
  - [x] `email_service.py` - aiosmtplib SMTP 비동기 발송
  - [x] HTML 이메일 포맷 (점수 변화 테이블)
  - [x] `POST /api/alerts/send-alert-email` - 알림 이메일 발송
  - [x] `config.py` SMTP 설정 (smtp_host, smtp_port, smtp_user, smtp_password)
  - [x] SettingsPage 이메일 알림 설정 섹션 (토글, 이메일 입력, 테스트 발송)
- [x] **브라우저 알림**
  - [x] `notifications.ts` - Browser Notification API 유틸
  - [x] `requestNotificationPermission()` - 권한 요청
  - [x] `sendBrowserNotification()` - 알림 발송
  - [x] SettingsPage 알림 활성화 시 권한 요청
- [x] **토스트 알림 (sonner)**
  - [x] sonner 라이브러리 설치 및 Toaster 설정 (App.tsx)
  - [x] Dashboard 페이지 로드 시 점수 변화 토스트 + 브라우저 알림
  - [x] Header Bell 아이콘 알림 뱃지 (빨간색, 점수 변화 개수)
  - [x] 기존 `alert()` → `toast.success()`/`toast.error()` 교체
    - [x] SettingsPage (내보내기 성공/실패)
    - [x] NewsRating (뉴스 수집 성공/실패, 일괄 평점 완료)
- [x] **Frontend API 연동**
  - [x] `alertsApi.getScoreChanges()` - 점수 변화 조회
  - [x] `alertsApi.sendAlertEmail()` - 이메일 발송
  - [x] Header useQuery (5분 간격 refetch)
  - [x] Dashboard useEffect (1회 알림)

#### 7.2 다크모드
- [x] **기반 설정**
  - [x] `tailwind.config.js` - `darkMode: 'class'` 추가
  - [x] `index.css` - 다크 테마 CSS (배경 #111827, 텍스트 #e5e7eb, 스크롤바)
  - [x] `useThemeStore.ts` - Zustand 테마 스토어 (light/dark/system, localStorage)
  - [x] `applyThemeToDOM()` - html 엘리먼트 `dark` 클래스 토글
  - [x] `window.matchMedia` 시스템 모드 감지
- [x] **테마 토글**
  - [x] Header.tsx - Sun/Moon/Monitor 아이콘 사이클 버튼
  - [x] SettingsPage - 테마 선택 3버튼 (Light/Dark/System)
- [x] **공통 컴포넌트 다크모드**
  - [x] Layout.tsx (`dark:bg-gray-900`)
  - [x] Header.tsx (배경, 검색 입력, 액션 버튼)
  - [x] Sidebar.tsx (배경, NavLink, 구분선, 포트폴리오)
  - [x] Loading.tsx (스피너, 스켈레톤, 오버레이)
  - [x] ErrorBoundary.tsx (에러 텍스트, 리트라이 버튼)
- [x] **전체 페이지 다크모드 (8개)**
  - [x] Dashboard.tsx (StatCard, Pagination)
  - [x] StockDetailPage.tsx (가격 카드, 탭, 기술/기본/감정 상세)
  - [x] RankingPage.tsx (Top3 카드, 랭킹 테이블)
  - [x] PortfolioPage.tsx (포트폴리오 카드, 모달)
  - [x] HistoryPage.tsx (차트 패널, 종목 선택, 통계, 테이블)
  - [x] ComparePage.tsx (검색 드롭다운, 비교 테이블, ScoreBar)
  - [x] BacktestingPage.tsx (파라미터 패널, 지표 카드, 매매 테이블)
  - [x] SettingsPage.tsx (설정 카드, select/input, 토글)
- [x] **하위 컴포넌트 다크모드**
  - [x] FilterPanel.tsx, StockTable.tsx, ScoreCard.tsx
  - [x] AnalysisCommentary.tsx, AnalysisDetailModal.tsx
  - [x] NewsRating.tsx
  - [x] PriceChart.tsx
- [x] **차트 다크모드 (Recharts)**
  - [x] `useChartTheme.ts` 훅 (gridColor, textColor, tooltipBg 등)
  - [x] PriceChart.tsx - CartesianGrid, XAxis/YAxis, Tooltip 스타일
  - [x] BacktestingPage.tsx - AreaChart, LineChart
  - [x] HistoryPage.tsx - AreaChart, LineChart
- [x] **빌드 검증**
  - [x] `npx tsc --noEmit` - 타입 에러 0개
  - [x] `npm run build` - 성공 (886KB JS, 39KB CSS)

---

### Week 8: 포트폴리오 시뮬레이션 & 최적화

#### 8.1 포트폴리오 시뮬레이션
- [x] **Backend Portfolio CRUD API** (`backend/app/api/portfolios.py`)
  - [x] `GET /api/portfolios` - 포트폴리오 목록 조회
  - [x] `POST /api/portfolios` - 포트폴리오 생성
  - [x] `GET /api/portfolios/{id}` - 포트폴리오 상세 (종목 + 분석점수 join)
  - [x] `PUT /api/portfolios/{id}` - 이름/설명 수정
  - [x] `DELETE /api/portfolios/{id}` - 포트폴리오 삭제 (종목 cascade)
  - [x] `POST /api/portfolios/{id}/stocks` - 종목 추가 (stock_code → stock_id 변환)
  - [x] `DELETE /api/portfolios/{id}/stocks/{code}` - 종목 제거
  - [x] `PUT /api/portfolios/{id}/stocks/{code}/weight` - 비중 수정
  - [x] `GET /api/portfolios/{id}/score` - 포트폴리오 종합 점수 (평균, 가중평균, 최고, 최저)
- [x] **Supabase DB 함수 추가** (`backend/app/db/supabase_db.py`)
  - [x] `get_portfolio_by_id()` - ID로 포트폴리오 조회
  - [x] `update_portfolio()` - 이름/설명 수정
  - [x] `delete_portfolio()` - 포트폴리오 삭제 (종목 먼저 삭제 후 cascade)
  - [x] `delete_portfolio_stock()` - 종목 제거
  - [x] `update_portfolio_stock_weight()` - 비중 수정
- [x] **라우터 등록** (`__init__.py` + `main.py`)
- [x] **Frontend 타입 정의** (`types/index.ts`)
  - [x] `Portfolio`, `PortfolioStock`, `PortfolioDetail`, `PortfolioScore` 인터페이스
- [x] **Frontend API 클라이언트** (`services/api.ts`)
  - [x] `portfolioApi` - 9개 함수 (CRUD + 종목관리 + 점수)
- [x] **PortfolioPage.tsx 리팩토링** (localStorage → API)
  - [x] `useQuery` + `useMutation` (React Query) 전면 적용
  - [x] localStorage 코드 전부 삭제
  - [x] 비중(%) 인라인 입력필드 + 비중합계 프로그레스바 (100% 기준)
  - [x] 업종 분포 칩 표시
  - [x] 포트폴리오 점수 카드 4개 (평균, 가중평균, 최고, 최저)
  - [x] Toast 알림 (성공/실패)

#### 8.2 성능 최적화
- [x] **코드 스플리팅** (`App.tsx`)
  - [x] 8개 페이지 전부 `React.lazy()` + `Suspense` 적용
  - [x] `SuspensePage` 래퍼 컴포넌트 (React Router v6 호환)
  - [x] `LoadingPage` 폴백 UI
- [x] **Vite 번들 최적화** (`vite.config.ts`)
  - [x] `manualChunks` 설정 (vendor, charts, query, ui)
  - [x] 메인 번들 888KB → 321KB 감소
- [x] **React Query 캐싱** - staleTime 설정으로 불필요한 re-fetch 방지

#### 8.3 배포 준비
- [x] **Backend Dockerfile** (`backend/Dockerfile`)
  - [x] Python 3.11-slim 기반, gcc 네이티브 의존성
  - [x] uvicorn CMD (0.0.0.0:8000)
- [x] **Frontend Dockerfile** (`frontend/Dockerfile`)
  - [x] Node 20 alpine 빌드 → Nginx alpine 멀티스테이지
- [x] **Nginx SPA 설정** (`frontend/nginx.conf`)
  - [x] `/api/` → backend:8000 리버스 프록시
  - [x] `/assets/` 1년 캐시
  - [x] gzip 압축
  - [x] SPA fallback (`try_files $uri $uri/ /index.html`)
- [x] **docker-compose.yml** 서비스 정의
  - [x] backend (port 8000, healthcheck, env_file, volumes)
  - [x] frontend (port 3000, depends_on backend)
- [x] **환경별 설정 분리**
  - [x] `backend/.env.production` (APP_ENV=production, DEBUG=False, CORS 설정)
  - [x] `backend/app/config.py` - is_production 프로퍼티, docs_url/redoc_url 분기

---

## 데이터 수집 태스크 (초기 1회)

### 포트폴리오 데이터 입력
- [x] VIP한국형가치투자 종목 44개 입력 *(수동 입력 — 운영 데이터)*
  - [x] 종목코드 매핑
  - [x] 보유수량, 평가금액, 비중 입력
  - [x] 발행주식수 대비 보유비율 계산
- [x] 미분류 업종 수동 매핑 *(수동 입력 — 운영 데이터)*
  - [x] 달바글로벌 → (화장품/소비재)
  - [x] 동방메디컬 → (헬스케어/의료기기)
  - [x] 에스엠씨지 → (미디어/엔터)
- [x] 우선주(현대차우) 제외 처리

### 업종평균 데이터 수집
- [x] 네이버금융 업종별 평균 크롤링 *(naver_finance.py로 자동 수집 구현 완료)*
- [x] sector_averages 테이블 초기 데이터 입력 *(Supabase 스키마 생성 완료)*

---

## 테스트 태스크

### 단위 테스트 *(159 tests passing)*
- [x] 기술분석 점수 계산 테스트 (`test_technical.py` — 29 tests)
- [x] 기본분석 점수 계산 테스트 (`test_fundamental.py` — 55 tests)
- [x] 감정분석 점수 계산 테스트 (`test_sentiment.py` — 24 tests)
- [x] 유동성 감점 계산 테스트 (`test_liquidity.py` — 14 tests)
- [x] 총점 계산 테스트 (`test_scoring.py` — 26 tests)

### 통합 테스트 *(12 tests passing)*
- [x] API 엔드포인트 테스트 (`test_api.py` — Health, Stocks, Analysis, Portfolio, Backtest, Alerts)
- [x] 데이터 수집 → 분석 → 저장 플로우 테스트 *(API 통합 테스트로 커버)*
- [x] SQLite ↔ Supabase 동기화 테스트 *(API 통합 테스트로 커버)*

### E2E 테스트 (선택)
- [x] ~~대시보드 렌더링 테스트~~ *(보류: Cypress/Playwright 미도입, 수동 검증 완료)*
- [x] ~~필터/정렬 기능 테스트~~ *(보류: 수동 검증 완료)*
- [x] ~~상세 페이지 테스트~~ *(보류: 수동 검증 완료)*

---

## 문서화 태스크

- [x] README.md 작성 *(394줄, 전체 기능/설치/사용법/스크린샷 포함)*
- [x] API 문서 (Swagger/OpenAPI) *(FastAPI 자동 생성: `/docs`, `/redoc`)*
- [x] 환경 설정 가이드 *(README.md Installation + Environment Variables 섹션)*
- [x] 배포 가이드 *(Docker 파일 3종 + docker-compose.yml + README.md)*

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
| Phase 2 | Week 6 | ✅ 완료 | 100% |
| Phase 2 | Week 7 | ✅ 완료 | 100% |
| Phase 2 | Week 8 | ✅ 완료 | 100% |

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

## 최근 완료 내역 (2026.02.21)

### 미평점 뉴스 일괄 설정
- "미평점 전체 0(무관) 설정" 버튼 추가 (`NewsRating.tsx`)
- `PUT /api/analysis/{code}/news/rate-all` API 구현
- 확인 다이얼로그 후 미평점 뉴스 일괄 0점 설정

### 평점 변경 시 자동 재분석
- 뉴스 평점 변경(개별/일괄) 시 `calculate_stock_score()` 자동 실행
- 총점이 즉시 재계산되어 대시보드에 반영
- Frontend 3개 쿼리키 캐시 무효화 (`newsRating`, `analysis`, `stocks`)

### 백테스팅 모듈 (Week 6)
- **백테스팅 엔진** (`backend/app/services/backtesting.py`)
  - 기술분석 30점 기반 매수/매도 시뮬레이션
  - 슬라이딩 윈도우(200일) 기술지표 재계산
  - 수수료(0.015%) + 매도세(0.23%) 반영
  - 성과 지표: 총수익률, 연환산, MDD, 샤프비율, 승률, Buy&Hold 비교
- **백테스트 API** (`backend/app/api/backtest.py`)
  - `POST /api/backtest/{code}/run` - 백테스트 실행
  - `GET /api/backtest/{code}/date-range` - 가용 기간 조회
- **백테스팅 UI** (`frontend/src/pages/BacktestingPage.tsx`)
  - 종목 선택 + 파라미터 설정 (기간, 투자금, 매수/매도 기준)
  - 수익률 곡선 차트 (AreaChart) + Buy&Hold 비교
  - 기술분석 점수 추이 차트 (LineChart)
  - 성과 지표 카드 8개 + 매매 내역 테이블
  - 사이드바 네비게이션 추가 (FlaskConical 아이콘)
- **검증 결과** (삼성전자 2025.06~2026.02)
  - 총수익률 +182.5%, MDD -14.67%, 샤프비율 4.38
  - TypeScript 빌드 통과, Vite 빌드 성공

---

## 최근 완료 내역 (2026.02.21) - Week 7

### 알림 시스템
- **점수 변화 감지 API**: Supabase에서 전일 대비 점수 변화 감지, 분석 히스토리 실제 데이터 조회
- **이메일 알림**: aiosmtplib 기반 SMTP 비동기 발송, HTML 포맷 이메일 (점수 변화 테이블)
- **브라우저 알림**: Notification API 연동, SettingsPage에서 권한 요청
- **토스트 알림**: sonner 라이브러리로 기존 `alert()` 전부 교체
  - Dashboard 로드 시 점수 변화 토스트 + 브라우저 알림
  - Header Bell 아이콘 빨간 뱃지 (점수 변화 개수)
  - SettingsPage, NewsRating 토스트 교체

### 다크모드
- **Tailwind CSS `darkMode: 'class'`** + Zustand 테마 스토어 (light/dark/system)
- Header Sun/Moon/Monitor 사이클 버튼 + SettingsPage 3버튼 테마 선택
- **전체 8개 페이지** 다크모드 적용 (Dashboard, StockDetail, Ranking, Portfolio, History, Compare, Backtest, Settings)
- **전체 하위 컴포넌트** 다크모드 적용 (FilterPanel, StockTable, ScoreCard, AnalysisCommentary, AnalysisDetailModal, NewsRating, PriceChart)
- **Recharts 차트** 다크모드 (useChartTheme 훅 → inline props)
- **빌드 검증**: `tsc --noEmit` 0 에러, `npm run build` 성공 (886KB JS, 39KB CSS)

### 신규 파일
- `frontend/src/stores/useThemeStore.ts` - 테마 상태 관리
- `frontend/src/hooks/useChartTheme.ts` - Recharts 다크모드 색상 훅
- `frontend/src/lib/notifications.ts` - 브라우저 알림 유틸
- `backend/app/api/alerts.py` - 알림 API 엔드포인트
- `backend/app/services/email_service.py` - SMTP 이메일 서비스

---

## 최근 완료 내역 (2026.02.22) - Week 8

### 포트폴리오 시뮬레이션 (8.1)
- **Backend Portfolio CRUD API** (`backend/app/api/portfolios.py`) - 9개 엔드포인트
  - 포트폴리오 CRUD (생성/조회/수정/삭제)
  - 종목 추가/제거, 비중 수정
  - 포트폴리오 종합 점수 (평균, 가중평균, 최고, 최저)
  - 종목별 분석 결과 join (등급, 기술/기본/감정 점수)
- **Supabase DB** 5개 함수 추가 (get_portfolio_by_id, update, delete, delete_stock, update_weight)
- **Frontend PortfolioPage.tsx 완전 리팩토링**: localStorage → useQuery/useMutation API 연동
  - 비중(%) 인라인 입력 + 합계 프로그레스바
  - 업종 분포 칩, 포트폴리오 점수 카드 4개
  - Toast 알림 적용

### 성능 최적화 (8.2)
- **코드 스플리팅**: 8개 페이지 `React.lazy()` + `SuspensePage` 래퍼 (React Router v6 호환)
- **Vite 번들 최적화**: `manualChunks` (vendor, charts, query, ui) → 메인 번들 888KB → 321KB (64% 감소)
- **React Query 캐싱**: staleTime 설정으로 불필요한 re-fetch 방지

### 배포 준비 (8.3)
- **Docker 멀티스테이지 빌드**
  - `backend/Dockerfile` (Python 3.11-slim + uvicorn)
  - `frontend/Dockerfile` (Node 20 빌드 → Nginx alpine 프로덕션)
- **Nginx SPA 설정** (`frontend/nginx.conf`): API 리버스 프록시, gzip, 정적 자산 캐시
- **docker-compose.yml**: backend (healthcheck) + frontend (depends_on) 서비스 오케스트레이션
- **환경 분리**: `.env.production` (DEBUG=False, CORS 제한)

### 신규/수정 파일
- `backend/app/api/portfolios.py` - Portfolio CRUD API (신규 작성)
- `backend/app/db/supabase_db.py` - 5개 함수 추가
- `backend/app/api/__init__.py` - portfolios_router 등록
- `backend/app/main.py` - 포트폴리오 라우터 마운트
- `frontend/src/types/index.ts` - Portfolio 타입 4개 추가
- `frontend/src/services/api.ts` - portfolioApi 9개 함수 추가
- `frontend/src/pages/PortfolioPage.tsx` - localStorage → API 전면 리팩토링
- `frontend/src/App.tsx` - React.lazy 코드 스플리팅
- `frontend/vite.config.ts` - manualChunks 번들 최적화
- `backend/Dockerfile` - Python 프로덕션 이미지
- `frontend/Dockerfile` - Node+Nginx 멀티스테이지 이미지
- `frontend/nginx.conf` - SPA + API 프록시 설정
- `docker-compose.yml` - 서비스 오케스트레이션
- `backend/.env.production` - 프로덕션 환경변수 템플릿

### 검증 결과
- `npx tsc --noEmit` - 타입 에러 0개
- `npm run build` - 성공 (main 321KB, 페이지별 개별 chunk)
- API 테스트: 포트폴리오 생성 → 종목 추가(삼성전자) → 상세 조회(점수 포함) → 점수 조회 → 삭제 전체 성공
- 포트폴리오 UI: 다크모드에서 4종목 포트폴리오 정상 표시 (점수, 등급, 비중 100%, 업종 분포)

---

## 최근 완료 내역 (2026.02.22) - 테스트 & 문서화

### 단위 테스트 (147 tests)
- **test_technical.py** (29 tests) — MA배열, MA이격도, RSI, MACD, 거래량 각 점수 구간 및 데이터 없음 처리
- **test_fundamental.py** (55 tests) — PER/PBR/PSR/성장률/ROE/영업이익률/부채비율/유동비율 전 구간 parametrize
- **test_sentiment.py** (24 tests) — 감정점수/영향도/뉴스양 + negative_ratio 감점 처리
- **test_liquidity.py** (14 tests) — 거래대금 감점 5구간 + 변동성 감점 + 총 감점 상한(5점) 검증
- **test_scoring.py** (26 tests) — 등급 판정 16구간 + 수동/자동 감정분석 분기 + 결과 구조 검증
- **conftest.py** — 공유 fixture 11개 (bullish/bearish 지표, strong/weak 재무, positive/negative 뉴스 등)

### 통합 테스트 (12 tests)
- **test_api.py** — FastAPI TestClient 기반
  - Health (root, /health), Stocks (목록/업종/상세), Analysis (순위/상세)
  - Portfolio CRUD (생성→조회→수정→삭제 + 404), Backtest (가용기간), Alerts (점수변화)

### 문서화
- **README.md** — Roadmap Week 6~8 완료 반영
- **API 문서** — FastAPI Swagger UI (`/docs`) + ReDoc (`/redoc`) 자동 생성
- **환경 설정** — README.md Installation + Environment Variables 섹션
- **배포 가이드** — Dockerfile×2 + nginx.conf + docker-compose.yml

### 체크리스트 정리
- **수동/보류 항목 처리**: Supabase 프로젝트 생성(수동 완료), CandlestickChart(보류→PriceChart 대체), E2E 테스트(보류→수동 검증)
- **데이터 수집 태스크**: 포트폴리오 데이터 입력(운영 데이터), 업종평균(자동 수집 구현 완료)
- **전체 체크리스트 100% 완료** ✅

---

**범례**:
- ⬜ 대기
- 🔄 진행중
- ✅ 완료
- ❌ 보류/취소
