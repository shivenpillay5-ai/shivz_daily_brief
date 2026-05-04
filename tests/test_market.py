from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.tools.market import fetch_market_pulse


class MarketTests(unittest.TestCase):
    @patch("daily_brief.tools.market.get_json")
    def test_fetch_market_pulse_builds_configured_quotes(self, get_json_mock) -> None:
        get_json_mock.side_effect = [
            {"date": "2026-05-04", "rates": {"ZAR": 18.42}},
            {
                "rates": {
                    "2026-04-30": {"ZAR": 18.35},
                    "2026-05-04": {"ZAR": 18.42},
                }
            },
            {"date": "2026-05-04", "rates": {"ZAR": 23.10}},
            {
                "rates": {
                    "2026-04-30": {"ZAR": 23.35},
                    "2026-05-04": {"ZAR": 23.10},
                }
            },
            _chart_response(price=2340.25, previous_close=2330.00),
            _chart_response(price=28.40, previous_close=28.20),
            _chart_response(price=83.20, previous_close=84.00),
        ]

        pulse = fetch_market_pulse()

        self.assertEqual(
            [quote.label for quote in pulse.quotes],
            ["USD/ZAR", "GBP/ZAR", "Gold", "Silver", "Brent"],
        )
        self.assertEqual(pulse.quotes[0].value, 18.42)
        self.assertGreater(pulse.quotes[0].change_percent or 0, 0)
        self.assertLess(pulse.quotes[1].change_percent or 0, 0)
        self.assertEqual(pulse.quotes[2].suffix, "/oz")
        self.assertLess(pulse.quotes[4].change_percent or 0, 0)
        self.assertEqual(pulse.warnings, [])

    @patch("daily_brief.tools.market.get_json")
    def test_fetch_market_pulse_keeps_going_when_one_source_fails(
        self,
        get_json_mock,
    ) -> None:
        get_json_mock.side_effect = [
            RuntimeError("temporary API failure"),
            {"date": "2026-05-04", "rates": {"ZAR": 23.10}},
            {
                "rates": {
                    "2026-04-30": {"ZAR": 23.35},
                    "2026-05-04": {"ZAR": 23.10},
                }
            },
            _chart_response(price=2340.25, previous_close=2330.00),
            _chart_response(price=28.40, previous_close=28.20),
            _chart_response(price=83.20, previous_close=84.00),
        ]

        pulse = fetch_market_pulse()

        self.assertEqual(len(pulse.quotes), 4)
        self.assertEqual(len(pulse.warnings), 1)
        self.assertIn("USD/ZAR", pulse.warnings[0])


def _chart_response(price: float, previous_close: float) -> dict[str, object]:
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": price,
                        "previousClose": previous_close,
                        "regularMarketTime": 1_778_000_000,
                    }
                }
            ]
        }
    }


if __name__ == "__main__":
    unittest.main()
