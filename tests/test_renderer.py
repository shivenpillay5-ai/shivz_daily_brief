from __future__ import annotations

import unittest
from datetime import datetime

from daily_brief.models import (
    HourlyForecast,
    MarketPulse,
    MarketQuote,
    RankedItem,
    WeatherReport,
)
from daily_brief.tools.rendering import (
    SUMMARY_MAX_CHARS,
    render_html,
    render_text,
    render_whatsapp_text,
)


class RendererTests(unittest.TestCase):
    def test_render_text_includes_links(self) -> None:
        weather = _weather("Johannesburg")
        item = RankedItem(
            title="AI story",
            url="https://example.com/ai",
            source="Example",
            summary="A useful AI story.",
        )

        body = render_text(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[item],
            ai_tech_items=[item],
        )

        self.assertIn("https://example.com/ai", body)
        self.assertIn("Top AI and Tech Stories", body)

    def test_render_text_shortens_long_summaries(self) -> None:
        weather = _weather("Johannesburg")
        item = RankedItem(
            title="Long story",
            url="https://example.com/long",
            source="Example",
            summary="word " * 200,
        )

        body = render_text(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[item],
            ai_tech_items=[],
        )

        summary_line = next(line for line in body.splitlines() if line.strip().startswith("word"))
        self.assertLessEqual(len(summary_line.strip()), SUMMARY_MAX_CHARS)

    def test_render_html_includes_visual_sections_and_links(self) -> None:
        weather = _weather("Johannesburg")
        item = RankedItem(
            title="World story",
            url="https://example.com/world",
            source="Example",
            summary="A useful world story.",
        )

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[item],
            ai_tech_items=[],
        )

        self.assertIn("Shivz Daily Brief", body)
        self.assertIn("Morning signal", body)
        self.assertIn("Weather, world chaos, and AI plot twists", body)
        self.assertIn("Top World News", body)
        self.assertIn("Read story", body)
        self.assertIn("https://example.com/world", body)

    def test_render_html_adds_weather_mood(self) -> None:
        weather = _weather(
            "Johannesburg",
            temperature_c=29,
            feels_like_c=30,
            daily_min_c=20,
            daily_max_c=31,
        )

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
        )

        self.assertIn("Clear Sky", body)
        self.assertIn("Weather mood: warm", body)
        self.assertIn("Now", body)

    def test_render_html_hides_feed_warnings_from_reader(self) -> None:
        weather = _weather("Johannesburg")

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
            warnings=["UN News: invalid XML"],
        )

        self.assertNotIn("Feed warnings", body)
        self.assertNotIn("UN News", body)
        self.assertIn("Weather, world chaos, and AI plot twists", body)

    def test_render_html_shows_hourly_weather_for_featured_location(self) -> None:
        weather = _weather(
            "Midrand",
            hourly=[
                HourlyForecast(
                    time_label="07:00",
                    temperature_c=18,
                    feels_like_c=18,
                    precipitation_probability_percent=10,
                    condition="clear sky",
                )
            ],
        )

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
        )

        self.assertIn("Midrand", body)
        self.assertIn("Next few hours", body)
        self.assertIn("07:00", body)

    def test_render_html_includes_market_pulse(self) -> None:
        weather = _weather("Midrand")

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
            market_pulse=_market_pulse(),
        )

        self.assertIn("Markets At A Glance", body)
        self.assertIn("USD/ZAR", body)
        self.assertIn("R18.42", body)
        self.assertIn("💵", body)
        self.assertIn("Gold", body)
        self.assertIn("🥇", body)

    def test_render_whatsapp_text_includes_weather_and_links(self) -> None:
        weather = _weather("Midrand")
        item = RankedItem(
            title="Story",
            url="https://example.com/story",
            source="Example",
            summary="Summary",
        )

        body = render_whatsapp_text(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[item],
            ai_tech_items=[item],
        )

        self.assertIn("Shivz Daily Brief", body)
        self.assertIn("Midrand", body)
        self.assertIn("https://example.com/story", body)

    def test_render_whatsapp_text_keeps_midrand_weather_compact(self) -> None:
        weather = _weather(
            "Midrand",
            hourly=[
                HourlyForecast(
                    time_label="07:00",
                    temperature_c=18,
                    feels_like_c=18,
                    precipitation_probability_percent=10,
                    condition="clear sky",
                )
            ],
        )

        body = render_whatsapp_text(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
            market_pulse=_market_pulse(),
        )

        self.assertIn("Market Pulse", body)
        self.assertIn("USD/ZAR R18.42 ↑ 0.4%", body)
        self.assertNotIn("Next few hours", body)
        self.assertNotIn("07:00", body)


def _weather(
    location_name: str,
    temperature_c: float | None = 21,
    feels_like_c: float | None = 21,
    daily_min_c: float | None = 12,
    daily_max_c: float | None = 25,
    hourly: list[HourlyForecast] | None = None,
) -> WeatherReport:
    return WeatherReport(
        location_name=location_name,
        temperature_c=temperature_c,
        feels_like_c=feels_like_c,
        humidity_percent=50,
        wind_kmh=11,
        daily_min_c=daily_min_c,
        daily_max_c=daily_max_c,
        precipitation_probability_percent=5,
        condition="clear sky",
        hourly=hourly or [],
    )


def _market_pulse() -> MarketPulse:
    return MarketPulse(
        quotes=[
            MarketQuote(
                label="USD/ZAR",
                value=18.42,
                prefix="R",
                suffix="",
                source="Frankfurter",
                as_of="2026-05-04",
                change_percent=0.4,
            ),
            MarketQuote(
                label="Gold",
                value=2340.25,
                prefix="$",
                suffix="/oz",
                source="Yahoo Finance delayed futures",
                as_of="2026-05-04 05:00 UTC",
                change_percent=0.4,
            ),
        ]
    )


if __name__ == "__main__":
    unittest.main()
