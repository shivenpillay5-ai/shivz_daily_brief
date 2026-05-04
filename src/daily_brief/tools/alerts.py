from __future__ import annotations

"""Failure alert email rendering and sending."""

from datetime import datetime
from html import escape
from pathlib import Path

from daily_brief.config import EmailConfig
from daily_brief.tools.email import send_email

MAX_LOG_CHARS = 6000


def read_failure_log(path: Path | None) -> str:
    if path is None:
        return "No failure log path was supplied."
    if not path.exists():
        return f"Failure log was not found: {path}"
    return path.read_text(encoding="utf-8", errors="replace")


def send_failure_alert(
    config: EmailConfig,
    brief_date: datetime,
    log_text: str,
    run_url: str = "",
) -> None:
    subject = f"Shivz Daily Brief failed - {brief_date:%Y-%m-%d}"
    log_tail = _tail_log(log_text)
    send_email(
        config,
        subject=subject,
        text_body=_render_text(brief_date, log_tail, run_url),
        html_body=_render_html(brief_date, log_tail, run_url),
    )


def _tail_log(log_text: str) -> str:
    clean_log = log_text.strip()
    if not clean_log:
        return "The run failed, but no log output was captured."
    if len(clean_log) <= MAX_LOG_CHARS:
        return clean_log
    return "... log trimmed ...\n" + clean_log[-MAX_LOG_CHARS:]


def _render_text(brief_date: datetime, log_tail: str, run_url: str) -> str:
    lines = [
        "Shivz Daily Brief did not send successfully.",
        "",
        f"Date: {brief_date:%A, %d %B %Y}",
        "What happened: GitHub Actions tried the morning run three times.",
        "Next step: Open the run link below and check the final error.",
    ]
    if run_url:
        lines.extend(["", f"Run link: {run_url}"])
    lines.extend(["", "Last captured log output:", log_tail])
    return "\n".join(lines)


def _render_html(brief_date: datetime, log_tail: str, run_url: str) -> str:
    run_link = ""
    if run_url:
        safe_url = escape(run_url, quote=True)
        run_link = (
            f'<p><a href="{safe_url}" '
            'style="color:#0f766e;font-weight:700;text-decoration:none;">'
            "Open the failed GitHub Actions run</a></p>"
        )

    return f"""\
<!doctype html>
<html>
  <body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#08233d;">
    <div style="max-width:720px;margin:0 auto;padding:28px 18px;">
      <div style="background:#ffffff;border:1px solid #d7e3ef;border-radius:14px;padding:24px;">
        <p style="margin:0 0 8px;color:#b42318;font-weight:800;letter-spacing:.08em;text-transform:uppercase;font-size:12px;">
          Daily brief alert
        </p>
        <h1 style="margin:0 0 10px;font-size:26px;line-height:1.2;">
          Shivz Daily Brief did not send
        </h1>
        <p style="margin:0 0 16px;color:#42627d;">
          The scheduled run for {brief_date:%A, %d %B %Y} was tried three times and still failed.
        </p>
        {run_link}
        <h2 style="margin:24px 0 10px;font-size:16px;">Last captured log output</h2>
        <pre style="white-space:pre-wrap;background:#071827;color:#e7f2fb;border-radius:10px;padding:16px;overflow:auto;font-size:13px;line-height:1.45;">{escape(log_tail)}</pre>
      </div>
    </div>
  </body>
</html>
"""
