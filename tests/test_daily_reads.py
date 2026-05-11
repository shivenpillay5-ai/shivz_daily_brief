from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from daily_brief.tools.daily_reads import (
    build_daily_history_moment,
    fetch_history_moment,
    select_daily_fun_fact,
)


class DailyReadsTests(unittest.TestCase):
    @patch("daily_brief.tools.daily_reads.get_json")
    def test_fetch_history_moment_reads_wikipedia_selected_event(
        self,
        get_json_mock,
    ) -> None:
        get_json_mock.return_value = {
            "selected": [
                {
                    "year": 1969,
                    "text": "Apollo 11 landed on the Moon",
                    "pages": [
                        {
                            "title": "Apollo_11",
                            "titles": {"normalized": "Apollo 11"},
                            "extract": (
                                "Apollo 11 was the American spaceflight that first"
                                " landed humans on the Moon."
                            ),
                            "content_urls": {
                                "desktop": {
                                    "page": "https://en.wikipedia.org/wiki/Apollo_11"
                                }
                            },
                        }
                    ],
                }
            ]
        }

        moment = fetch_history_moment(datetime(2026, 5, 4))

        self.assertEqual(moment.title, "1969: Apollo 11")
        self.assertEqual(moment.year, 1969)
        self.assertEqual(moment.source, "Wikipedia")
        self.assertEqual(moment.source_url, "https://en.wikipedia.org/wiki/Apollo_11")
        self.assertIn("On this date in 1969", moment.paragraph)
        self.assertIn("Moon", moment.paragraph)
        args, kwargs = get_json_mock.call_args
        self.assertIn("/05/04", args[0])
        self.assertEqual(kwargs["timeout_seconds"], 12)

    @patch("daily_brief.tools.daily_reads.get_json")
    def test_fetch_history_moment_tries_events_feed_after_selected_fails(
        self,
        get_json_mock,
    ) -> None:
        get_json_mock.side_effect = [
            RuntimeError("selected unavailable"),
            {
                "events": [
                    {
                        "year": 2001,
                        "text": "Wikipedia became available online",
                        "pages": [
                            {
                                "title": "Wikipedia",
                                "extract": "Wikipedia is a free online encyclopedia.",
                            }
                        ],
                    }
                ]
            },
        ]

        moment = fetch_history_moment(datetime(2026, 5, 4))

        self.assertEqual(moment.title, "2001: Wikipedia")
        self.assertEqual(get_json_mock.call_count, 2)
        self.assertIn("/events/05/04", get_json_mock.call_args.args[0])

    @patch("daily_brief.tools.daily_reads.fetch_history_moment")
    def test_build_daily_history_moment_uses_fallback_when_source_fails(
        self,
        fetch_history_moment_mock,
    ) -> None:
        fetch_history_moment_mock.side_effect = RuntimeError("source down")

        moment = build_daily_history_moment(datetime(2026, 5, 4))

        self.assertEqual(moment.source, "Curated fallback")
        self.assertTrue(moment.title)
        self.assertTrue(moment.paragraph)

    def test_fun_fact_rotates_daily(self) -> None:
        first = select_daily_fun_fact(datetime(2026, 5, 4))
        second = select_daily_fun_fact(datetime(2026, 5, 5))

        self.assertNotEqual(first.title, second.title)
        self.assertTrue(first.body)


if __name__ == "__main__":
    unittest.main()
