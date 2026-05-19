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
        get_text_mock.side_effect = [
            """
        <html>
          <body>
            <h2>Products in Checkers specials</h2>
            <div>Catalogue</div><div>Page</div><div>Products</div><div>Description</div><div>Price</div>
            <table class="table monitoring-products-table">
              <tr>
                <td class="image-cell" rowspan="2">
                  <a href="/checkers-specials/catalogue-1">
                    <img src="/public/gimg/checkers-160-165.jpg">
                  </a>
                  <span>11/05 - 20/05/2026</span>
                </td>
                <td>1</td><td><a href="/products/canola-oil">canola oil</a></td><td>B-Well Pure Canola Oil</td><td>R 69.99</td>
              </tr>
              <tr>
                <td><a href="/products/cereals">cereals</a></td><td>Kellogg's All Bran Flakes Cereal</td><td>R 54.99</td>
              </tr>
            </table>
            <h2>Latest specials</h2>
          </body>
        </html>
        """,
            """
        <html>
          <body>
            <table>
              <tr>
                <td>Checkers</td>
                <td>B-Well Pure Canola Oil</td>
                <td><img src="/public/gimg/2/8/5/2/9/1/2/b-well-pure-canola-oil--2852912.jpg" alt="B-Well Pure Canola Oil"></td>
                <td>R 69.99</td>
              </tr>
            </table>
          </body>
        </html>
        """,
            """
        <html>
          <body>
            <table>
              <tr>
                <td>Checkers</td>
                <td>Kellogg's All Bran Flakes Cereal</td>
                <td><img src="/public/gimg/2/8/5/0/0/5/9/2850059-1080-1080.jpg" alt="Kellogg's All Bran Flakes Cereal"></td>
                <td>R 54.99</td>
              </tr>
            </table>
          </body>
        </html>
        """,
        ]

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
        self.assertEqual(specials[0].category, "Pantry Staples")
        self.assertEqual(
            specials[0].image_url,
            "https://my-catalogue.co.za/public/gimg/2/8/5/2/9/1/2/b-well-pure-canola-oil--2852912.jpg",
        )
        self.assertEqual(specials[1].image_url, "")
        self.assertEqual(
            specials[0].catalogue_url,
            "https://my-catalogue.co.za/checkers-specials/catalogue-1",
        )

    @patch("daily_brief.tools.grocery_specials.get_text")
    def test_woolworths_embedded_records_are_enriched(self, get_text_mock) -> None:
        get_text_mock.return_value = """
        <html><script>
        {"records":[
          {
            "attributes":{
              "p_displayName":"Large Carrots 1 kg",
              "p_defaultCategoryName":"Carrots",
              "p_externalImageReference":"https://assets.example/carrot.jpg",
              "detailPageURL":"/prod/Food/Promotions/Buy-2-Or-More-And-Save/Buy-any-2-save-R10/Large-Carrots/_/A-123"
            },
            "startingPrice":{
              "p_pl10":29.99,
              "p_pl30":19.99,
              "p_pl30_kilogramPrice":19.99
            },
            "priceRangeStatus":{"p_pl30":false}
          }
        ]}
        </script></html>
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

        special = content.stores[0].specials[0]
        self.assertEqual(special.item_name, "Large Carrots 1 kg")
        self.assertEqual(special.price, "R19.99")
        self.assertEqual(special.regular_price, "R29.99")
        self.assertEqual(special.saving_amount, "R10.00")
        self.assertEqual(special.saving_percent, 33.3)
        self.assertEqual(special.category, "Fresh Produce")
        self.assertEqual(special.image_url, "https://assets.example/carrot.jpg")

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
            html = render_grocery_html(datetime(2026, 5, 26), content)
            self.assertIn("Where to shop", html)
            self.assertIn("Top 10 by store", html)
            self.assertIn("Top 10 at Checkers", html)
            self.assertIn("https://example.com/apple.jpg", html)
            self.assertIn("Was R49.99 | Save R10.00 | 20% off", html)

            with patch(
                "daily_brief.tools.grocery_rendering.get_bytes",
                side_effect=RuntimeError("offline"),
            ):
                paths = write_grocery_store_pdfs(
                    datetime(2026, 5, 26),
                    content,
                    Path(temp_dir),
                )

            self.assertEqual(len(paths), 2)
            self.assertTrue(all(path.read_bytes().startswith(b"%PDF-1.4") for path in paths))


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
        category="Fresh Produce",
        image_url="https://example.com/apple.jpg",
        regular_price="R49.99",
        saving_amount="R10.00",
        saving_percent=20.0,
        deal_score=60,
    )


if __name__ == "__main__":
    unittest.main()
