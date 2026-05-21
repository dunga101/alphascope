from app.db.database import SessionLocal
from app.db.models import MarketSnapshot


def save_market_snapshot(ai: dict, unified: dict):
    session = SessionLocal()

    try:
        snapshot = MarketSnapshot(
            sp500=None,
            nasdaq100=None,
            dow=None,
            russell2000=None,
            vix=None,
            us10y=None,
            market_regime=unified.get("final_regime"),
            confidence_score=unified.get("final_confidence")
        )

        session.add(snapshot)
        session.commit()

        print("Market snapshot persisted.")

    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()
