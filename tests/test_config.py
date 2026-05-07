from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.config import load_config


class ConfigTests(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "SMTP_PASSWORD": "abcd efgh\u00a0ijkl mnop",
        },
        clear=True,
    )
    def test_smtp_password_whitespace_is_removed(self) -> None:
        config = load_config()

        self.assertEqual(config.email.smtp_password, "abcdefghijklmnop")

    @patch.dict(
        "os.environ",
        {
            "WEATHER_LOCATIONS": (
                "Midrand|-25.9992|28.1263|Africa/Johannesburg|hourly;"
                "Cape Town|-33.9249|18.4241|Africa/Johannesburg"
            ),
        },
        clear=True,
    )
    def test_weather_locations_are_parsed(self) -> None:
        config = load_config()

        self.assertEqual(
            [location.name for location in config.weather_locations],
            ["Midrand", "Cape Town"],
        )
        self.assertTrue(config.weather_locations[0].hourly)
        self.assertFalse(config.weather_locations[1].hourly)

    @patch.dict(
        "os.environ",
        {
            "WHATSAPP_ENABLED": "true",
            "WHATSAPP_PHONE_NUMBER_ID": "123",
            "WHATSAPP_BUSINESS_ACCOUNT_ID": "456",
            "WHATSAPP_ACCESS_TOKEN": "abc def",
            "WHATSAPP_TO": "27820000000,27830000000",
            "WHATSAPP_TEMPLATE_NAME": "shivz_daily_brief_v1",
            "WHATSAPP_TEMPLATE_LANGUAGE": "en",
        },
        clear=True,
    )
    def test_whatsapp_config_is_parsed(self) -> None:
        config = load_config()

        self.assertTrue(config.whatsapp.enabled)
        self.assertEqual(config.whatsapp.phone_number_id, "123")
        self.assertEqual(config.whatsapp.business_account_id, "456")
        self.assertEqual(config.whatsapp.access_token, "abcdef")
        self.assertEqual(config.whatsapp.recipients, ["27820000000", "27830000000"])
        self.assertEqual(config.whatsapp.template_name, "shivz_daily_brief_v1")
        self.assertEqual(config.whatsapp.template_language, "en")

    @patch.dict(
        "os.environ",
        {
            "WHATSAPP_TO": "+27 82 000 0000, 27-83-000-0000",
        },
        clear=True,
    )
    def test_whatsapp_numbers_are_normalized(self) -> None:
        config = load_config()

        self.assertEqual(config.whatsapp.recipients, ["27820000000", "27830000000"])

    @patch.dict(
        "os.environ",
        {
            "MARKET_PULSE_ENABLED": "false",
        },
        clear=True,
    )
    def test_market_pulse_can_be_disabled(self) -> None:
        config = load_config()

        self.assertFalse(config.market_pulse_enabled)

    @patch.dict(
        "os.environ",
        {
            "DEVOTIONAL_SUBJECT_PREFIX": "Morning Verse",
        },
        clear=True,
    )
    def test_devotional_subject_prefix_is_parsed(self) -> None:
        config = load_config()

        self.assertEqual(config.devotional_subject_prefix, "Morning Verse")

    @patch.dict(
        "os.environ",
        {
            "EMAIL_TO": "main@example.com,family@example.com",
            "DEVOTIONAL_EMAIL_TO": "devotional@example.com,verse@example.com",
            "ALERT_EMAIL_TO": "alerts@example.com",
        },
        clear=True,
    )
    def test_email_recipient_lists_are_parsed(self) -> None:
        config = load_config()

        self.assertEqual(
            config.email.email_to,
            ["main@example.com", "family@example.com"],
        )
        self.assertEqual(
            config.email.devotional_email_to,
            ["devotional@example.com", "verse@example.com"],
        )
        self.assertEqual(config.email.alert_email_to, ["alerts@example.com"])

    @patch.dict(
        "os.environ",
        {
            "COUPLE_EMAIL_TO": "you@example.com,spouse@example.com",
            "COUPLE_SUBJECT_PREFIX": "Custom Couple Brief",
            "COUPLE_NAMES": "Shiv and spouse",
            "COUPLE_REMINDERS": "Check calendars;Confirm dinner plan",
        },
        clear=True,
    )
    def test_couple_config_is_parsed(self) -> None:
        config = load_config()

        self.assertEqual(
            config.couple.email_to,
            ["you@example.com", "spouse@example.com"],
        )
        self.assertEqual(config.couple.subject_prefix, "Custom Couple Brief")
        self.assertEqual(config.couple.names, "Shiv and spouse")
        self.assertEqual(
            config.couple.reminders,
            ["Check calendars", "Confirm dinner plan"],
        )

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_CALENDAR_ENABLED": "true",
            "GOOGLE_CALENDAR_CREDENTIALS_FILE": "config/google-client.json",
            "GOOGLE_CALENDAR_TOKEN_FILE": "config/google-token.json",
            "GOOGLE_CALENDAR_IDS": "primary|Shiven;wife@example.com|Nolene",
            "GOOGLE_CALENDAR_LOOKAHEAD_DAYS": "5",
            "GOOGLE_CALENDAR_MAX_EVENTS_PER_CALENDAR": "9",
        },
        clear=True,
    )
    def test_google_calendar_config_is_parsed(self) -> None:
        config = load_config()

        self.assertTrue(config.google_calendar.enabled)
        self.assertTrue(
            str(config.google_calendar.credentials_file)
            .replace("\\", "/")
            .endswith("config/google-client.json")
        )
        self.assertTrue(
            str(config.google_calendar.token_file)
            .replace("\\", "/")
            .endswith("config/google-token.json")
        )
        self.assertEqual(
            [
                (calendar.calendar_id, calendar.label)
                for calendar in config.google_calendar.calendars
            ],
            [("primary", "Shiven"), ("wife@example.com", "Nolene")],
        )
        self.assertEqual(config.google_calendar.lookahead_days, 5)
        self.assertEqual(config.google_calendar.max_events_per_calendar, 9)


if __name__ == "__main__":
    unittest.main()
