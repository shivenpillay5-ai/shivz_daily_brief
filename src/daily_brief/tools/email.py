from __future__ import annotations

"""Email sending tool used by DailyBriefAgent."""

import smtplib
from email.message import EmailMessage

from daily_brief.config import EmailConfig


UNDISCLOSED_RECIPIENTS = "Undisclosed recipients:;"


def send_email(
    config: EmailConfig,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    _validate_email_config(config)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.email_from
    message["To"] = UNDISCLOSED_RECIPIENTS
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

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
