import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))

from app.collectors import fred_macro


class FredMacroCollectorTests(unittest.TestCase):
    def test_collect_fred_macro_returns_error_without_api_key(self):
        with patch.object(fred_macro, "FRED_API_KEY", None):
            result = fred_macro.collect_fred_macro(["FEDFUNDS"])

        self.assertEqual(result["status"], "ERROR")
        self.assertIn("FRED_API_KEY", result["errors"])

    def test_collect_fred_macro_fetches_and_normalizes_observations(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "observations": [
                {
                    "realtime_start": "2026-01-01",
                    "realtime_end": "2026-01-01",
                    "date": "2026-01-01",
                    "value": "4.33",
                },
                {
                    "realtime_start": "2026-02-01",
                    "realtime_end": "2026-02-01",
                    "date": "2026-02-01",
                    "value": ".",
                },
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(fred_macro, "FRED_API_KEY", "test-key"):
                with patch.object(fred_macro, "FRED_CACHE_DIR", Path(tmpdir)):
                    with patch.object(fred_macro.requests, "get", return_value=response):
                        result = fred_macro.collect_fred_macro(["FEDFUNDS"])

        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["cache_stats"]["misses"], 1)
        self.assertEqual(result["series"]["FEDFUNDS"]["latest"]["value"], 4.33)
        self.assertIsNone(result["series"]["FEDFUNDS"]["observations"][1]["value"])

    def test_collect_fred_macro_uses_valid_cache(self):
        cached = {
            "series_id": "FEDFUNDS",
            "observations": [
                {
                    "series_id": "FEDFUNDS",
                    "date": "2026-01-01",
                    "value": 4.33,
                }
            ],
            "latest": {
                "series_id": "FEDFUNDS",
                "date": "2026-01-01",
                "value": 4.33,
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "FEDFUNDS.json"
            cache_path.write_text(json.dumps(cached), encoding="utf-8")

            with patch.object(fred_macro, "FRED_API_KEY", "test-key"):
                with patch.object(fred_macro, "FRED_CACHE_DIR", Path(tmpdir)):
                    with patch.object(fred_macro.requests, "get") as get:
                        result = fred_macro.collect_fred_macro(["FEDFUNDS"])

        get.assert_not_called()
        self.assertEqual(result["cache_stats"]["hits"], 1)
        self.assertEqual(result["series"]["FEDFUNDS"]["cache_status"], "HIT")

    def test_collect_fred_macro_redacts_api_key_from_errors(self):
        response = Mock()
        response.raise_for_status.side_effect = RuntimeError(
            "429 Client Error for url: https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=secret-key&file_type=json"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(fred_macro, "FRED_API_KEY", "secret-key"):
                with patch.object(fred_macro, "FRED_CACHE_DIR", Path(tmpdir)):
                    with patch.object(fred_macro.requests, "get", return_value=response):
                        result = fred_macro.collect_fred_macro(["DGS10"])

        self.assertEqual(result["status"], "ERROR")
        self.assertNotIn("secret-key", result["errors"]["DGS10"])
        self.assertIn("api_key=REDACTED", result["errors"]["DGS10"])


if __name__ == "__main__":
    unittest.main()
