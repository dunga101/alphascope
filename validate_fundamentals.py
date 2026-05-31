from app.collectors import fmp_fundamentals

symbols = ["AAPL", "MSFT", "NVDA"]

fmp_fundamentals._cache_is_valid = lambda symbol: False
fmp_fundamentals._save_cache = lambda symbol, data: None

for symbol in symbols:
    data = fmp_fundamentals.collect_fundamentals(symbol)

    print(symbol)
    print("  pe_ratio:", data.get("pe_ratio"))
    print("  roe:", data.get("roe"))
    print("  debt_to_equity:", data.get("debt_to_equity"))
    print()
