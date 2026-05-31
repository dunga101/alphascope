import sys
import types
import unittest
from unittest.mock import Mock, patch


class RequestException(Exception):
    pass


class ReadTimeout(RequestException):
    pass


requests_stub = types.SimpleNamespace(
    get=Mock(),
    exceptions=types.SimpleNamespace(
        RequestException=RequestException,
        ReadTimeout=ReadTimeout,
    ),
)

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
sys.modules.setdefault("requests", requests_stub)

from app.collectors import finnhub_news


class FinnhubNewsTests(unittest.TestCase):
    def test_collect_finnhub_news_returns_empty_payload_on_timeout(self):
        with patch.object(finnhub_news, "FINNHUB_API_KEY", "test-key"):
            with patch.object(
                finnhub_news.requests,
                "get",
                side_effect=ReadTimeout("timed out"),
            ):
                with self.assertLogs("alphascope", level="WARNING") as logs:
                    result = finnhub_news.collect_finnhub_news()

        self.assertEqual(result, [])
        self.assertTrue(any("Finnhub news collection failed" in line for line in logs.output))

    def test_collect_finnhub_news_returns_empty_payload_without_api_key(self):
        with patch.object(finnhub_news, "FINNHUB_API_KEY", None):
            with self.assertLogs("alphascope", level="WARNING") as logs:
                result = finnhub_news.collect_finnhub_news()

        self.assertEqual(result, [])
        self.assertTrue(any("FINNHUB_API_KEY missing" in line for line in logs.output))

    def test_collect_finnhub_news_returns_empty_payload_for_unexpected_shape(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"error": "unexpected"}

        with patch.object(finnhub_news, "FINNHUB_API_KEY", "test-key"):
            with patch.object(finnhub_news.requests, "get", return_value=response):
                with self.assertLogs("alphascope", level="WARNING") as logs:
                    result = finnhub_news.collect_finnhub_news()

        self.assertEqual(result, [])
        self.assertTrue(any("unexpected payload shape" in line for line in logs.output))

    def test_collect_finnhub_news_maps_articles(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [
            {
                "source": "Reuters",
                "headline": "Market headline",
                "summary": "Market summary",
                "url": "https://example.com/news",
                "datetime": 1760000000,
            }
        ]

        with patch.object(finnhub_news, "FINNHUB_API_KEY", "test-key"):
            with patch.object(finnhub_news.requests, "get", return_value=response):
                result = finnhub_news.collect_finnhub_news()

        self.assertEqual(
            result,
            [
                {
                    "source_type": "finnhub",
                    "source": "Reuters",
                    "title": "Market headline",
                    "summary": "Market summary",
                    "url": "https://example.com/news",
                    "published": 1760000000,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
