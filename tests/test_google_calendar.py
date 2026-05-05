from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path

from daily_brief.config import CalendarSourceConfig, GoogleCalendarConfig
from daily_brief.tools.google_calendar import (
    fetch_google_calendar_events,
    parse_google_calendar_event,
)


class GoogleCalendarTests(unittest.TestCase):
    def test_fetch_returns_empty_when_disabled(self) -> None:
        events = fetch_google_calendar_events(
            _config(enabled=False),
            start_datetime=datetime(2026, 5, 5, 0, 0),
            end_datetime=datetime(2026, 5, 6, 0, 0),
            timezone_name="Africa/Johannesburg",
        )

        self.assertEqual(events, [])

    def test_parse_timed_event(self) -> None:
        event = parse_google_calendar_event(
            {
                "summary": "School pickup",
                "location": "School",
                "start": {"dateTime": "2026-05-05T14:30:00+02:00"},
                "end": {"dateTime": "2026-05-05T15:00:00+02:00"},
            },
            calendar_id="primary",
            calendar_name="Shiven",
            timezone_name="Africa/Johannesburg",
        )

        self.assertEqual(event.title, "School pickup")
        self.assertEqual(event.calendar_name, "Shiven")
        self.assertEqual(event.start.hour, 14)
        self.assertFalse(event.all_day)
        self.assertEqual(event.location, "School")

    def test_parse_all_day_event(self) -> None:
        event = parse_google_calendar_event(
            {
                "summary": "School holiday",
                "start": {"date": "2026-05-05"},
                "end": {"date": "2026-05-06"},
            },
            calendar_id="primary",
            calendar_name="Family",
            timezone_name="Africa/Johannesburg",
        )

        self.assertEqual(event.title, "School holiday")
        self.assertTrue(event.all_day)
        self.assertEqual(event.start.date().isoformat(), "2026-05-05")


def _config(enabled: bool) -> GoogleCalendarConfig:
    return GoogleCalendarConfig(
        enabled=enabled,
        credentials_file=Path("credentials.json"),
        token_file=Path("token.json"),
        calendars=[CalendarSourceConfig(calendar_id="primary", label="Primary")],
        lookahead_days=3,
        max_events_per_calendar=12,
    )


if __name__ == "__main__":
    unittest.main()
