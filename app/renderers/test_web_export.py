import json
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=Mock()))
sys.modules.setdefault(
    "psycopg2.extras",
    types.SimpleNamespace(RealDictCursor=object),
)

from app.renderers.web_export import export_investor_rankings


class WebExportTests(unittest.TestCase):
    def test_export_investor_rankings_writes_ranked_payload(self):
        rows = [
            {
                "rank": 1,
                "symbol": "MSFT",
                "company_name": "Microsoft Corporation",
                "sector": "Technology",
                "buy_score": 82.5,
                "recommendation": "Strong Buy",
                "valuation_score": 75,
                "dividend_score": 70,
                "financial_quality_score": 90,
                "price_position_score": 65,
                "technical_score": 80,
                "dividend_yield": 0.008,
                "pe_ratio": 31.4,
                "distance_from_52w_low": 24.2,
                "rsi": 59.1,
                "roe": 0.35,
                "debt_to_equity": 0.7,
                "free_cash_flow": 71611000000,
                "technical_raw_signals": {
                    "metrics": {
                        "sma20": 416.97,
                        "sma50": 402.06,
                    }
                },
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            previous_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                with patch(
                    "app.renderers.web_export.fetch_latest_investor_rankings",
                    return_value=rows,
                ):
                    output = export_investor_rankings(
                        "2026-05-31 17:00 EDT",
                        "2026-05-31T17:00:00-04:00",
                    )

                with open("web/data/investor-rankings.json", encoding="utf-8") as f:
                    payload = json.load(f)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(output["generation_status"], "success")
        self.assertEqual(payload["generated_at"], "2026-05-31 17:00 EDT")
        self.assertEqual(payload["generation_status"], "success")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["rankings"][0]["rank"], 1)
        self.assertEqual(payload["rankings"][0]["symbol"], "MSFT")
        self.assertEqual(payload["rankings"][0]["company"], "Microsoft Corporation")
        self.assertEqual(payload["rankings"][0]["sma20"], 416.97)
        self.assertTrue(payload["rankings"][0]["strengths"])


if __name__ == "__main__":
    unittest.main()
