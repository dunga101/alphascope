import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

from app.collectors import yahoo_fundamentals


class YahooFundamentalsTests(unittest.TestCase):
    def test_collect_yahoo_fundamentals_maps_info_fields(self):
        info = {
            "trailingPE": 34.1,
            "forwardPE": 27.4,
            "dividendYield": 1.2,
            "returnOnEquity": 0.58,
            "marketCap": 1900000000000,
            "sector": "Technology",
            "industry": "Semiconductors",
            "totalRevenue": 51500000000,
            "operatingMargins": 0.37,
            "profitMargins": 0.22,
            "beta": 1.1,
            "freeCashflow": 21000000000,
            "totalDebt": 76000000000,
            "debtToEquity": 140.0,
            "currentRatio": 1.2,
            "totalCash": 12000000000,
        }
        with patch.object(yahoo_fundamentals, "_cache_is_valid", return_value=False):
            with patch.object(yahoo_fundamentals, "_save_cache"):
                with patch.object(yahoo_fundamentals, "_get_ticker_info", return_value=info):
                    result = yahoo_fundamentals.collect_yahoo_fundamentals("avgo")

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["symbol"], "AVGO")
        self.assertEqual(result["source"], "YAHOO")
        self.assertEqual(result["pe_ratio"], 34.1)
        self.assertEqual(result["forward_pe"], 27.4)
        self.assertEqual(result["dividend_yield"], 0.012)
        self.assertEqual(result["roe"], 0.58)
        self.assertEqual(result["sector"], "Technology")
        self.assertEqual(result["industry"], "Semiconductors")
        self.assertEqual(result["debt_to_equity"], 1.4)
        self.assertEqual(result["provider_fields"]["pe_ratio"], "YAHOO")

    def test_collect_yahoo_fundamentals_preserves_zero_dividend(self):
        info = {
            "trailingPE": 29.0,
            "returnOnEquity": 0.18,
            "dividendYield": 0,
        }
        with patch.object(yahoo_fundamentals, "_cache_is_valid", return_value=False):
            with patch.object(yahoo_fundamentals, "_save_cache"):
                with patch.object(yahoo_fundamentals, "_get_ticker_info", return_value=info):
                    result = yahoo_fundamentals.collect_yahoo_fundamentals("amzn")

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["dividend_yield"], 0)

    def test_collect_yahoo_fundamentals_returns_error_for_empty_info(self):
        with patch.object(yahoo_fundamentals, "_cache_is_valid", return_value=False):
            with patch.object(yahoo_fundamentals, "_get_ticker_info", return_value={}):
                result = yahoo_fundamentals.collect_yahoo_fundamentals("missing")

        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["source"], "YAHOO")


if __name__ == "__main__":
    unittest.main()
