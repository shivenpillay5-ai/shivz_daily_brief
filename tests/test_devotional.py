from __future__ import annotations

import json
import unittest
from datetime import datetime
from unittest.mock import patch

from daily_brief.config import (
    AppConfig,
    EmailConfig,
    FeedConfig,
    LocationConfig,
    WhatsAppConfig,
)
from daily_brief.tools.devotional import build_daily_devotional, select_daily_verse


class DevotionalTests(unittest.TestCase):
    def test_build_daily_devotional_uses_fallback_without_openai_key(self) -> None:
        content = build_daily_devotional(
            brief_date=datetime(2026, 5, 4),
            config=_config(openai_api_key=""),
            use_openai=True,
        )

        self.assertEqual(content.verse.translation, "KJV")
        self.assertTrue(content.verse.reference)
        self.assertTrue(content.reflection)
        self.assertFalse(content.used_openai)

    def test_select_daily_verse_is_repeatable_for_same_date(self) -> None:
        date = datetime(2026, 5, 4)

        self.assertEqual(select_daily_verse(date), select_daily_verse(date))

    @patch("daily_brief.tools.devotional.post_json")
    def test_build_daily_devotional_uses_openai_json(self, post_json_mock) -> None:
        post_json_mock.return_value = {
            "output_text": json.dumps(
                {
                    "title": "Grace For Today",
                    "reflection": "A warm reflection about receiving the day with faith.",
                }
            )
        }

        content = build_daily_devotional(
            brief_date=datetime(2026, 5, 4),
            config=_config(openai_api_key="secret"),
            use_openai=True,
        )

        self.assertEqual(content.title, "Grace For Today")
        self.assertTrue(content.used_openai)
        self.assertEqual(post_json_mock.call_count, 1)


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
