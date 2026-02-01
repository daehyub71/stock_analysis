-- ===================================================
-- Stock Analysis Dashboard - Supabase Schema
-- ===================================================
-- Supabase SQL Editor에서 실행하세요.
-- https://supabase.com/dashboard/project/[PROJECT_ID]/sql
-- 테이블명: 기존 stocks와 충돌 방지를 위해 _anal 접미사 사용

-- 1. stocks_anal 테이블 (종목 기본 정보)
CREATE TABLE IF NOT EXISTS stocks_anal (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,          -- 종목코드
    name VARCHAR(100) NOT NULL,                -- 종목명
    sector VARCHAR(50),                        -- 업종
    mapped_sector VARCHAR(50),                 -- 매핑된 업종 (미분류용)
    market VARCHAR(20),                        -- KOSPI/KOSDAQ
    market_cap BIGINT,                         -- 시가총액
    shares_outstanding BIGINT,                 -- 발행주식수
    avg_trading_value BIGINT,                  -- 20일 평균 거래대금
    -- 밸류에이션 지표 (PER/PBR/PSR)
    per DECIMAL(10,2),                         -- PER (주가수익비율)
    pbr DECIMAL(10,2),                         -- PBR (주가순자산비율)
    psr DECIMAL(10,2),                         -- PSR (주가매출비율)
    -- 수익성 지표
    roe DECIMAL(10,2),                         -- ROE (자기자본이익률)
    op_margin DECIMAL(10,2),                   -- 영업이익률
    -- 성장성 지표
    revenue_growth DECIMAL(10,2),              -- 매출성장률 (YoY)
    op_growth DECIMAL(10,2),                   -- 영업이익성장률 (YoY)
    -- 안정성 지표
    debt_ratio DECIMAL(10,2),                  -- 부채비율
    current_ratio DECIMAL(10,2),               -- 유동비율
    -- 기타
    dividend_yield DECIMAL(10,2),              -- 배당수익률
    is_active BOOLEAN DEFAULT TRUE,            -- 활성 여부
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 기존 테이블에 재무 컬럼 추가 (마이그레이션용)
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS per DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS pbr DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS psr DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS roe DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS op_margin DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS revenue_growth DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS op_growth DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS debt_ratio DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS current_ratio DECIMAL(10,2);
-- ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS dividend_yield DECIMAL(10,2);

-- 2. portfolios_anal 테이블 (포트폴리오/기관별)
CREATE TABLE IF NOT EXISTS portfolios_anal (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,                -- 포트폴리오명 (VIP한가투 등)
    source VARCHAR(50),                        -- 출처
    report_date DATE,                          -- 보고서 기준일
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. portfolio_stocks_anal 테이블 (포트폴리오-종목 연결)
CREATE TABLE IF NOT EXISTS portfolio_stocks_anal (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios_anal(id) ON DELETE CASCADE,
    stock_id INTEGER REFERENCES stocks_anal(id) ON DELETE CASCADE,
    quantity BIGINT,                           -- 보유수량
    amount BIGINT,                             -- 평가금액
    weight DECIMAL(5,2),                       -- 포트폴리오 내 비중(%)
    holding_ratio DECIMAL(5,2),                -- 발행주식수 대비 보유비율(%)
    is_concentrated BOOLEAN DEFAULT FALSE,     -- 집중보유 여부 (5% 초과)
    UNIQUE(portfolio_id, stock_id)
);

-- 4. sector_averages_anal 테이블 (업종 평균)
CREATE TABLE IF NOT EXISTS sector_averages_anal (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(50) NOT NULL,
    avg_per DECIMAL(10,2),
    avg_pbr DECIMAL(10,2),
    avg_psr DECIMAL(10,2),
    avg_roe DECIMAL(10,2),
    avg_operating_margin DECIMAL(10,2),
    base_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(sector, base_date)
);

-- 5. analysis_results_anal 테이블 (분석 결과)
CREATE TABLE IF NOT EXISTS analysis_results_anal (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks_anal(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,

    -- 기술분석 (30점)
    tech_ma_arrangement DECIMAL(4,2),          -- MA배열 (6점)
    tech_ma_divergence DECIMAL(4,2),           -- MA이격도 (6점)
    tech_rsi DECIMAL(4,2),                     -- RSI (5점)
    tech_macd DECIMAL(4,2),                    -- MACD (5점)
    tech_volume DECIMAL(4,2),                  -- 거래량 (8점)
    tech_total DECIMAL(5,2),                   -- 기술분석 총점 (30점)

    -- 기본분석 (50점)
    fund_per DECIMAL(4,2),                     -- PER (8점)
    fund_pbr DECIMAL(4,2),                     -- PBR (7점)
    fund_psr DECIMAL(4,2),                     -- PSR (5점)
    fund_revenue_growth DECIMAL(4,2),          -- 매출성장률 (6점)
    fund_profit_growth DECIMAL(4,2),           -- 영업이익성장률 (6점)
    fund_roe DECIMAL(4,2),                     -- ROE (5점)
    fund_margin DECIMAL(4,2),                  -- 영업이익률 (5점)
    fund_debt_ratio DECIMAL(4,2),              -- 부채비율 (4점)
    fund_current_ratio DECIMAL(4,2),           -- 유동비율 (4점)
    fund_total DECIMAL(5,2),                   -- 기본분석 총점 (50점)
    is_loss_company BOOLEAN DEFAULT FALSE,     -- 적자기업 여부

    -- 감정분석 (20점)
    sent_trend DECIMAL(4,2),                   -- 트렌드 (8점)
    sent_news DECIMAL(4,2),                    -- 뉴스감정 (12점)
    sent_total DECIMAL(5,2),                   -- 감정분석 총점 (20점)
    sent_data_insufficient BOOLEAN DEFAULT FALSE,

    -- 유동성 리스크 감점 (최대 -5점)
    liquidity_holding_penalty DECIMAL(4,2),    -- 보유비율 감점 (-3점)
    liquidity_trading_penalty DECIMAL(4,2),    -- 거래대금 감점 (-2점)
    liquidity_total_penalty DECIMAL(4,2),      -- 유동성 감점 합계 (-5점)

    -- 총점
    total_score DECIMAL(5,2),                  -- 종합점수 (100점 - 유동성감점)
    grade VARCHAR(2),                          -- 등급 (A+, A, B+, B, C+, C, D, F)

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(stock_id, analysis_date)
);

-- ===================================================
-- 인덱스 생성
-- ===================================================

CREATE INDEX IF NOT EXISTS idx_stocks_anal_code ON stocks_anal(code);
CREATE INDEX IF NOT EXISTS idx_stocks_anal_sector ON stocks_anal(sector);
CREATE INDEX IF NOT EXISTS idx_stocks_anal_active ON stocks_anal(is_active);

CREATE INDEX IF NOT EXISTS idx_portfolio_stocks_anal_portfolio ON portfolio_stocks_anal(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_stocks_anal_stock ON portfolio_stocks_anal(stock_id);

CREATE INDEX IF NOT EXISTS idx_sector_avg_anal_sector ON sector_averages_anal(sector);
CREATE INDEX IF NOT EXISTS idx_sector_avg_anal_date ON sector_averages_anal(base_date);

CREATE INDEX IF NOT EXISTS idx_analysis_anal_stock ON analysis_results_anal(stock_id);
CREATE INDEX IF NOT EXISTS idx_analysis_anal_date ON analysis_results_anal(analysis_date);
CREATE INDEX IF NOT EXISTS idx_analysis_anal_stock_date ON analysis_results_anal(stock_id, analysis_date);
CREATE INDEX IF NOT EXISTS idx_analysis_anal_score ON analysis_results_anal(total_score DESC);

-- ===================================================
-- RLS (Row Level Security) 정책
-- ===================================================

-- RLS 활성화
ALTER TABLE stocks_anal ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios_anal ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_stocks_anal ENABLE ROW LEVEL SECURITY;
ALTER TABLE sector_averages_anal ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results_anal ENABLE ROW LEVEL SECURITY;

-- 모든 사용자에게 읽기 허용 (anon key 사용 시)
CREATE POLICY "Allow public read access on stocks_anal"
    ON stocks_anal FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access on portfolios_anal"
    ON portfolios_anal FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access on portfolio_stocks_anal"
    ON portfolio_stocks_anal FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access on sector_averages_anal"
    ON sector_averages_anal FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access on analysis_results_anal"
    ON analysis_results_anal FOR SELECT
    USING (true);

-- Service Role에게 모든 권한 허용 (INSERT, UPDATE, DELETE)
CREATE POLICY "Allow service role full access on stocks_anal"
    ON stocks_anal FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on portfolios_anal"
    ON portfolios_anal FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on portfolio_stocks_anal"
    ON portfolio_stocks_anal FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on sector_averages_anal"
    ON sector_averages_anal FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access on analysis_results_anal"
    ON analysis_results_anal FOR ALL
    USING (auth.role() = 'service_role');

-- 6. news_ratings_anal 테이블 (뉴스 평점)
CREATE TABLE IF NOT EXISTS news_ratings_anal (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks_anal(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,                  -- 뉴스 제목
    link VARCHAR(1000),                           -- 뉴스 링크
    press VARCHAR(100),                           -- 언론사
    news_date DATE,                               -- 뉴스 날짜
    rating INTEGER CHECK (rating >= -10 AND rating <= 10),  -- 사용자 평점 (-10 ~ +10)
    auto_sentiment VARCHAR(20),                   -- 자동 감정 (positive/negative/neutral)
    auto_impact VARCHAR(20),                      -- 자동 영향도 (high/medium/low)
    is_rated BOOLEAN DEFAULT FALSE,               -- 평점 완료 여부
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(stock_id, title)                       -- 같은 종목의 동일 제목 중복 방지
);

-- news_ratings_anal 인덱스
CREATE INDEX IF NOT EXISTS idx_news_ratings_anal_stock ON news_ratings_anal(stock_id);
CREATE INDEX IF NOT EXISTS idx_news_ratings_anal_date ON news_ratings_anal(news_date);
CREATE INDEX IF NOT EXISTS idx_news_ratings_anal_rated ON news_ratings_anal(is_rated);

-- news_ratings_anal RLS
ALTER TABLE news_ratings_anal ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access on news_ratings_anal"
    ON news_ratings_anal FOR SELECT
    USING (true);

CREATE POLICY "Allow public write access on news_ratings_anal"
    ON news_ratings_anal FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public update access on news_ratings_anal"
    ON news_ratings_anal FOR UPDATE
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on news_ratings_anal"
    ON news_ratings_anal FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ===================================================
-- 뷰 생성 (선택)
-- ===================================================

-- 종목별 최신 분석 결과 뷰
CREATE OR REPLACE VIEW v_latest_analysis_anal AS
SELECT DISTINCT ON (ar.stock_id)
    s.code,
    s.name,
    s.sector,
    ar.*
FROM analysis_results_anal ar
JOIN stocks_anal s ON ar.stock_id = s.id
ORDER BY ar.stock_id, ar.analysis_date DESC;

-- 점수 순위 뷰
CREATE OR REPLACE VIEW v_score_ranking_anal AS
SELECT
    s.code,
    s.name,
    s.sector,
    ar.analysis_date,
    ar.tech_total,
    ar.fund_total,
    ar.sent_total,
    ar.liquidity_total_penalty,
    ar.total_score,
    ar.grade,
    RANK() OVER (PARTITION BY ar.analysis_date ORDER BY ar.total_score DESC) as rank
FROM analysis_results_anal ar
JOIN stocks_anal s ON ar.stock_id = s.id
WHERE s.is_active = true;

-- ===================================================
-- 완료 메시지
-- ===================================================
SELECT 'Schema created successfully! Tables: stocks_anal, portfolios_anal, portfolio_stocks_anal, sector_averages_anal, analysis_results_anal' as message;
