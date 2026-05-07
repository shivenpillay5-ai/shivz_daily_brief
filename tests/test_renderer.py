from __future__ import annotations

import unittest
from datetime import datetime

from daily_brief.models import (
    HourlyForecast,
    MarketPulse,
    MarketQuote,
    MorningSummary,
    RankedItem,
    WeatherReport,
)
from daily_brief.tools.rendering import (
    HERO_INTROS,
    SUMMARY_MAX_CHARS,
    render_html,
    render_text,
    render_whatsapp_template_parameters,
    render_whatsapp_text,
)


class RendererTests(unittest.TestCase):
    def test_render_html_has_month_of_hero_intro_variety(self) -> None:
        self.assertEqual(len(HERO_INTROS), 30)

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
        self.assertTrue(any(intro in body for intro in HERO_INTROS))
        self.assertIn("Top World News", body)
        self.assertIn("Read story", body)
        self.assertIn("https://example.com/world", body)

    def test_render_html_rotates_hero_intro_by_date(self) -> None:
        weather = _weather("Johannesburg")

        first_body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
        )
        second_body = render_html(
            brief_date=datetime(2026, 5, 5),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
        )

        first_intro = next(intro for intro in HERO_INTROS if intro in first_body)
        second_intro = next(intro for intro in HERO_INTROS if intro in second_body)
        self.assertNotEqual(first_intro, second_intro)

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

    def test_render_html_adds_weather_refresh_links_for_each_region(self) -> None:
        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[_weather("Midrand"), _weather("Cape Town")],
            world_items=[],
            ai_tech_items=[],
        )

        self.assertEqual(body.count("Real-time update &#8599;"), 2)
        self.assertIn("live-weather.html", body)
        self.assertIn("name=Midrand", body)
        self.assertIn("lat=-25.9992", body)
        self.assertIn("name=Cape+Town", body)

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
        self.assertTrue(any(intro in body for intro in HERO_INTROS))

    def test_render_html_shows_hourly_weather_for_featured_location(self) -> None:
        weather = _weather(
            "Midrand",
            hourly=_hourly_forecasts(),
        )

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
        )

        self.assertIn("Midrand", body)
        self.assertIn("Next 24 hours", body)
        self.assertIn("05:00 today to 04:00 tomorrow", body)
        self.assertIn("05:00", body)
        self.assertIn("04:00", body)
        self.assertIn("width:8.33%", body)

    def test_render_html_uses_night_icon_for_clear_hourly_weather(self) -> None:
        weather = _weather(
            "Midrand",
            hourly=[
                HourlyForecast(
                    time_label="05:00",
                    temperature_c=15,
                    feels_like_c=15,
                    precipitation_probability_percent=0,
                    condition="clear sky",
                ),
                HourlyForecast(
                    time_label="12:00",
                    temperature_c=24,
                    feels_like_c=24,
                    precipitation_probability_percent=0,
                    condition="clear sky",
                ),
                HourlyForecast(
                    time_label="20:00",
                    temperature_c=18,
                    feels_like_c=18,
                    precipitation_probability_percent=0,
                    condition="clear sky",
                ),
            ],
        )

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
        )

        self.assertIn("🌙", body)
        self.assertIn("☀️", body)
        self.assertIn("background:#eef5ff", body)
        self.assertIn("border:1px solid #b8c7df", body)

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

    def test_render_html_includes_morning_summary(self) -> None:
        weather = _weather("Midrand")

        body = render_html(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[],
            ai_tech_items=[],
            morning_summary=_morning_summary(),
        )

        self.assertIn("Morning read", body)
        self.assertIn("Morning Signal", body)
        self.assertIn("A useful morning read.", body)
        self.assertNotIn("Weather is calm.", body)
        self.assertIn("⚡", body)

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
            morning_summary=_morning_summary(),
            market_pulse=_market_pulse(),
        )

        self.assertIn("Market Pulse", body)
        self.assertIn("Morning Signal", body)
        self.assertIn("USD/ZAR R18.42 ↑ 0.4%", body)
        self.assertNotIn("Next 24 hours", body)
        self.assertNotIn("07:00", body)

    def test_render_whatsapp_template_parameters_match_approved_template(self) -> None:
        weather = _weather("Midrand")
        world_item = RankedItem(
            title="World story",
            url="https://example.com/world",
            source="Example World",
            summary="Summary",
        )
        ai_item = RankedItem(
            title="AI story",
            url="https://example.com/ai",
            source="Example AI",
            summary="Summary",
        )

        parameters = render_whatsapp_template_parameters(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[weather],
            world_items=[world_item],
            ai_tech_items=[ai_item],
        )

        self.assertEqual(len(parameters), 4)
        self.assertEqual(parameters[0], "Monday, 04 May 2026")
        self.assertIn("Midrand", parameters[1])
        self.assertIn("World story", parameters[2])
        self.assertNotIn("https://example.com/world", parameters[2])
        self.assertIn("AI story", parameters[3])


def _weather(
    location_name: str,
    temperature_c: float | None = 21,
    feels_like_c: float | None = 21,
    daily_min_c: float | None = 12,
    daily_max_c: float | None = 25,
    hourly: list[HourlyForecast] | None = None,
) -> WeatherReport:
    latitude, longitude = _coordinates(location_name)
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
        latitude=latitude,
        longitude=longitude,
        timezone="Africa/Johannesburg",
        hourly=hourly or [],
    )


def _coordinates(location_name: str) -> tuple[float, float]:
    return {
        "Midrand": (-25.9992, 28.1263),
        "Johannesburg": (-26.2041, 28.0473),
        "Cape Town": (-33.9249, 18.4241),
        "Durban": (-29.8587, 31.0218),
    }.get(location_name, (-25.9992, 28.1263))


def _hourly_forecasts() -> list[HourlyForecast]:
    labels = [f"{hour:02d}:00" for hour in range(5, 24)]
    labels.extend(f"{hour:02d}:00" for hour in range(0, 5))
    return [
        HourlyForecast(
            time_label=label,
            temperature_c=18,
            feels_like_c=18,
            precipitation_probability_percent=10,
            condition="clear sky",
        )
        for label in labels
    ]


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


def _morning_summary() -> MorningSummary:
    return MorningSummary(
        headline="Morning Signal",
        body="A useful morning read.",
        bullets=["Weather is calm.", "Markets are awake."],
    )


if __name__ == "__main__":
    unittest.main()
