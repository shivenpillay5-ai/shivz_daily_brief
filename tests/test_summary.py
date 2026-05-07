from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from daily_brief.config import (
    AppConfig,
    CalendarSourceConfig,
    CoupleBriefConfig,
    EmailConfig,
    FeedConfig,
    GoogleCalendarConfig,
    LocationConfig,
    WhatsAppConfig,
)
from daily_brief.models import MarketPulse, MarketQuote, RankedItem, WeatherReport
from daily_brief.tools.summary import SUMMARY_OPENERS, write_morning_summary


class SummaryTests(unittest.TestCase):
    def test_fallback_summary_has_month_of_variety(self) -> None:
        self.assertEqual(len(SUMMARY_OPENERS), 30)

    def test_write_morning_summary_uses_fallback_without_openai_key(self) -> None:
        summary = write_morning_summary(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[_weather()],
            market_pulse=_market_pulse(),
            world_items=[_ranked("World lead", "BBC World")],
            ai_tech_items=[_ranked("AI lead", "TechCrunch AI")],
            config=_config(openai_api_key=""),
            use_openai=True,
        )

        self.assertIn(summary.headline, [headline for headline, _ in SUMMARY_OPENERS])
        self.assertIn("Midrand", summary.body)
        self.assertNotIn("World lead", summary.body)
        self.assertNotIn("18.42", summary.body)
        self.assertEqual(summary.bullets, [])
        self.assertFalse(summary.used_openai)

    def test_write_morning_summary_fallback_rotates_by_date(self) -> None:
        first = write_morning_summary(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[_weather()],
            market_pulse=_market_pulse(),
            world_items=[_ranked("World lead", "BBC World")],
            ai_tech_items=[_ranked("AI lead", "TechCrunch AI")],
            config=_config(openai_api_key=""),
            use_openai=True,
        )
        second = write_morning_summary(
            brief_date=datetime(2026, 5, 5),
            weather_reports=[_weather()],
            market_pulse=_market_pulse(),
            world_items=[_ranked("World lead", "BBC World")],
            ai_tech_items=[_ranked("AI lead", "TechCrunch AI")],
            config=_config(openai_api_key=""),
            use_openai=True,
        )

        self.assertNotEqual(first.headline, second.headline)
        self.assertNotEqual(first.body, second.body)

    @patch("daily_brief.tools.summary.post_json")
    def test_write_morning_summary_uses_openai_json(self, post_json_mock) -> None:
        post_json_mock.return_value = {
            "output_text": json.dumps(
                {
                    "headline": "Coffee Before Chaos",
                    "body": "A crisp morning scan with markets awake and AI making noise.",
                    "bullets": ["Weather is mild.", "Markets moved.", "AI leads."],
                }
            )
        }

        summary = write_morning_summary(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[_weather()],
            market_pulse=_market_pulse(),
            world_items=[_ranked("World lead", "BBC World")],
            ai_tech_items=[_ranked("AI lead", "TechCrunch AI")],
            config=_config(openai_api_key="secret"),
            use_openai=True,
        )

        self.assertEqual(summary.headline, "Coffee Before Chaos")
        self.assertTrue(summary.used_openai)
        self.assertEqual(post_json_mock.call_count, 1)

    @patch("daily_brief.tools.summary.post_json")
    def test_write_morning_summary_sends_daily_style_cue_to_openai(
        self,
        post_json_mock,
    ) -> None:
        post_json_mock.return_value = {
            "output_text": json.dumps(
                {
                    "headline": "Coffee Before Chaos",
                    "body": "A crisp morning scan with markets awake and AI making noise.",
                    "bullets": [],
                }
            )
        }

        write_morning_summary(
            brief_date=datetime(2026, 5, 4),
            weather_reports=[_weather()],
            market_pulse=_market_pulse(),
            world_items=[_ranked("World lead", "BBC World")],
            ai_tech_items=[_ranked("AI lead", "TechCrunch AI")],
            config=_config(openai_api_key="secret"),
            use_openai=True,
        )

        payload = post_json_mock.call_args.kwargs["payload"]
        self.assertIn('"opener_style"', payload["input"])


def _weather() -> WeatherReport:
    return WeatherReport(
        location_name="Midrand",
        temperature_c=21,
        feels_like_c=21,
        humidity_percent=50,
        wind_kmh=11,
        daily_min_c=12,
        daily_max_c=25,
        precipitation_probability_percent=5,
        condition="clear sky",
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
            )
        ]
    )


def _ranked(title: str, source: str) -> RankedItem:
    return RankedItem(
        title=title,
        url="https://example.com/story",
        source=source,
        summary="Story summary.",
    )


def _config(openai_api_key: str) -> AppConfig:
    return AppConfig(
        location=LocationConfig(
            name="Johannesburg",
            latitude=-26.2041,
            longitude=28.0473,
            timezone="Africa/Johannesburg",
        ),
        email=EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_use_tls=True,
            smtp_username="sender@example.com",
            smtp_password="secret",
            email_from="sender@example.com",
            email_to=["reader@example.com"],
            subject_prefix="Shivz Daily Brief",
        ),
        whatsapp=WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000"],
            api_version="v24.0",
        ),
        couple=CoupleBriefConfig(
            email_to=["spouse@example.com"],
            subject_prefix="Team ShiNola - Our Daily Brief",
            names="you two",
            reminders=["Check the shared Gmail calendars."],
        ),
        google_calendar=GoogleCalendarConfig(
            enabled=False,
            credentials_file=Path("credentials.json"),
            token_file=Path("token.json"),
            calendars=[CalendarSourceConfig(calendar_id="primary", label="Primary")],
            lookahead_days=3,
            max_events_per_calendar=12,
        ),
        news_feeds=[FeedConfig(name="News", url="https://example.com/rss")],
        ai_tech_feeds=[FeedConfig(name="AI", url="https://example.com/ai/rss")],
        top_n=5,
        openai_api_key=openai_api_key,
        openai_model="gpt-5",
        market_pulse_enabled=True,
        weather_locations=[],
    )


if __name__ == "__main__":
    unittest.main()
