from app.db.intelligence_persistence import (
    persist_intelligence_report,
    persist_event_snapshot,
    persist_technical_snapshot
)

sample_ai_output = {
    "market_regime": "RISK_ON",
    "confidence": 78,
    "quick_take": "Markets showing constructive bullish behavior.",
    "executive_summary": "Breadth and momentum remain supportive while volatility is contained.",
    "recommended_posture": "Selective bullish exposure with disciplined risk management.",
    "bullish_signals": [
        "SPY above 20DMA",
        "QQQ momentum positive",
        "VIX stable"
    ],
    "bearish_signals": [
        "US10Y elevated"
    ],
    "risk_flags": [
        "Fed uncertainty"
    ]
}

sample_event_output = {
    "event_regime": "RISK_ON",
    "event_confidence": 71,
    "major_headlines": [
        "Tech earnings beat expectations",
        "Inflation data softer than expected"
    ],
    "bullish_events": [
        "Strong earnings"
    ],
    "bearish_events": [
        "Geopolitical tensions"
    ],
    "neutral_events": [
        "Sector rotation"
    ],
    "risk_events": [
        "Bond market volatility"
    ]
}

sample_technical_output = {
    "signal_score": 72,
    "trend_score": 80,
    "momentum_score": 76,
    "volatility_score": 61,
    "risk_score": 35,
    "technical_regime": "RISK_ON",
    "technical_confidence": 74
}

def main():
    persist_intelligence_report(sample_ai_output)
    persist_event_snapshot(sample_event_output)
    persist_technical_snapshot("SPY", sample_technical_output)

    print("Intelligence persistence test successful.")

if __name__ == "__main__":
    main()
