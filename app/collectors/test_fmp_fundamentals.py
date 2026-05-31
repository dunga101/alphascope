import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
sys.modules.setdefault("requests", types.SimpleNamespace(get=Mock()))

from app.collectors import fmp_fundamentals


class FmpFundamentalsTests(unittest.TestCase):
    def _fake_fmp_payloads(self):
        return {
            "income-statement": [
                {
                    "revenue": 416161000000,
                    "netIncome": 112010000000,
                }
            ],
            "balance-sheet-statement": [
                {
                    "cashAndCashEquivalents": 35934000000,
                    "totalDebt": 112377000000,
                    "totalStockholdersEquity": 73733000000,
                }
            ],
            "cash-flow-statement": [
                {
                    "operatingCashFlow": 111482000000,
                    "freeCashFlow": 98767000000,
                    "capitalExpenditure": -12715000000,
                }
            ],
            "ratios-ttm": [
                {
                    "priceToEarningsRatioTTM": 37.45157380444626,
                    "debtToEquityRatioTTM": 0.7954756740006198,
                    "dividendYieldTTM": 0.00336474,
                    "priceToBookRatioTTM": 43.10811861171367,
                    "currentRatioTTM": 1.07035746912159,
                }
            ],
        }

    def _fake_get(self, payloads):
        def fake_get(url, timeout):
            response = Mock()
            response.raise_for_status.return_value = None

            for endpoint, payload in payloads.items():
                if endpoint in url:
                    response.json.return_value = payload
                    return response

            self.fail(f"Unexpected URL: {url}")

        return fake_get

    def test_collect_fundamentals_maps_ratios_and_calculates_roe(self):
        payloads = self._fake_fmp_payloads()

        with patch.object(fmp_fundamentals, "API_KEY", "test-key"):
            with patch.object(fmp_fundamentals, "_cache_is_valid", return_value=False):
                with patch.object(fmp_fundamentals, "_save_cache"):
                    with patch.object(
                        fmp_fundamentals.requests,
                        "get",
                        side_effect=self._fake_get(payloads),
                    ):
                        result = fmp_fundamentals.collect_fundamentals("aapl")

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["pe_ratio"], 37.45157380444626)
        self.assertEqual(result["debt_to_equity"], 0.7954756740006198)
        self.assertEqual(result["dividend_yield"], 0.00336474)
        self.assertAlmostEqual(
            result["roe"],
            112010000000 / 73733000000,
        )
        self.assertEqual(result["free_cash_flow"], 98767000000)

    def test_calculate_roe_returns_none_for_missing_or_zero_equity(self):
        self.assertIsNone(fmp_fundamentals._calculate_roe(100, None))
        self.assertIsNone(fmp_fundamentals._calculate_roe(100, 0))
        self.assertIsNone(fmp_fundamentals._calculate_roe(None, 100))

    def test_collect_fundamentals_refreshes_stale_investor_metric_cache(self):
        payloads = self._fake_fmp_payloads()
        stale_cache = {
            "status": "OK",
            "symbol": "AAPL",
            "pe_ratio": None,
            "roe": None,
            "debt_to_equity": None,
            "dividend_yield": None,
            "free_cash_flow": 98767000000,
        }

        with patch.object(fmp_fundamentals, "API_KEY", "test-key"):
            with patch.object(fmp_fundamentals, "_cache_is_valid", return_value=True):
                with patch.object(fmp_fundamentals, "_load_cache", return_value=stale_cache):
                    with patch.object(fmp_fundamentals, "_save_cache"):
                        with patch.object(
                            fmp_fundamentals.requests,
                            "get",
                            side_effect=self._fake_get(payloads),
                        ) as mocked_get:
                            result = fmp_fundamentals.collect_fundamentals("aapl")

        self.assertEqual(mocked_get.call_count, 4)
        self.assertEqual(result["pe_ratio"], 37.45157380444626)
        self.assertEqual(result["debt_to_equity"], 0.7954756740006198)
        self.assertEqual(result["dividend_yield"], 0.00336474)
        self.assertAlmostEqual(result["roe"], 112010000000 / 73733000000)


if __name__ == "__main__":
    unittest.main()
