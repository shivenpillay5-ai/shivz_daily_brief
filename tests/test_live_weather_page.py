from __future__ import annotations

import unittest
from pathlib import Path


class LiveWeatherPageTests(unittest.TestCase):
    def test_live_weather_page_includes_regions_and_icon_helpers(self) -> None:
        page = Path("docs/live-weather.html").read_text(encoding="utf-8")

        self.assertIn("Weather Around The People", page)
        self.assertIn("Live Region Snapshot", page)
        self.assertLess(page.index("Midrand"), page.index("Johannesburg"))
        self.assertLess(page.index("Johannesburg"), page.index("Cape Town"))
        self.assertLess(page.index("Cape Town"), page.index("Durban"))
        self.assertIn("function conditionIcon", page)
        self.assertIn("function renderWeatherCard", page)
        self.assertIn("hour-strip", page)
        self.assertIn("Next 24 hours", page)
        self.assertNotIn("Next 12 Hours", page)
        self.assertNotIn("Selected Region", page)


if __name__ == "__main__":
    unittest.main()
