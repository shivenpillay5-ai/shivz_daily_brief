from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from daily_brief.config import LocationConfig
from daily_brief.tools.weather import fetch_weather


class WeatherTests(unittest.TestCase):
    @patch("daily_brief.tools.weather.get_json")
    def test_fetch_weather_returns_5am_to_4am_hourly_window(self, get_json_mock) -> None:
        get_json_mock.return_value = _weather_response()

        report = fetch_weather(
            LocationConfig(
                name="Midrand",
                latitude=-25.9992,
                longitude=28.1263,
                timezone="Africa/Johannesburg",
                hourly=True,
            )
        )

        query = parse_qs(urlparse(get_json_mock.call_args.args[0]).query)
        self.assertEqual(query["forecast_days"], ["2"])
        self.assertEqual(report.latitude, -25.9992)
        self.assertEqual(report.longitude, 28.1263)
        self.assertEqual(report.timezone, "Africa/Johannesburg")
        self.assertEqual(len(report.hourly), 24)
        self.assertEqual(report.hourly[0].time_label, "05:00")
        self.assertEqual(report.hourly[-1].time_label, "04:00")


def _weather_response() -> dict[str, object]:
    start = datetime(2026, 5, 4, 0, 0)
    hours = [start + timedelta(hours=index) for index in range(48)]
    return {
        "current": {
            "temperature_2m": 21,
            "apparent_temperature": 21,
            "relative_humidity_2m": 50,
            "wind_speed_10m": 11,
            "weather_code": 0,
        },
        "daily": {
            "temperature_2m_min": [12],
            "temperature_2m_max": [25],
            "precipitation_probability_max": [5],
            "weather_code": [0],
        },
        "hourly": {
            "time": [hour.strftime("%Y-%m-%dT%H:%M") for hour in hours],
            "temperature_2m": [float(index) for index in range(48)],
            "apparent_temperature": [float(index) for index in range(48)],
            "precipitation_probability": [float(index % 100) for index in range(48)],
            "weather_code": [0 for _ in range(48)],
        },
    }


if __name__ == "__main__":
    unittest.main()
