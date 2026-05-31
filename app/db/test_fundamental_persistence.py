import unittest
from unittest.mock import Mock, patch
import sys
import types

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=Mock()))
from app.db.intelligence_persistence import persist_fundamental_snapshot


class FundamentalPersistenceTests(unittest.TestCase):
    def test_persist_fundamental_snapshot_maps_current_fmp_output(self):
        cursor = Mock()
        connection = Mock()
        connection.cursor.return_value = cursor

        fundamentals = {
            "symbol": "AAPL",
            "revenue": 391035000000,
            "net_income": 93736000000,
            "cash_and_equivalents": 29943000000,
            "total_debt": 106629000000,
            "operating_cash_flow": 118254000000,
            "free_cash_flow": 108807000000,
            "pe_ratio": 28.4,
            "roe": 1.36,
            "debt_to_equity": 1.87,
            "dividend_yield": 0.0034,
        }

        with patch("app.db.intelligence_persistence.get_connection", return_value=connection):
            persist_fundamental_snapshot("aapl", fundamentals)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args.args

        self.assertIn("INSERT INTO fundamental_snapshots", sql)
        self.assertIn("ON CONFLICT (symbol, snapshot_date)", sql)

        self.assertEqual(params[0], "AAPL")
        self.assertEqual(params[2], fundamentals["revenue"])
        self.assertEqual(params[3], fundamentals["net_income"])
        self.assertIsNone(params[4])
        self.assertIsNone(params[5])
        self.assertEqual(params[6], fundamentals["cash_and_equivalents"])
        self.assertEqual(params[7], fundamentals["total_debt"])
        self.assertEqual(params[8], fundamentals["operating_cash_flow"])
        self.assertEqual(params[9], fundamentals["free_cash_flow"])
        self.assertEqual(params[10], fundamentals["pe_ratio"])
        self.assertIsNone(params[11])
        self.assertEqual(params[12], fundamentals["roe"])
        self.assertEqual(params[13], fundamentals["debt_to_equity"])
        self.assertEqual(params[14], fundamentals["dividend_yield"])

        connection.commit.assert_called_once()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
