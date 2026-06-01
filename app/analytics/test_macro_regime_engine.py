import unittest

from app.analytics.macro_regime_engine import (
    build_macro_snapshot,
    calculate_cpi_yoy,
    inflation_trend,
    interest_rate_trend,
    yield_curve_state,
)


def series(series_id, values):
    observations = [
        {
            "series_id": series_id,
            "date": f"2025-{index + 1:02d}-01",
            "value": value,
        }
        for index, value in enumerate(values)
    ]

    return {
        "series_id": series_id,
        "observations": observations,
        "latest": observations[-1],
    }


class MacroRegimeEngineTests(unittest.TestCase):
    def test_calculate_cpi_yoy(self):
        cpi = series(
            "CPIAUCSL",
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 315],
        )

        self.assertEqual(calculate_cpi_yoy(cpi), 5.0)

    def test_inflation_trend_detects_reaccelerating(self):
        cpi = series(
            "CPIAUCSL",
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 318, 326],
        )

        self.assertEqual(inflation_trend(cpi), "REACCELERATING")

    def test_yield_curve_state_detects_inversion(self):
        state, spread = yield_curve_state(
            series("DGS10", [4.2]),
            series("DGS2", [4.7]),
        )

        self.assertEqual(state, "INVERTED")
        self.assertEqual(spread, -0.5)

    def test_interest_rate_trend_detects_rising(self):
        self.assertEqual(
            interest_rate_trend(
                series("FEDFUNDS", [4.1, 4.2, 4.6]),
                series("DGS2", [4.0] * 29 + [4.8]),
            ),
            "RISING",
        )

    def test_build_macro_snapshot_returns_compact_regime(self):
        payload = {
            "status": "OK",
            "series": {
                "FEDFUNDS": series("FEDFUNDS", [4.1, 4.2, 4.6]),
                "CPIAUCSL": series(
                    "CPIAUCSL",
                    [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 318, 326],
                ),
                "UNRATE": series("UNRATE", [3.8, 3.9, 4.0, 4.2]),
                "DGS10": series("DGS10", [4.2]),
                "DGS2": series("DGS2", [4.7]),
            },
            "errors": {},
        }

        snapshot = build_macro_snapshot(payload)

        self.assertEqual(snapshot["status"], "OK")
        self.assertEqual(snapshot["yield_curve_state"], "INVERTED")
        self.assertEqual(snapshot["inflation_trend"], "REACCELERATING")
        self.assertIn(snapshot["macro_regime"], {"STAGFLATION_RISK", "RECESSION_RISK"})
        self.assertIn("summary", snapshot)


if __name__ == "__main__":
    unittest.main()
