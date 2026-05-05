from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from daily_brief.models import CalendarEvent, CoupleBriefContent, MarriageSpark, MealIdea
from daily_brief.tools.couple_rendering import render_couple_html, render_couple_text


class CoupleRenderingTests(unittest.TestCase):
    def test_render_couple_text_includes_private_sections(self) -> None:
        text = render_couple_text(datetime(2026, 5, 4), _content())

        self.assertIn("Team ShiNola - Our Daily Brief", text)
        self.assertIn("Calendar snapshot", text)
        self.assertIn("Nudges", text)
        self.assertIn("Meal idea", text)
        self.assertIn("Short recipe", text)
        self.assertIn("This week's marriage spark", text)
        self.assertIn("Chicken pesto wraps", text)
        self.assertIn("School pickup", text)
        self.assertIn("Today", text)

    def test_render_couple_html_escapes_content(self) -> None:
        html = render_couple_html(datetime(2026, 5, 4), _content())

        self.assertIn("&lt;Shiv &amp; spouse&gt;", html)
        self.assertIn("Check &lt;calendar&gt;", html)
        self.assertIn("https://example.com/chicken-wrap.jpg", html)
        self.assertIn("Chicken wrap", html)
        self.assertNotIn("<calendar>", html)


def _content() -> CoupleBriefContent:
    return CoupleBriefContent(
        names="<Shiv & spouse>",
        reminders=["Check <calendar>", "Confirm dinner"],
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
            motivation="Choose one pocket where both of you are present.",
            fun_idea="Take a short walk after dinner.",
            conversation_starter="What can I make lighter?",
        ),
        closing="Keep the day practical and kind.",
        calendar_events=[
            CalendarEvent(
                calendar_id="primary",
                calendar_name="Family",
                title="School pickup",
                start=datetime(
                    2026,
                    5,
                    4,
                    14,
                    30,
                    tzinfo=ZoneInfo("Africa/Johannesburg"),
                ),
                location="School",
            )
        ],
    )


if __name__ == "__main__":
    unittest.main()
