from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

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
from daily_brief.models import CalendarEvent, DailyFunFact, HistoryMoment
from daily_brief.tools.couple import (
    build_couple_brief,
    select_daily_meal,
    select_weekly_marriage_spark,
)


class CoupleBriefTests(unittest.TestCase):
    def test_build_couple_brief_uses_configured_names_and_reminders(self) -> None:
        content = build_couple_brief(
            brief_date=datetime(2026, 5, 4),
            config=_config(),
        )

        self.assertEqual(content.names, "you two")
        self.assertEqual(content.reminders, ["Check calendars", "Confirm dinner"])
        self.assertTrue(content.meal.title)
        self.assertTrue(content.meal.ingredients)
        self.assertTrue(content.meal.steps)
        self.assertTrue(content.meal.image_url)
        self.assertTrue(content.spark.title)
        self.assertTrue(content.closing)
        self.assertIsNone(content.history_moment)
        self.assertIsNone(content.fun_fact)

    def test_meal_rotates_daily(self) -> None:
        first = select_daily_meal(datetime(2026, 5, 4))
        second = select_daily_meal(datetime(2026, 5, 5))

        self.assertNotEqual(first.title, second.title)

    def test_marriage_spark_stays_stable_for_the_week(self) -> None:
        monday = select_weekly_marriage_spark(datetime(2026, 5, 4))
        friday = select_weekly_marriage_spark(datetime(2026, 5, 8))

        self.assertEqual(monday, friday)

    @patch("daily_brief.tools.couple.select_daily_fun_fact")
    @patch("daily_brief.tools.couple.build_daily_history_moment")
    def test_build_couple_brief_adds_daily_reads_when_enabled(
        self,
        build_daily_history_moment_mock,
        select_daily_fun_fact_mock,
    ) -> None:
        build_daily_history_moment_mock.return_value = HistoryMoment(
            title="1969: Apollo 11",
            paragraph="On this date in 1969, humans landed on the Moon.",
            year=1969,
            source="Wikipedia",
            source_url="https://example.com/apollo-11",
        )
        select_daily_fun_fact_mock.return_value = DailyFunFact(
            title="The dot has a name",
            body="The small dot above a lowercase i or j is called a tittle.",
        )

        content = build_couple_brief(
            brief_date=datetime(2026, 5, 4),
            config=_config(daily_reads_enabled=True),
        )

        self.assertEqual(content.history_moment.title, "1969: Apollo 11")
        self.assertEqual(content.fun_fact.title, "The dot has a name")
        build_daily_history_moment_mock.assert_called_once()
        select_daily_fun_fact_mock.assert_called_once()

    @patch("daily_brief.tools.couple.fetch_google_calendar_events")
    def test_build_couple_brief_fetches_google_calendar_when_enabled(
        self,
        fetch_google_calendar_events_mock,
    ) -> None:
        fetch_google_calendar_events_mock.return_value = [
            CalendarEvent(
                calendar_id="primary",
                calendar_name="Family",
                title="Swimming",
                start=datetime(2026, 5, 4, 17, 30, tzinfo=ZoneInfo("Africa/Johannesburg")),
            )
        ]

        content = build_couple_brief(
            brief_date=datetime(2026, 5, 4, 8, 0),
            config=_config(google_enabled=True),
        )

        self.assertEqual(content.calendar_events[0].title, "Swimming")
        fetch_google_calendar_events_mock.assert_called_once()

    @patch("daily_brief.tools.couple.fetch_google_calendar_events")
    def test_build_couple_brief_keeps_building_when_calendar_fails(
        self,
        fetch_google_calendar_events_mock,
    ) -> None:
        fetch_google_calendar_events_mock.side_effect = RuntimeError("auth missing")

        content = build_couple_brief(
            brief_date=datetime(2026, 5, 4, 8, 0),
            config=_config(google_enabled=True),
        )

        self.assertIn("Google Calendar could not be read", content.calendar_note)


def _config(
    google_enabled: bool = False,
    daily_reads_enabled: bool = False,
) -> AppConfig:
    google_calendar = GoogleCalendarConfig(
        enabled=google_enabled,
        credentials_file=Path("credentials.json"),
        token_file=Path("token.json"),
        calendars=[CalendarSourceConfig(calendar_id="primary", label="Primary")],
        lookahead_days=3,
        max_events_per_calendar=12,
    )

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
            email_to=["family@example.com"],
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
            reminders=["Check calendars", "Confirm dinner"],
            daily_reads_enabled=daily_reads_enabled,
        ),
        google_calendar=google_calendar,
        news_feeds=[FeedConfig(name="News", url="https://example.com/rss")],
        ai_tech_feeds=[FeedConfig(name="AI", url="https://example.com/ai/rss")],
        top_n=5,
        openai_api_key="",
        openai_model="gpt-5",
        market_pulse_enabled=True,
        weather_locations=[],
    )


if __name__ == "__main__":
    unittest.main()
