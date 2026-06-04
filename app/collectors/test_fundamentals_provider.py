import unittest
from unittest.mock import patch

from app.collectors import fundamentals_provider


class FundamentalsProviderTests(unittest.TestCase):
    def test_merge_prefers_fmp_field_when_valid(self):
        result = fundamentals_provider.merge_fundamental_payloads(
            "MSFT",
            {
                "status": "OK",
                "pe_ratio": 25.3,
                "roe": 0.29,
                "dividend_yield": 0.008,
            },
            {
                "status": "OK",
                "pe_ratio": 30.0,
                "roe": 0.31,
                "dividend_yield": 0.01,
            },
        )

        self.assertEqual(result["pe_ratio"], 25.3)
        self.assertEqual(result["pe_ratio_source"], "FMP")
        self.assertEqual(result["roe"], 0.29)
        self.assertEqual(result["dividend_yield_source"], "FMP")

    def test_merge_uses_yahoo_field_level_fallback(self):
        result = fundamentals_provider.merge_fundamental_payloads(
            "AVGO",
            {
                "status": "ERROR",
                "reason": "402 Payment Required",
            },
            {
                "status": "OK",
                "pe_ratio": 34.1,
                "roe": 0.58,
                "dividend_yield": 0.012,
                "free_cash_flow": 21000000000,
            },
        )

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["provider_used"], "YAHOO")
        self.assertEqual(result["pe_ratio_source"], "YAHOO")
        self.assertEqual(result["provider_errors"]["FMP"], "402 Payment Required")
        self.assertNotIn("pe_ratio", result["missing_fields"])

    def test_merge_combines_partial_provider_payloads(self):
        result = fundamentals_provider.merge_fundamental_payloads(
            "AAPL",
            {
                "status": "OK",
                "pe_ratio": 28,
                "dividend_yield": None,
            },
            {
                "status": "OK",
                "pe_ratio": 30,
                "dividend_yield": 0.004,
                "roe": 1.2,
            },
        )

        self.assertEqual(result["provider_used"], "COMBINED")
        self.assertEqual(result["pe_ratio"], 28)
        self.assertEqual(result["dividend_yield"], 0.004)
        self.assertEqual(result["dividend_yield_source"], "YAHOO")
        self.assertEqual(result["roe_source"], "YAHOO")

    def test_collect_combined_fundamentals_returns_diagnostics(self):
        with patch.object(
            fundamentals_provider,
            "collect_fundamentals",
            return_value={"status": "ERROR", "reason": "FMP unavailable"},
        ):
            with patch.object(
                fundamentals_provider,
                "collect_yahoo_fundamentals",
                return_value={
                    "status": "OK",
                    "pe_ratio": 20,
                    "roe": 0.2,
                    "dividend_yield": 0.01,
                },
            ):
                fundamentals, diagnostics = fundamentals_provider.collect_combined_fundamentals(["MSFT"])

        self.assertIn("MSFT", fundamentals)
        self.assertEqual(diagnostics["symbols"]["MSFT"]["provider_used"], "YAHOO")
        self.assertEqual(diagnostics["provider_counts"]["YAHOO"], 1)


if __name__ == "__main__":
    unittest.main()
