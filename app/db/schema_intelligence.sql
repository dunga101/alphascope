CREATE TABLE IF NOT EXISTS intelligence_reports (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    market_regime VARCHAR(50),
    confidence_score DOUBLE PRECISION,
    quick_take TEXT,
    executive_summary TEXT,
    recommended_posture TEXT,
    bullish_signals JSONB,
    bearish_signals JSONB,
    risk_flags JSONB,
    raw_ai_output JSONB,
    UNIQUE (report_date)
);

CREATE TABLE IF NOT EXISTS technical_snapshots (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    symbol VARCHAR(20),
    signal_score DOUBLE PRECISION,
    trend_score DOUBLE PRECISION,
    momentum_score DOUBLE PRECISION,
    volatility_score DOUBLE PRECISION,
    risk_score DOUBLE PRECISION,
    technical_regime VARCHAR(50),
    technical_confidence DOUBLE PRECISION,
    raw_signals JSONB,
    UNIQUE (report_date, symbol)
);

CREATE TABLE IF NOT EXISTS event_snapshots (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    event_regime VARCHAR(50),
    event_confidence DOUBLE PRECISION,
    major_headlines JSONB,
    bullish_events JSONB,
    bearish_events JSONB,
    neutral_events JSONB,
    risk_events JSONB,
    raw_event_output JSONB,
    UNIQUE (report_date)
);

CREATE TABLE IF NOT EXISTS investor_scores (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    score_date DATE NOT NULL DEFAULT CURRENT_DATE,
    symbol VARCHAR(20) NOT NULL,
    company_name TEXT,
    sector VARCHAR(100),
    buy_score DOUBLE PRECISION NOT NULL,
    recommendation VARCHAR(50) NOT NULL,
    valuation_score DOUBLE PRECISION,
    dividend_score DOUBLE PRECISION,
    financial_quality_score DOUBLE PRECISION,
    price_position_score DOUBLE PRECISION,
    technical_score DOUBLE PRECISION,
    dividend_yield DOUBLE PRECISION,
    pe_ratio DOUBLE PRECISION,
    distance_from_52w_low DOUBLE PRECISION,
    rsi DOUBLE PRECISION,
    raw_score JSONB,
    UNIQUE (score_date, symbol)
);

CREATE INDEX IF NOT EXISTS idx_investor_scores_date_score
ON investor_scores (score_date, buy_score DESC);

CREATE INDEX IF NOT EXISTS idx_investor_scores_symbol_date
ON investor_scores (symbol, score_date DESC);
