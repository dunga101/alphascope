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
