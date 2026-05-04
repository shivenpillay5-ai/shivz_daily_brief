from __future__ import annotations

"""WhatsApp sending tool used by DailyBriefAgent."""

from collections.abc import Callable

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
    template_name: str = "hello_world",
    language_code: str = "en_US",
) -> list[dict[str, object]]:
    _validate_whatsapp_config(config)

    def build_payload(recipient: str) -> dict[str, object]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
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
            failures.append(f"{recipient}: {exc}")
            print(f"WhatsApp API rejected message for {recipient}: {exc}")
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

    print(f"WhatsApp API accepted message for {recipient}: {message_id}")
