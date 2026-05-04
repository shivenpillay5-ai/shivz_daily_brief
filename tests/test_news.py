from __future__ import annotations

import unittest

from daily_brief.tools.news import parse_feed


class NewsParsingTests(unittest.TestCase):
    def test_parse_rss_item(self) -> None:
        xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Example story</title>
              <link>https://example.com/story</link>
              <description><![CDATA[<p>A short summary.</p>]]></description>
              <pubDate>Mon, 04 May 2026 05:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>
        """

        items = parse_feed(xml, source="Example", category="world")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Example story")
        self.assertEqual(items[0].url, "https://example.com/story")
        self.assertEqual(items[0].summary, "A short summary.")


if __name__ == "__main__":
    unittest.main()
