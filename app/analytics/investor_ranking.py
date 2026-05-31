from app.analytics.investor_scoring_engine import score_investor_opportunity
from app.analytics.technical_engine import get_symbol_indicators
from app.config.watchlist import load_watchlist_config
from app.logger import setup_logger

log = setup_logger()


def get_investor_symbols() -> list[str]:
    config = load_watchlist_config()
    symbols = config.get("investor") or config.get("core") or []
    return [symbol.upper() for symbol in symbols]


def _technical_for_symbol(symbol: str):
    try:
        return get_symbol_indicators(symbol)
    except Exception as e:
        log.warning(f"Investor ranking technical data unavailable for {symbol}: {e}")
        return None


def build_investor_rankings(
    fundamentals: dict | None = None,
    company_profiles: dict | None = None,
    fmp_quotes: dict | None = None,
    symbols: list[str] | None = None,
) -> list[dict]:
    fundamentals = fundamentals or {}
    company_profiles = company_profiles or {}
    quote_map = {}

    if fmp_quotes and fmp_quotes.get("status") == "OK":
        quote_map = fmp_quotes.get("quotes", {})

    ranking_symbols = symbols or get_investor_symbols()
    rankings = []

    for symbol in ranking_symbols:
        symbol = symbol.upper()
        technical_indicators = _technical_for_symbol(symbol)

        score = score_investor_opportunity(
            symbol=symbol,
            fundamentals=fundamentals.get(symbol),
            profile=company_profiles.get(symbol),
            quote=quote_map.get(symbol),
            technical_indicators=technical_indicators,
        )

        rankings.append(score)

    rankings.sort(
        key=lambda item: item.get("buy_score", 0),
        reverse=True,
    )

    return rankings
