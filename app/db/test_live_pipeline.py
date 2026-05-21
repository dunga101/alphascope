from app.db.repositories import save_market_snapshot

mock_fmp_quotes = {
    "quotes": {
        "SPY": {
            "changePercentage": 0.87
        }
    }
}

mock_unified = {
    "final_regime": "RISK_ON",
    "final_confidence": 74
}

save_market_snapshot(mock_fmp_quotes, mock_unified)

print("Pipeline persistence test successful.")
