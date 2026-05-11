from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.tools.email_images import fetch_inline_image


class EmailImagesTests(unittest.TestCase):
    @patch("daily_brief.tools.email_images.get_bytes")
    def test_fetch_inline_image_builds_email_image_from_content_type(
        self,
        get_bytes_mock,
    ) -> None:
        get_bytes_mock.return_value = (b"image", "image/png")

        image = fetch_inline_image(
            "https://example.com/photo",
            content_id="meal-image",
            filename_stem="Breakfast for dinner",
        )

        self.assertEqual(image.content_id, "meal-image")
        self.assertEqual(image.data, b"image")
        self.assertEqual(image.maintype, "image")
        self.assertEqual(image.subtype, "png")
        self.assertEqual(image.filename, "breakfast-for-dinner.png")

    @patch("daily_brief.tools.email_images.get_bytes")
    def test_fetch_inline_image_rejects_non_image_content(
        self,
        get_bytes_mock,
    ) -> None:
        get_bytes_mock.return_value = (b"not an image", "text/html")

        with self.assertRaisesRegex(RuntimeError, "Unsupported image"):
            fetch_inline_image(
                "https://example.com/photo",
                content_id="meal-image",
                filename_stem="Meal",
            )


if __name__ == "__main__":
    unittest.main()
