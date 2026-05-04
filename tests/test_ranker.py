from __future__ import annotations

import unittest
from datetime import datetime, timezone

from daily_brief.models import FeedItem
from daily_brief.tools.ranking import _fallback_rank


class RankerTests(unittest.TestCase):
    def test_fallback_rank_prefers_source_variety(self) -> None:
        published = datetime(2026, 5, 4, tzinfo=timezone.utc)
        items = [
            FeedItem(f"Story {index}", f"https://a.example/{index}", "Source A", "A", published, "ai")
            for index in range(5)
        ]
        items.append(
            FeedItem("Other story", "https://b.example/1", "Source B", "B", published, "ai")
        )

        ranked = _fallback_rank(items, top_n=3)

        self.assertIn("Source B", {item.source for item in ranked})


if __name__ == "__main__":
    unittest.main()
