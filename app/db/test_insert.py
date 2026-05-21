from app.db.repositories import save_market_snapshot


sample_data = {
    "sp500": -1.24,
    "nasdaq_100": -1.54,
    "dow": -1.07,
    "small_caps": -2.44,
    "vix": 6.78,
    "10y_yield": 3.00,
    "market_regime": "RISK_OFF",
    "confidence": 67.6
}

save_market_snapshot(sample_data)
