-- ===================================================
-- 재무 데이터 컬럼 추가 마이그레이션
-- ===================================================
-- Supabase SQL Editor에서 실행하세요.
-- https://supabase.com/dashboard/project/[PROJECT_ID]/sql

-- 밸류에이션 지표
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS per DECIMAL(10,2);
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS pbr DECIMAL(10,2);
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS psr DECIMAL(10,2);

-- 수익성 지표
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS roe DECIMAL(10,2);
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS op_margin DECIMAL(10,2);

-- 성장성 지표
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS revenue_growth DECIMAL(10,2);
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS op_growth DECIMAL(10,2);

-- 안정성 지표
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS debt_ratio DECIMAL(10,2);
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS current_ratio DECIMAL(10,2);

-- 기타
ALTER TABLE stocks_anal ADD COLUMN IF NOT EXISTS dividend_yield DECIMAL(10,2);

-- 확인
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'stocks_anal'
ORDER BY ordinal_position;
