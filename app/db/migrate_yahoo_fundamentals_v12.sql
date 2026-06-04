-- AlphaScope V1.2 Yahoo fundamentals and provider provenance migration.
--
-- This migration is additive and non-destructive.

BEGIN;

ALTER TABLE fundamental_snapshots
    ADD COLUMN IF NOT EXISTS provider_used VARCHAR(20),
    ADD COLUMN IF NOT EXISTS providers_available JSONB,
    ADD COLUMN IF NOT EXISTS pe_ratio_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS roe_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS dividend_yield_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS debt_to_equity_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS free_cash_flow_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS market_cap DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS market_cap_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS sector VARCHAR(100),
    ADD COLUMN IF NOT EXISTS industry VARCHAR(200),
    ADD COLUMN IF NOT EXISTS data_completeness_percent DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS available_fields JSONB,
    ADD COLUMN IF NOT EXISTS missing_fields JSONB,
    ADD COLUMN IF NOT EXISTS provider_errors JSONB,
    ADD COLUMN IF NOT EXISTS raw_provider_data JSONB;

UPDATE fundamental_snapshots
SET
    provider_used = COALESCE(provider_used, source, 'UNKNOWN'),
    pe_ratio_source = COALESCE(pe_ratio_source, source, 'UNKNOWN'),
    roe_source = COALESCE(roe_source, source, 'UNKNOWN'),
    dividend_yield_source = COALESCE(dividend_yield_source, source, 'UNKNOWN'),
    debt_to_equity_source = COALESCE(debt_to_equity_source, source, 'UNKNOWN'),
    free_cash_flow_source = COALESCE(free_cash_flow_source, source, 'UNKNOWN')
WHERE provider_used IS NULL
   OR pe_ratio_source IS NULL
   OR roe_source IS NULL
   OR dividend_yield_source IS NULL
   OR debt_to_equity_source IS NULL
   OR free_cash_flow_source IS NULL;

COMMIT;
