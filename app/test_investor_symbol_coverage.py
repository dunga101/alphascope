import unittest

from app.config.symbols import CORE_SYMBOLS, FMP_WATCHLIST, FUNDAMENTAL_SYMBOLS


class InvestorSymbolCoverageTests(unittest.TestCase):
    def test_core_universe_has_v12_size(self):
        self.assertEqual(len(CORE_SYMBOLS), 50)

    def test_fundamentals_cover_core_investor_symbols(self):
        self.assertEqual(set(CORE_SYMBOLS), set(FUNDAMENTAL_SYMBOLS))

    def test_fmp_watchlist_includes_core_investor_symbols(self):
        self.assertTrue(set(CORE_SYMBOLS).issubset(set(FMP_WATCHLIST)))


if __name__ == "__main__":
    unittest.main()
