from __future__ import annotations

import unittest
from pathlib import Path


class LiveMarketsPageTests(unittest.TestCase):
    def test_live_markets_page_includes_quotes_and_fetch_helpers(self) -> None:
        page = Path("docs/live-markets.html").read_text(encoding="utf-8")

        self.assertIn("Markets At A Glance", page)
        self.assertIn("Rand Crosses", page)
        self.assertIn("Metals And Brent", page)
        quote_config = page.split("const QUOTES = [", 1)[1]
        self.assertLess(quote_config.index("USD/ZAR"), quote_config.index("GBP/ZAR"))
        self.assertLess(quote_config.index("GBP/ZAR"), quote_config.index("Gold"))
        self.assertLess(quote_config.index("Gold"), quote_config.index("Silver"))
        self.assertLess(quote_config.index("Silver"), quote_config.index("Brent"))
        self.assertIn("api.frankfurter.dev", page)
        self.assertIn("query1.finance.yahoo.com", page)
        self.assertIn("function fetchFxQuote", page)
        self.assertIn("function fetchYahooQuote", page)
        self.assertIn("Refresh now", page)


if __name__ == "__main__":
    unittest.main()
