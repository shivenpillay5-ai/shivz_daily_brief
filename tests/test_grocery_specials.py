from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from daily_brief.config import GrocerySourceConfig, GrocerySpecialsConfig
from daily_brief.models import GrocerySpecialsContent, GroceryStoreSpecials
from daily_brief.tools.grocery_rendering import (
    render_grocery_html,
    render_grocery_text,
    write_grocery_store_pdfs,
)
from daily_brief.tools.grocery_specials import build_grocery_specials


class GrocerySpecialsTests(unittest.TestCase):
    @patch("daily_brief.tools.grocery_specials.get_text")
    def test_catalogue_specials_are_extracted(self, get_text_mock) -> None:
        get_text_mock.return_value = """
        <html>
          <body>
            <a>0 PnP Super Maize Meal 10kg 11 days R 84,99</a>
            <a>0 PnP All Grain Large Eggs 24s 23 hours R 54,99</a>
          </body>
        </html>
        """

        content = build_grocery_specials(
            datetime(2026, 5, 26),
            _config(
                [
                    GrocerySourceConfig(
                        store_name="Pick n Pay",
                        source_name="Pick n Pay Catalogue Specials",
                        url="https://www.cataloguespecials.co.za/stores/pick-n-pay/specials",
                    )
                ]
            ),
        )

        specials = content.stores[0].specials
        self.assertEqual(len(specials), 2)
        self.assertEqual(specials[0].item_name, "PnP Super Maize Meal 10kg")
        self.assertEqual(specials[0].price, "R84,99")
        self.assertEqual(specials[0].validity, "11 days")

    @patch("daily_brief.tools.grocery_specials.get_text")
    def test_generic_store_page_specials_are_extracted(self, get_text_mock) -> None:
        get_text_mock.return_value = """
        <html>
          <body>
            <div><a>Rosa Tomatoes 400 g</a><span>R 29.99</span></div>
            <div><a>Seedless Grapes 500 g</a><span>Buy any 2 save R10</span><span>R 49.99</span></div>
          </body>
        </html>
        """

        content = build_grocery_specials(
            datetime(2026, 5, 26),
            _config(
                [
                    GrocerySourceConfig(
                        store_name="Woolworths",
                        source_name="Woolworths Food Promotions",
                        url="https://www.woolworths.co.za/cat/Promotions/Save/Food/_/N-1z13sk5",
                    )
                ]
            ),
        )

        specials = content.stores[0].specials
        self.assertEqual([special.item_name for special in specials], [
            "Rosa Tomatoes 400 g",
            "Seedless Grapes 500 g",
        ])
        self.assertEqual(specials[1].promotion, "Buy any 2 save R10")

    @patch("daily_brief.tools.grocery_specials.get_text")
    def test_my_catalogue_product_table_is_extracted(self, get_text_mock) -> None:
        get_text_mock.return_value = """
        <html>
          <body>
            <h2>Products in Checkers specials</h2>
            <div>Catalogue</div><div>Page</div><div>Products</div><div>Description</div><div>Price</div>
            <div>11/05 - 20/05/2026</div>
            <a>1</a><a>canola oil</a><div>B-Well Pure Canola Oil</div><div>R 69.99</div>
            <a>cereals</a><div>Kellogg's All Bran Flakes Cereal</div><div>R 54.99</div>
            <h2>Latest specials</h2>
          </body>
        </html>
        """

        content = build_grocery_specials(
            datetime(2026, 5, 26),
            _config(
                [
                    GrocerySourceConfig(
                        store_name="Checkers",
                        source_name="My Catalogue Product Table",
                        url="https://my-catalogue.co.za/checkers-specials",
                    )
                ]
            ),
        )

        specials = content.stores[0].specials
        self.assertEqual(
            [(special.item_name, special.price, special.validity) for special in specials],
            [
                ("B-Well Pure Canola Oil", "R69.99", "11/05 - 20/05/2026"),
                ("Kellogg's All Bran Flakes Cereal", "R54.99", "11/05 - 20/05/2026"),
            ],
        )

    def test_rendering_writes_store_pdfs(self) -> None:
        content = GrocerySpecialsContent(
            area="Midrand",
            generated_at=datetime(2026, 5, 26),
            stores=[],
        )
        # No configured sources still renders a store-free summary cleanly.
        self.assertIn("Midrand Grocery Specials", render_grocery_text(datetime(2026, 5, 26), content))
        self.assertIn("Midrand Grocery Specials", render_grocery_html(datetime(2026, 5, 26), content))

        with tempfile.TemporaryDirectory() as temp_dir:
            content = GrocerySpecialsContent(
                area="Midrand",
                generated_at=datetime(2026, 5, 26),
                stores=[
                    GroceryStoreSpecials(
                        store_name="Checkers",
                        area="Midrand",
                        specials=[_fixture_special()],
                        source_urls=["https://example.com/checkers"],
                    )
                ],
            )
            paths = write_grocery_store_pdfs(
                datetime(2026, 5, 26),
                content,
                Path(temp_dir),
            )

            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].read_bytes().startswith(b"%PDF-1.4"))


def _config(sources: list[GrocerySourceConfig]) -> GrocerySpecialsConfig:
    return GrocerySpecialsConfig(
        email_to=[],
        subject_prefix="Midrand Grocery Specials",
        area="Midrand",
        sources=sources,
        max_items_per_store=20,
        output_dir=Path("grocery-specials"),
    )


def _fixture_special():
    from daily_brief.models import GrocerySpecial

    return GrocerySpecial(
        store_name="Checkers",
        item_name="Bulk Apples 1.5kg",
        price="R39,99",
        source_name="Checkers fixture",
        source_url="https://example.com/checkers",
    )


if __name__ == "__main__":
    unittest.main()
