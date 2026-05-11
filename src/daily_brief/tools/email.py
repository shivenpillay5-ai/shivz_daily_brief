from __future__ import annotations

"""Email sending tool used by DailyBriefAgent."""

import smtplib
from collections.abc import Sequence
from dataclasses import dataclass
from email.message import EmailMessage

from daily_brief.config import EmailConfig


UNDISCLOSED_RECIPIENTS = "Undisclosed recipients:;"


@dataclass(frozen=True)
class InlineImage:
    content_id: str
    data: bytes
    maintype: str
    subtype: str
    filename: str


def send_email(
    config: EmailConfig,
    subject: str,
    text_body: str,
    html_body: str,
    inline_images: Sequence[InlineImage] | None = None,
) -> None:
    _validate_email_config(config)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.email_from
    message["To"] = UNDISCLOSED_RECIPIENTS
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    _add_inline_images(message, inline_images or [])

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        if config.smtp_use_tls:
            smtp.starttls()
        if config.smtp_username:
            smtp.login(config.smtp_username, config.smtp_password)
        smtp.send_message(message, to_addrs=config.email_to)


def _validate_email_config(config: EmailConfig) -> None:
    missing = []
    if not config.smtp_host:
        missing.append("SMTP_HOST")
    if not config.email_from:
        missing.append("EMAIL_FROM")
    if not config.email_to:
        missing.append("EMAIL_TO")
    if config.smtp_username and not config.smtp_password:
        missing.append("SMTP_PASSWORD")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing email configuration: {joined}")


def _add_inline_images(
    message: EmailMessage,
    inline_images: Sequence[InlineImage],
) -> None:
    if not inline_images:
        return

    html_part = message.get_payload()[-1]
    for image in inline_images:
        html_part.add_related(
            image.data,
            maintype=image.maintype,
            subtype=image.subtype,
            cid=f"<{image.content_id}>",
            filename=image.filename,
            disposition="inline",
        )
