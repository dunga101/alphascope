import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=Mock()))

from app.db.intelligence_persistence import persist_investor_score


class InvestorPersistenceTests(unittest.TestCase):
    def test_persist_investor_score_maps_payload_to_sql_params(self):
        cursor = Mock()
        connection = Mock()
        connection.cursor.return_value = cursor

        score = {
            "symbol": "AAPL",
            "company": "Apple Inc.",
            "sector": "Technology",
            "buy_score": 78.5,
            "recommendation": "Buy",
            "valuation_score": 75,
            "dividend_score": 50,
            "financial_quality_score": 90,
            "price_position_score": 70,
            "technical_score": 65,
            "dividend_yield": 0.006,
            "pe_ratio": 22,
            "distance_from_52w_low": 18,
            "rsi": 58,
            "raw_score": {"weights": {"valuation": 0.25}},
        }

        with patch("app.db.intelligence_persistence.get_connection", return_value=connection):
            persist_investor_score(score)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args.args

        self.assertIn("INSERT INTO investor_scores", sql)
        self.assertIn("ON CONFLICT (score_date, symbol)", sql)
        self.assertEqual(params[1], "AAPL")
        self.assertEqual(params[2], "Apple Inc.")
        self.assertEqual(params[3], "Technology")
        self.assertEqual(params[4], 78.5)
        self.assertEqual(params[5], "Buy")
        self.assertEqual(params[12], 22)
        self.assertEqual(params[14], 58)

        connection.commit.assert_called_once()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
