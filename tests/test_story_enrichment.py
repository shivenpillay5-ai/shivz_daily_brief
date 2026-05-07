from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.models import RankedItem
from daily_brief.tools.story_enrichment import (
    enrich_story_summaries,
    extract_article_summary,
)


class StoryEnrichmentTests(unittest.TestCase):
    def test_extract_article_summary_prefers_article_paragraphs(self) -> None:
        article_html = """
        <html>
          <head>
            <meta name="description" content="Short meta description.">
          </head>
          <body>
            <p>Advertisement</p>
            <p>The first useful paragraph explains the situation with enough context for a fuller digest in the daily brief and gives the reader a real scan of what happened.</p>
            <p>The second useful paragraph adds consequences, timing, and the next expected step so the article card does not feel like a headline with decoration or unnecessary empty space underneath.</p>
          </body>
        </html>
        """

        summary = extract_article_summary(article_html)

        self.assertIn("first useful paragraph", summary)
        self.assertIn("second useful paragraph", summary)
        self.assertNotIn("Short meta description", summary)

    @patch("daily_brief.tools.story_enrichment.get_text")
    def test_enrich_story_summaries_replaces_thin_summary(self, get_text_mock) -> None:
        get_text_mock.return_value = """
        <html>
          <body>
            <p>This article gives a fuller account of the story, including who is involved, what changed, and why readers should care about the development today before deciding whether to open the full link.</p>
            <p>It also adds useful background and a clear next step, which makes the daily brief card feel informative without forcing extra empty space into the article layout.</p>
          </body>
        </html>
        """
        item = RankedItem(
            title="Story",
            url="https://example.com/story",
            source="Example",
            summary="Tiny summary.",
        )

        enriched = enrich_story_summaries([item])

        self.assertEqual(len(enriched), 1)
        self.assertIn("fuller account", enriched[0].summary)
        self.assertNotEqual(enriched[0].summary, item.summary)

    @patch("daily_brief.tools.story_enrichment.get_text")
    def test_enrich_story_summaries_leaves_full_summary_alone(self, get_text_mock) -> None:
        item = RankedItem(
            title="Story",
            url="https://example.com/story",
            source="Example",
            summary=" ".join(f"word{index}" for index in range(50)),
        )

        enriched = enrich_story_summaries([item])

        self.assertEqual(enriched[0], item)
        get_text_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
