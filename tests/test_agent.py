from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from daily_brief.agent import Brief, CoupleBrief, DevotionalBrief, DailyBriefAgent
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
from daily_brief.models import (
    CoupleBriefContent,
    MarketPulse,
    MarketQuote,
    MarriageSpark,
    MealIdea,
    MorningSummary,
    RankedItem,
    ScriptureVerse,
    WeatherReport,
    DevotionalContent,
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

    @patch("daily_brief.agent.build_daily_devotional")
    def test_agent_builds_devotional_brief(self, build_daily_devotional_mock) -> None:
        build_daily_devotional_mock.return_value = DevotionalContent(
            title="Start With Gratitude",
            verse=ScriptureVerse(
                reference="Psalm 118:24",
                text="This is the day which the LORD hath made; we will rejoice and be glad in it.",
                translation="KJV",
            ),
            reflection="Start with gratitude before the day gets noisy.",
        )

        brief = DailyBriefAgent(_config()).build_devotional(
            brief_date=__import__("datetime").datetime(2026, 5, 4),
            use_openai=False,
        )

        self.assertIsInstance(brief, DevotionalBrief)
        self.assertIn("Daily Motivation", brief.subject)
        self.assertIn("Psalm 118:24", brief.text_body)
        self.assertIn("Psalm 118:24", brief.html_body)
        self.assertIn("Psalm 118:24", brief.whatsapp_body)

    @patch("daily_brief.agent.build_couple_brief")
    def test_agent_builds_couple_brief(self, build_couple_brief_mock) -> None:
        build_couple_brief_mock.return_value = _couple_content()

        brief = DailyBriefAgent(_config()).build_couple(
            brief_date=__import__("datetime").datetime(2026, 5, 4),
        )

        self.assertIsInstance(brief, CoupleBrief)
        self.assertIn("Team ShiNola - Our Daily Brief", brief.subject)
        self.assertIn("Chicken pesto wraps", brief.text_body)
        self.assertIn("Chicken pesto wraps", brief.html_body)
        self.assertIn("Check the shared Gmail calendars.", brief.text_body)

    @patch("daily_brief.agent.send_email")
    def test_agent_sends_couple_brief_to_couple_recipients(
        self,
        send_email_mock,
    ) -> None:
        brief = CoupleBrief(
            subject="Team ShiNola - Our Daily Brief - 2026-05-04",
            text_body="text",
            html_body="<p>text</p>",
            content=_couple_content(),
        )

        DailyBriefAgent(_config()).send_couple(brief)

        args, kwargs = send_email_mock.call_args
        self.assertEqual(args[0].email_to, ["spouse@example.com"])
        self.assertEqual(kwargs["subject"], brief.subject)

    def test_agent_requires_couple_recipients_before_sending(self) -> None:
        brief = CoupleBrief(
            subject="Team ShiNola - Our Daily Brief - 2026-05-04",
            text_body="text",
            html_body="<p>text</p>",
            content=_couple_content(),
        )

        with self.assertRaisesRegex(ValueError, "COUPLE_EMAIL_TO"):
            DailyBriefAgent(_config(couple_email_to=[])).send_couple(brief)


def _couple_content() -> CoupleBriefContent:
    return CoupleBriefContent(
        names="you two",
        reminders=["Check the shared Gmail calendars."],
        meal=MealIdea(
            title="Chicken pesto wraps",
            description="Warm wraps with chicken and pesto.",
            ingredients=["Wraps", "Chicken", "Pesto"],
            steps=["Warm wraps.", "Fill and fold."],
            prep_note="Cook extra chicken.",
            image_url="https://example.com/chicken-wrap.jpg",
            image_alt="Chicken wrap",
            image_credit="Photo: Example",
            image_credit_url="https://example.com/photo",
        ),
        spark=MarriageSpark(
            title="Protect one small pocket",
            motivation="Choose one pocket this week where the two of you are present.",
            fun_idea="Take a short walk after dinner.",
            conversation_starter="What can I make lighter?",
        ),
        closing="Keep the day practical and kind.",
    )


def _config(couple_email_to: list[str] | None = None) -> AppConfig:
    if couple_email_to is None:
        couple_email_to = ["spouse@example.com"]

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
            email_to=couple_email_to,
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
