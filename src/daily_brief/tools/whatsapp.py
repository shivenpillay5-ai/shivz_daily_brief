from __future__ import annotations

"""WhatsApp sending tool used by DailyBriefAgent."""

import re
from collections.abc import Callable, Sequence

from daily_brief.config import WhatsAppConfig
from daily_brief.http_client import post_json


def send_whatsapp_message(config: WhatsAppConfig, body: str) -> list[dict[str, object]]:
    _validate_whatsapp_config(config)

    def build_payload(recipient: str) -> dict[str, object]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": body,
            },
        }

    return _send_to_recipients(config, build_payload)


def send_whatsapp_template(
    config: WhatsAppConfig,
    template_name: str | None = None,
    language_code: str | None = None,
    body_parameters: Sequence[str] | None = None,
) -> list[dict[str, object]]:
    _validate_whatsapp_config(config)
    resolved_template_name = template_name or config.template_name
    resolved_language_code = language_code or config.template_language

    def build_payload(recipient: str) -> dict[str, object]:
        template: dict[str, object] = {
            "name": resolved_template_name,
            "language": {"code": resolved_language_code},
        }
        if body_parameters:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": _sanitize_template_parameter(parameter)}
                        for parameter in body_parameters
                    ],
                }
            ]

        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": template,
        }

    return _send_to_recipients(config, build_payload)


def _send_to_recipients(
    config: WhatsAppConfig,
    build_payload: Callable[[str], dict[str, object]],
) -> list[dict[str, object]]:
    url = (
        f"https://graph.facebook.com/{config.api_version}/"
        f"{config.phone_number_id}/messages"
    )
    headers = {"Authorization": f"Bearer {config.access_token}"}
    responses: list[dict[str, object]] = []
    failures: list[str] = []

    for recipient in config.recipients:
        try:
            response = post_json(
                url,
                payload=build_payload(recipient),
                headers=headers,
            )
        except RuntimeError as exc:
            masked_recipient = _mask_recipient(recipient)
            failures.append(f"{masked_recipient}: {exc}")
            print(f"WhatsApp API rejected message for {masked_recipient}: {exc}")
            continue

        _print_response(recipient, response)
        responses.append(response)

    if failures and not responses:
        joined = "; ".join(failures)
        raise RuntimeError(f"WhatsApp API rejected all recipients: {joined}")

    return responses


def _validate_whatsapp_config(config: WhatsAppConfig) -> None:
    missing = []
    if not config.enabled:
        missing.append("WHATSAPP_ENABLED=true")
    if not config.phone_number_id:
        missing.append("WHATSAPP_PHONE_NUMBER_ID")
    if not config.access_token:
        missing.append("WHATSAPP_ACCESS_TOKEN")
    if not config.recipients:
        missing.append("WHATSAPP_TO")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing WhatsApp configuration: {joined}")


def _print_response(recipient: str, response: dict[str, object]) -> None:
    message_id = "<unknown>"
    messages = response.get("messages")
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        raw_id = messages[0].get("id")
        if isinstance(raw_id, str):
            message_id = raw_id

    print(f"WhatsApp API accepted message for {_mask_recipient(recipient)}: {message_id}")


def _mask_recipient(recipient: str) -> str:
    if len(recipient) <= 4:
        return "<masked>"
    return f"...{recipient[-4:]}"


def _sanitize_template_parameter(parameter: object) -> str:
    text = str(parameter).replace("\r\n", " | ").replace("\n", " | ")
    text = text.replace("\r", " | ").replace("\t", " ")
    return re.sub(r"\s{2,}", " ", text).strip()
