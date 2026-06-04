import unittest

from app.analytics.investor_scoring_engine import (
    recommendation_for_score,
    score_investor_opportunity,
)


class InvestorScoringEngineTests(unittest.TestCase):
    def test_recommendation_thresholds(self):
        self.assertEqual(recommendation_for_score(80), "Strong Buy")
        self.assertEqual(recommendation_for_score(65), "Buy")
        self.assertEqual(recommendation_for_score(50), "Watch")
        self.assertEqual(recommendation_for_score(49.99), "Avoid")

    def test_score_investor_opportunity_returns_required_fields(self):
        result = score_investor_opportunity(
            symbol="AAPL",
            fundamentals={
                "pe_ratio": 22,
                "roe": 0.30,
                "debt_to_equity": 0.8,
                "dividend_yield": 0.006,
                "free_cash_flow": 98767000000,
            },
            profile={
                "company_name": "Apple Inc.",
                "sector": "Technology",
            },
            quote={
                "price": 201.25,
            },
            technical_indicators={
                "distance_from_52w_low_pct": 18,
                "rsi14": 58,
            },
        )

        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["company"], "Apple Inc.")
        self.assertEqual(result["sector"], "Technology")
        self.assertEqual(result["current_price"], 201.25)
        self.assertIn("buy_score", result)
        self.assertIn(result["recommendation"], {"Strong Buy", "Buy", "Watch", "Avoid"})
        self.assertEqual(result["pe_ratio"], 22)
        self.assertEqual(result["rsi"], 58)
        self.assertEqual(result["data_status"], "COMPLETE")

    def test_missing_critical_fundamentals_returns_insufficient_data(self):
        result = score_investor_opportunity(
            symbol="AVGO",
            fundamentals=None,
            profile={"company_name": "Broadcom Inc."},
            quote={"price": 463.84},
        )

        self.assertEqual(result["recommendation"], "Insufficient Data")
        self.assertEqual(result["buy_score"], 0)
        self.assertEqual(result["data_status"], "INSUFFICIENT_DATA")
        self.assertIn("pe_ratio", result["critical_missing_fields"])
        self.assertEqual(result["raw_score"]["calculated_buy_score"], 47.25)

    def test_zero_dividend_yield_is_valid_fundamental(self):
        result = score_investor_opportunity(
            symbol="AMZN",
            fundamentals={
                "pe_ratio": 29,
                "roe": 0.18,
                "debt_to_equity": 0.4,
                "dividend_yield": 0,
                "free_cash_flow": 7695000000,
            },
        )

        self.assertNotEqual(result["recommendation"], "Insufficient Data")
        self.assertEqual(result["data_status"], "COMPLETE")


if __name__ == "__main__":
    unittest.main()
