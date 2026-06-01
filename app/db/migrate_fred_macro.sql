CREATE TABLE IF NOT EXISTS fred_observations (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(32) NOT NULL,
    observation_date DATE NOT NULL,
    value DOUBLE PRECISION,
    realtime_start DATE,
    realtime_end DATE,
    source VARCHAR(20) NOT NULL DEFAULT 'FRED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_observation JSONB,
    UNIQUE (series_id, observation_date)
);

CREATE INDEX IF NOT EXISTS idx_fred_observations_series_date
ON fred_observations (series_id, observation_date DESC);

CREATE TABLE IF NOT EXISTS macro_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    fed_funds_rate DOUBLE PRECISION,
    cpi_value DOUBLE PRECISION,
    cpi_yoy DOUBLE PRECISION,
    cpi_3m_annualized DOUBLE PRECISION,
    unemployment_rate DOUBLE PRECISION,
    unemployment_trend VARCHAR(30),
    treasury_10y DOUBLE PRECISION,
    treasury_2y DOUBLE PRECISION,
    yield_curve_spread DOUBLE PRECISION,
    yield_curve_state VARCHAR(30),
    interest_rate_trend VARCHAR(30),
    inflation_trend VARCHAR(30),
    macro_regime VARCHAR(50),
    macro_risk_score DOUBLE PRECISION,
    summary TEXT,
    raw_macro JSONB,
    UNIQUE (snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_macro_snapshots_date
ON macro_snapshots (snapshot_date DESC);
