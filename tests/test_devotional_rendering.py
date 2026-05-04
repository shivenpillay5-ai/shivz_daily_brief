from __future__ import annotations

import unittest
from datetime import datetime

from daily_brief.models import DevotionalContent, ScriptureVerse
from daily_brief.tools.devotional_rendering import (
    render_devotional_html,
    render_devotional_text,
    render_devotional_whatsapp_text,
)


class DevotionalRenderingTests(unittest.TestCase):
    def test_render_devotional_text_includes_verse_and_reflection(self) -> None:
        text = render_devotional_text(datetime(2026, 5, 4), _devotional())

        self.assertIn("Psalm 118:24", text)
        self.assertIn("This is the day", text)
        self.assertIn("Start with gratitude", text)

    def test_render_devotional_html_escapes_content(self) -> None:
        html = render_devotional_html(datetime(2026, 5, 4), _devotional())

        self.assertIn("Daily Motivation and Bible Verse", html)
        self.assertIn("Psalm 118:24", html)
        self.assertIn("&ldquo;This is the day", html)

    def test_render_devotional_whatsapp_is_compact(self) -> None:
        whatsapp = render_devotional_whatsapp_text(
            datetime(2026, 5, 4),
            _devotional(),
        )

        self.assertIn("*Daily Motivation and Bible Verse*", whatsapp)
        self.assertLess(len(whatsapp), 1800)


def _devotional() -> DevotionalContent:
    return DevotionalContent(
        title="Start With Gratitude",
        verse=ScriptureVerse(
            reference="Psalm 118:24",
            text="This is the day which the LORD hath made; we will rejoice and be glad in it.",
            translation="KJV",
        ),
        reflection="Start with gratitude before the day gets noisy.",
    )


if __name__ == "__main__":
    unittest.main()
