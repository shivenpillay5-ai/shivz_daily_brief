from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.agent import Brief, DailyBriefAgent
from daily_brief.config import (
    AppConfig,
    EmailConfig,
    FeedConfig,
    LocationConfig,
    WhatsAppConfig,
)
from daily_brief.models import (
    MarketPulse,
    MarketQuote,
    MorningSummary,
    RankedItem,
    WeatherReport,
)


class AgentTests(unittest.TestCase):
    @patch("daily_brief.agent.fetch_weather")
    @patch("daily_brief.agent.fetch_market_pulse")
    @patch("daily_brief.agent.fetch_feed_items")
    @patch("daily_brief.agent.rank_items")
    @patch("daily_brief.agent.write_morning_summary")
    def test_agent_builds_brief(
        self,
        write_morning_summary_mock,
        rank_items_mock,
        fetch_feed_items_mock,
        fetch_market_pulse_mock,
        fetch_weather_mock,
    ) -> None:
        fetch_weather_mock.return_value = WeatherReport(
            location_name="Johannesburg",
            temperature_c=21,
            feels_like_c=21,
            humidity_percent=50,
            wind_kmh=11,
            daily_min_c=12,
            daily_max_c=25,
            precipitation_probability_percent=5,
            condition="clear sky",
        )
        fetch_market_pulse_mock.return_value = MarketPulse(
            quotes=[
                MarketQuote(
                    label="USD/ZAR",
                    value=18.42,
                    prefix="R",
                    suffix="",
                    source="Frankfurter",
                    as_of="2026-05-04",
                )
            ]
        )
        write_morning_summary_mock.return_value = MorningSummary(
            headline="Morning Signal",
            body="A useful morning read.",
            bullets=["Weather is calm."],
        )
        fetch_feed_items_mock.return_value = ([], [])
        rank_items_mock.return_value = [
            RankedItem(
                title="Story",
                url="https://example.com",
                source="Example",
                summary="Summary",
            )
        ]

        brief = DailyBriefAgent(_config()).build(
            brief_date=__import__("datetime").datetime(2026, 5, 4),
            use_openai=False,
        )

        self.assertIsInstance(brief, Brief)
        self.assertIn("Shivz Daily Brief", brief.subject)
        self.assertIn("https://example.com", brief.text_body)
        self.assertIn("https://example.com", brief.html_body)
        self.assertIn("https://example.com", brief.whatsapp_body)
        self.assertIn("USD/ZAR", brief.text_body)
        self.assertIn("Morning Signal", brief.html_body)


def _config() -> AppConfig:
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
        news_feeds=[FeedConfig(name="News", url="https://example.com/rss")],
        ai_tech_feeds=[FeedConfig(name="AI", url="https://example.com/ai/rss")],
        top_n=5,
        openai_api_key="",
        openai_model="gpt-5",
        market_pulse_enabled=True,
        weather_locations=[
            LocationConfig(
                name="Midrand",
                latitude=-25.9992,
                longitude=28.1263,
                timezone="Africa/Johannesburg",
                hourly=True,
            )
        ],
    )


if __name__ == "__main__":
    unittest.main()
