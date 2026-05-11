from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.config import EmailConfig
from daily_brief.tools.email import InlineImage, UNDISCLOSED_RECIPIENTS, send_email


class EmailToolTests(unittest.TestCase):
    @patch("daily_brief.tools.email.smtplib.SMTP")
    def test_send_email_hides_configured_recipients(self, smtp_mock) -> None:
        smtp = smtp_mock.return_value.__enter__.return_value
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_use_tls=True,
            smtp_username="sender@example.com",
            smtp_password="secret",
            email_from="sender@example.com",
            email_to=["reader@example.com", "family@example.com"],
            subject_prefix="Shivz Daily Brief",
        )

        send_email(
            config,
            subject="Morning brief",
            text_body="Plain text",
            html_body="<p>Plain text</p>",
        )

        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["To"], UNDISCLOSED_RECIPIENTS)
        self.assertIsNone(message["Bcc"])
        self.assertEqual(
            smtp.send_message.call_args.kwargs["to_addrs"],
            ["reader@example.com", "family@example.com"],
        )

    @patch("daily_brief.tools.email.smtplib.SMTP")
    def test_send_email_can_attach_inline_images(self, smtp_mock) -> None:
        smtp = smtp_mock.return_value.__enter__.return_value
        config = _email_config()

        send_email(
            config,
            subject="Morning brief",
            text_body="Plain text",
            html_body='<p>Plain text</p><img src="cid:meal-image">',
            inline_images=[
                InlineImage(
                    content_id="meal-image",
                    data=b"image-bytes",
                    maintype="image",
                    subtype="jpeg",
                    filename="meal.jpg",
                )
            ],
        )

        message = smtp.send_message.call_args.args[0]
        html_parts = [
            part for part in message.walk() if part.get_content_type() == "text/html"
        ]
        image_parts = [
            part for part in message.walk() if part.get_content_maintype() == "image"
        ]
        self.assertIn('cid:meal-image', html_parts[0].get_content())
        self.assertEqual(len(image_parts), 1)
        self.assertEqual(image_parts[0]["Content-ID"], "<meal-image>")
        self.assertEqual(image_parts[0].get_content_disposition(), "inline")
        self.assertEqual(image_parts[0].get_filename(), "meal.jpg")
        self.assertEqual(image_parts[0].get_payload(decode=True), b"image-bytes")


def _email_config() -> EmailConfig:
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_use_tls=True,
        smtp_username="sender@example.com",
        smtp_password="secret",
        email_from="sender@example.com",
        email_to=["reader@example.com"],
        subject_prefix="Shivz Daily Brief",
    )


if __name__ == "__main__":
    unittest.main()
