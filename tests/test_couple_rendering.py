from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from daily_brief.models import (
    CalendarEvent,
    CoupleBriefContent,
    DailyFunFact,
    HistoryMoment,
    MarriageSpark,
    MealIdea,
)
from daily_brief.tools.couple_rendering import render_couple_html, render_couple_text


class CoupleRenderingTests(unittest.TestCase):
    def test_render_couple_text_includes_private_sections(self) -> None:
        text = render_couple_text(datetime(2026, 5, 4), _content())

        self.assertIn("Team ShiNola - Our Daily Brief", text)
        self.assertIn("Calendar snapshot", text)
        self.assertIn("Nudges", text)
        self.assertIn("Meal idea", text)
        self.assertIn("What happened in history today", text)
        self.assertIn("Fun fact of the day", text)
        self.assertIn("Short recipe", text)
        self.assertIn("This week's marriage spark", text)
        self.assertIn("Chicken pesto wraps", text)
        self.assertIn("1969: Apollo 11", text)
        self.assertIn("The dot has a name", text)
        self.assertIn("School pickup", text)
        self.assertIn("Today", text)
        self.assertLess(text.index("Good morning"), text.index("Meal idea"))
        self.assertLess(text.index("Meal idea"), text.index("Calendar snapshot"))
        self.assertLess(
            text.index("Calendar snapshot"),
            text.index("What happened in history today"),
        )
        self.assertLess(
            text.index("What happened in history today"),
            text.index("Fun fact of the day"),
        )
        self.assertLess(
            text.index("Fun fact of the day"),
            text.index("This week's marriage spark"),
        )

    def test_render_couple_html_escapes_content(self) -> None:
        html = render_couple_html(datetime(2026, 5, 4), _content())

        self.assertIn("&lt;Shiv &amp; spouse&gt;", html)
        self.assertIn("Check &lt;calendar&gt;", html)
        self.assertIn("https://example.com/chicken-wrap.jpg", html)
        self.assertIn("Chicken wrap", html)
        self.assertIn("1969: Apollo 11", html)
        self.assertIn("A &lt;moment&gt; worth remembering.", html)
        self.assertIn("https://example.com/history?x=1&amp;y=2", html)
        self.assertIn("The dot has a name", html)
        self.assertIn("lowercase i or j", html)
        self.assertNotIn("<calendar>", html)
        self.assertNotIn("<moment>", html)
        self.assertLess(html.index("Good morning"), html.index("Meal idea"))
        self.assertLess(html.index("Meal idea"), html.index("Calendar snapshot"))
        self.assertLess(
            html.index("Calendar snapshot"),
            html.index("What happened in history today"),
        )
        self.assertLess(
            html.index("What happened in history today"),
            html.index("Fun fact of the day"),
        )
        self.assertLess(
            html.index("Fun fact of the day"),
            html.index("This week's spark"),
        )


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
        history_moment=HistoryMoment(
            title="1969: Apollo 11",
            paragraph="A <moment> worth remembering.",
            year=1969,
            source="Wikipedia",
            source_url="https://example.com/history?x=1&y=2",
        ),
        fun_fact=DailyFunFact(
            title="The dot has a name",
            body="The small dot above a lowercase i or j is called a tittle.",
        ),
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
