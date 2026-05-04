from __future__ import annotations

"""Rendering for the daily devotional email and WhatsApp text."""

import html
from datetime import datetime

from daily_brief.models import DevotionalContent


DEVOTIONAL_NAME = "Daily Motivation and Bible Verse"


def render_devotional_text(
    brief_date: datetime,
    devotional: DevotionalContent,
) -> str:
    return "\n".join(
        [
            f"Daily Motivation and Bible Verse - {brief_date:%A, %d %B %Y}",
            "",
            devotional.title,
            "",
            f"{devotional.verse.reference} ({devotional.verse.translation})",
            f'"{devotional.verse.text}"',
            "",
            "What it means today:",
            devotional.reflection,
            "",
            "Start the day:",
            devotional.motivation,
        ]
    )


def render_devotional_html(
    brief_date: datetime,
    devotional: DevotionalContent,
) -> str:
    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f4f0ea;font-family:Segoe UI,Arial,sans-serif;color:#1f2933">
    <div style="display:none;max-height:0;overflow:hidden;color:#f4f0ea">
      A short scripture and reflection for {brief_date:%A, %d %B %Y}.
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f0ea">
      <tr>
        <td align="center" style="padding:30px 12px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px;background:#fffdf8;border-radius:22px;overflow:hidden;box-shadow:0 18px 45px rgba(79,55,35,.16)">
            <tr>
              <td style="padding:32px 34px;background:#31504a;color:#ffffff">
                <div style="display:inline-block;background:#f6dfb4;color:#31504a;border-radius:999px;padding:7px 11px;font-size:12px;letter-spacing:.8px;text-transform:uppercase;font-weight:800">Morning pause</div>
                <h1 style="font-size:34px;line-height:1.08;margin:15px 0 8px;font-weight:850">Daily Motivation and Bible Verse</h1>
                <p style="font-size:15px;line-height:1.5;margin:0;color:#e9f2ee">
                  One scripture, one steady thought, and a quieter way to step into the day.
                </p>
                <div style="margin-top:16px;color:#cfe2dc;font-size:14px;font-weight:700">{brief_date:%A, %d %B %Y}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:30px 34px 34px">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #ead8bd;border-radius:18px;background:#fff8eb">
                  <tr>
                    <td style="padding:24px">
                      <div style="font-size:13px;color:#80623a;font-weight:800;text-transform:uppercase;letter-spacing:.8px">Scripture</div>
                      <h2 style="font-size:25px;line-height:1.2;margin:7px 0 12px;color:#243b35">{html.escape(devotional.title)}</h2>
                      <p style="font-size:22px;line-height:1.5;margin:0;color:#243b35;font-family:Georgia,serif">
                        &ldquo;{html.escape(devotional.verse.text)}&rdquo;
                      </p>
                      <p style="margin:14px 0 0;color:#80623a;font-size:14px;font-weight:800">
                        {html.escape(devotional.verse.reference)} ({html.escape(devotional.verse.translation)})
                      </p>
                    </td>
                  </tr>
                </table>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:26px 0">
                  <tr>
                    <td style="width:56px;height:4px;background:#31504a;border-radius:999px 0 0 999px;font-size:0;line-height:0">&nbsp;</td>
                    <td style="height:4px;background:#ead8bd;border-radius:0 999px 999px 0;font-size:0;line-height:0">&nbsp;</td>
                  </tr>
                </table>

                <div style="font-size:13px;color:#80623a;font-weight:800;text-transform:uppercase;letter-spacing:.8px">What it means today</div>
                <p style="font-size:17px;line-height:1.65;margin:8px 0 0;color:#334e48">
                  {html.escape(devotional.reflection)}
                </p>

                {_motivation_html(devotional)}

                <p style="margin:30px 0 0;color:#87958f;font-size:12px;text-align:center">
                  Built by your Shivz Daily Brief Agent.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def render_devotional_whatsapp_text(
    brief_date: datetime,
    devotional: DevotionalContent,
) -> str:
    return _clip_message(
        "\n".join(
            [
                "*Daily Motivation and Bible Verse*",
                f"{brief_date:%A, %d %B %Y}",
                "",
                f"*{devotional.title}*",
                f"{devotional.verse.reference} ({devotional.verse.translation})",
                f'"{devotional.verse.text}"',
                "",
                f"Thought: {devotional.reflection}",
                "",
                f"Start the day: {devotional.motivation}",
            ]
        )
    )


def _clip_message(value: str, max_chars: int = 1800) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 30].rstrip() + "\n\n...trimmed for WhatsApp"


def _motivation_html(devotional: DevotionalContent) -> str:
    if not devotional.motivation:
        return ""

    return f"""
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:26px;border:1px solid #d7e8df;border-radius:18px;background:#f1faf5">
                  <tr>
                    <td valign="top" style="width:56px;padding:18px 0 18px 18px">
                      <div style="width:42px;height:42px;border-radius:14px;background:#31504a;color:#ffffff;text-align:center;line-height:42px;font-size:23px">+</div>
                    </td>
                    <td style="padding:18px 20px 18px 12px">
                      <div style="font-size:12px;color:#31504a;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Start the day</div>
                      <p style="font-size:16px;line-height:1.58;margin:6px 0 0;color:#334e48">
                        {html.escape(devotional.motivation)}
                      </p>
                    </td>
                  </tr>
                </table>
    """
