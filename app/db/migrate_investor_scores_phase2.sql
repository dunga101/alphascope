-- Phase 2 Investor Edition investor_scores migration.
--
-- Purpose:
-- Bring an existing legacy investor_scores table into alignment with
-- app/db/schema_intelligence.sql and app/db/intelligence_persistence.py.
--
-- This migration is intentionally non-destructive. It does not drop the table
-- and does not delete legacy rows. If duplicate rows would prevent the required
-- (score_date, symbol) unique key, the migration raises an exception so the
-- duplicates can be reviewed explicitly.

BEGIN;

ALTER TABLE investor_scores
    ADD COLUMN IF NOT EXISTS score_date DATE,
    ADD COLUMN IF NOT EXISTS company_name TEXT,
    ADD COLUMN IF NOT EXISTS sector VARCHAR(100),
    ADD COLUMN IF NOT EXISTS financial_quality_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS dividend_yield DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pe_ratio DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS rsi DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS raw_score JSONB;

UPDATE investor_scores
SET score_date = COALESCE(score_date, created_at::date, CURRENT_DATE)
WHERE score_date IS NULL;

UPDATE investor_scores
SET buy_score = 0
WHERE buy_score IS NULL;

UPDATE investor_scores
SET recommendation = 'Avoid'
WHERE recommendation IS NULL;

ALTER TABLE investor_scores
    ALTER COLUMN score_date SET DEFAULT CURRENT_DATE,
    ALTER COLUMN score_date SET NOT NULL,
    ALTER COLUMN symbol TYPE VARCHAR(20),
    ALTER COLUMN recommendation TYPE VARCHAR(50),
    ALTER COLUMN buy_score TYPE DOUBLE PRECISION USING buy_score::DOUBLE PRECISION,
    ALTER COLUMN buy_score SET NOT NULL,
    ALTER COLUMN recommendation SET NOT NULL,
    ALTER COLUMN valuation_score TYPE DOUBLE PRECISION USING valuation_score::DOUBLE PRECISION,
    ALTER COLUMN dividend_score TYPE DOUBLE PRECISION USING dividend_score::DOUBLE PRECISION,
    ALTER COLUMN price_position_score TYPE DOUBLE PRECISION USING price_position_score::DOUBLE PRECISION,
    ALTER COLUMN technical_score TYPE DOUBLE PRECISION USING technical_score::DOUBLE PRECISION,
    ALTER COLUMN distance_from_52w_low TYPE DOUBLE PRECISION USING distance_from_52w_low::DOUBLE PRECISION;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM investor_scores
        GROUP BY score_date, symbol
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'investor_scores has duplicate (score_date, symbol) rows. Review duplicates before adding unique constraint.';
    END IF;
END $$;

ALTER TABLE investor_scores
    ADD CONSTRAINT investor_scores_score_date_symbol_key
    UNIQUE (score_date, symbol);

CREATE INDEX IF NOT EXISTS idx_investor_scores_date_score
ON investor_scores (score_date, buy_score DESC);

CREATE INDEX IF NOT EXISTS idx_investor_scores_symbol_date
ON investor_scores (symbol, score_date DESC);

COMMIT;
