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


if __name__ == "__main__":
    unittest.main()
