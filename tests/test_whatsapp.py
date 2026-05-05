from __future__ import annotations

import unittest
from unittest.mock import patch

from daily_brief.config import WhatsAppConfig
from daily_brief.tools.whatsapp import send_whatsapp_message, send_whatsapp_template


class WhatsAppTests(unittest.TestCase):
    @patch("daily_brief.tools.whatsapp.post_json")
    def test_send_whatsapp_message_posts_to_each_recipient(self, post_json_mock) -> None:
        post_json_mock.return_value = {"messages": [{"id": "message-id"}]}
        config = WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000", "27830000000"],
            api_version="v24.0",
        )

        send_whatsapp_message(config, "hello")

        self.assertEqual(post_json_mock.call_count, 2)
        first_payload = post_json_mock.call_args_list[0].kwargs["payload"]
        self.assertEqual(first_payload["to"], "27820000000")
        self.assertEqual(first_payload["text"]["body"], "hello")

    @patch("daily_brief.tools.whatsapp.post_json")
    def test_send_whatsapp_message_continues_after_recipient_failure(
        self,
        post_json_mock,
    ) -> None:
        post_json_mock.side_effect = [
            {"messages": [{"id": "message-id"}]},
            RuntimeError("recipient not allowed"),
            {"messages": [{"id": "message-id-2"}]},
        ]
        config = WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000", "27830000000", "27840000000"],
            api_version="v24.0",
        )

        responses = send_whatsapp_message(config, "hello")

        self.assertEqual(post_json_mock.call_count, 3)
        self.assertEqual(len(responses), 2)

    @patch("daily_brief.tools.whatsapp.post_json")
    @patch("builtins.print")
    def test_send_whatsapp_message_raises_when_all_recipients_fail(
        self,
        print_mock,
        post_json_mock,
    ) -> None:
        post_json_mock.side_effect = RuntimeError("recipient not allowed")
        config = WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000"],
            api_version="v24.0",
        )

        with self.assertRaisesRegex(RuntimeError, "rejected all recipients"):
            send_whatsapp_message(config, "hello")
        printed = "\n".join(str(call.args[0]) for call in print_mock.call_args_list)
        self.assertIn("...0000", printed)
        self.assertNotIn("27820000000", printed)

    @patch("daily_brief.tools.whatsapp.post_json")
    def test_send_whatsapp_template_uses_configured_template(self, post_json_mock) -> None:
        post_json_mock.return_value = {"messages": [{"id": "message-id"}]}
        config = WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000"],
            api_version="v24.0",
            template_name="shivz_daily_brief_v1",
            template_language="en",
        )

        send_whatsapp_template(
            config,
            body_parameters=["Monday, 04 May 2026", "Weather", "World", "AI"],
        )

        payload = post_json_mock.call_args.kwargs["payload"]
        self.assertEqual(payload["type"], "template")
        self.assertEqual(payload["template"]["name"], "shivz_daily_brief_v1")
        self.assertEqual(payload["template"]["language"]["code"], "en")
        body_component = payload["template"]["components"][0]
        self.assertEqual(body_component["type"], "body")
        self.assertEqual(
            [parameter["text"] for parameter in body_component["parameters"]],
            ["Monday, 04 May 2026", "Weather", "World", "AI"],
        )

    @patch("daily_brief.tools.whatsapp.post_json")
    def test_send_whatsapp_template_sanitizes_body_parameters(
        self,
        post_json_mock,
    ) -> None:
        post_json_mock.return_value = {"messages": [{"id": "message-id"}]}
        config = WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000"],
            api_version="v24.0",
        )

        send_whatsapp_template(
            config,
            body_parameters=["Weather\nWorld\tAI", "Too    many spaces"],
        )

        payload = post_json_mock.call_args.kwargs["payload"]
        body_component = payload["template"]["components"][0]
        self.assertEqual(
            [parameter["text"] for parameter in body_component["parameters"]],
            ["Weather | World AI", "Too many spaces"],
        )

    @patch("daily_brief.tools.whatsapp.post_json")
    def test_send_whatsapp_template_can_override_config(self, post_json_mock) -> None:
        post_json_mock.return_value = {"messages": [{"id": "message-id"}]}
        config = WhatsAppConfig(
            enabled=True,
            phone_number_id="123",
            business_account_id="456",
            access_token="secret",
            recipients=["27820000000"],
            api_version="v24.0",
        )

        send_whatsapp_template(
            config,
            template_name="custom_template",
            language_code="en_US",
        )

        payload = post_json_mock.call_args.kwargs["payload"]
        self.assertEqual(payload["template"]["name"], "custom_template")
        self.assertEqual(payload["template"]["language"]["code"], "en_US")


if __name__ == "__main__":
    unittest.main()
