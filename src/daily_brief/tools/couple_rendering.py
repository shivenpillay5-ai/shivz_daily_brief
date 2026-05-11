from __future__ import annotations

"""Rendering for the private couple brief email."""

import html
from datetime import datetime

from daily_brief.models import (
    CalendarEvent,
    CoupleBriefContent,
    DailyFunFact,
    HistoryMoment,
)


COUPLE_BRIEF_NAME = "Team ShiNola - Our Daily Brief"


def render_couple_text(
    brief_date: datetime,
    content: CoupleBriefContent,
) -> str:
    reminder_lines = [f"- {reminder}" for reminder in content.reminders]
    calendar_lines = _calendar_text_lines(brief_date, content)
    daily_read_lines = _daily_read_text_lines(content)
    ingredient_lines = [f"- {ingredient}" for ingredient in content.meal.ingredients]
    step_lines = [
        f"{index}. {step}"
        for index, step in enumerate(content.meal.steps, start=1)
    ]
    return "\n".join(
        [
            f"{COUPLE_BRIEF_NAME} - {brief_date:%A, %d %B %Y}",
            "",
            f"Good morning, {content.names}.",
            "",
            "Meal idea:",
            content.meal.title,
            content.meal.description,
            "",
            "Ingredients:",
            *ingredient_lines,
            "",
            "Short recipe:",
            *step_lines,
            "",
            f"Prep note: {content.meal.prep_note}",
            f"{content.meal.image_credit} ({content.meal.image_credit_url})",
            "",
            *calendar_lines,
            "Nudges:",
            *reminder_lines,
            "",
            *daily_read_lines,
            "This week's marriage spark:",
            content.spark.title,
            content.spark.motivation,
            f"Fun thing to try: {content.spark.fun_idea}",
            f"Conversation starter: {content.spark.conversation_starter}",
            "",
            content.closing,
        ]
    )


def render_couple_html(
    brief_date: datetime,
    content: CoupleBriefContent,
) -> str:
    reminders_html = "\n".join(
        f"""
                          <tr>
                            <td style="width:10px;padding:8px 0;vertical-align:top">
                              <div style="width:6px;height:6px;border-radius:50%;background:#d46a4c;margin-top:7px">&nbsp;</div>
                            </td>
                            <td style="padding:5px 0 8px 10px;font-size:15px;line-height:1.5;color:#314251">
                              {html.escape(reminder)}
                            </td>
                          </tr>
        """
        for reminder in content.reminders
    )
    calendar_events_html = _calendar_events_html(brief_date, content)
    calendar_note_html = _calendar_note_html(content)
    daily_reads_html = _daily_reads_html(content)
    ingredients_html = "\n".join(
        f"<li style=\"margin:0 0 6px;color:#314251\">{html.escape(ingredient)}</li>"
        for ingredient in content.meal.ingredients
    )
    steps_html = "\n".join(
        f"<li style=\"margin:0 0 8px;color:#314251\">{html.escape(step)}</li>"
        for step in content.meal.steps
    )
    meal_image_html = _meal_image_html(content)

    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f5f1ec;font-family:Segoe UI,Arial,sans-serif;color:#24313b">
    <div style="display:none;max-height:0;overflow:hidden;color:#f5f1ec">
      A private couple brief for {brief_date:%A, %d %B %Y}: calendar nudges, dinner, and one marriage spark.
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f1ec">
      <tr>
        <td align="center" style="padding:30px 12px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:760px;background:#fffdf9;border-radius:18px;overflow:hidden;box-shadow:0 18px 45px rgba(48,43,38,.14)">
            <tr>
              <td style="padding:30px 34px;background:#213f46;color:#ffffff">
                <div style="display:inline-block;background:#f3d9b1;color:#213f46;border-radius:999px;padding:7px 11px;font-size:12px;letter-spacing:.7px;text-transform:uppercase;font-weight:800">Private morning note</div>
                <h1 style="font-size:32px;line-height:1.1;margin:14px 0 8px;font-weight:850">Team ShiNola - Our Daily Brief</h1>
                <p style="font-size:15px;line-height:1.5;margin:0;color:#deedf0">
                  A small plan for the home, the evening, and the two people holding it together.
                </p>
                <div style="margin-top:15px;color:#bfe1e7;font-size:14px;font-weight:700">{brief_date:%A, %d %B %Y}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 34px 34px">
                <p style="font-size:18px;line-height:1.5;margin:0 0 22px;color:#314251">
                  Good morning, <strong>{html.escape(content.names)}</strong>.
                </p>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #d7e7dc;border-radius:16px;background:#f4fbf6">
                  {meal_image_html}
                  <tr>
                    <td style="padding:22px">
                      <div style="font-size:12px;color:#2f7358;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Meal idea</div>
                      <h2 style="font-size:23px;line-height:1.2;margin:7px 0 10px;color:#203830">{html.escape(content.meal.title)}</h2>
                      <p style="font-size:15px;line-height:1.55;margin:0;color:#314251">{html.escape(content.meal.description)}</p>
                      <div style="margin-top:16px;font-size:12px;color:#2f7358;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Ingredients</div>
                      <ul style="padding-left:18px;margin:8px 0 0;font-size:14px;line-height:1.5">
                        {ingredients_html}
                      </ul>
                      <div style="margin-top:16px;font-size:12px;color:#2f7358;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Short recipe</div>
                      <ol style="padding-left:18px;margin:8px 0 0;font-size:14px;line-height:1.5">
                        {steps_html}
                      </ol>
                      <p style="font-size:14px;line-height:1.5;margin:16px 0 0;color:#567066"><strong>Prep note:</strong> {html.escape(content.meal.prep_note)}</p>
                      <p style="font-size:11px;line-height:1.4;margin:10px 0 0;color:#7b8a83">
                        <a href="{html.escape(content.meal.image_credit_url, quote=True)}" style="color:#567066;text-decoration:none">{html.escape(content.meal.image_credit)}</a>
                      </p>
                    </td>
                  </tr>
                </table>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:22px;border:1px solid #e7d9c6;border-radius:16px;background:#fff8ee">
                  <tr>
                    <td style="padding:22px 24px">
                      <div style="font-size:12px;color:#9b5a42;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Calendar snapshot</div>
                      {calendar_events_html}
                      {calendar_note_html}
                      <div style="margin-top:15px;font-size:12px;color:#9b5a42;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Nudges</div>
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:8px">
                        {reminders_html}
                      </table>
                    </td>
                  </tr>
                </table>

                {daily_reads_html}

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:22px;border:1px solid #ead4d0;border-radius:16px;background:#fff6f4">
                  <tr>
                    <td style="padding:22px">
                      <div style="font-size:12px;color:#9b4d4a;font-weight:850;text-transform:uppercase;letter-spacing:.8px">This week's spark</div>
                      <h2 style="font-size:23px;line-height:1.2;margin:7px 0 10px;color:#3f2c2b">{html.escape(content.spark.title)}</h2>
                      <p style="font-size:15px;line-height:1.55;margin:0;color:#314251">{html.escape(content.spark.motivation)}</p>
                    </td>
                  </tr>
                </table>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:22px;border:1px solid #d3e1e5;border-radius:16px;background:#f2fafb">
                  <tr>
                    <td style="padding:21px 24px">
                      <div style="font-size:12px;color:#326c78;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Try this together</div>
                      <p style="font-size:16px;line-height:1.55;margin:7px 0 0;color:#314251">{html.escape(content.spark.fun_idea)}</p>
                      <p style="font-size:15px;line-height:1.55;margin:14px 0 0;color:#526879"><strong>Ask:</strong> {html.escape(content.spark.conversation_starter)}</p>
                    </td>
                  </tr>
                </table>

                <p style="font-size:16px;line-height:1.55;margin:26px 0 0;color:#314251;text-align:center">
                  {html.escape(content.closing)}
                </p>
                <p style="margin:24px 0 0;color:#8b989f;font-size:12px;text-align:center">
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


def _daily_read_text_lines(content: CoupleBriefContent) -> list[str]:
    lines: list[str] = []
    if content.history_moment:
        lines.extend(
            [
                "What happened in history today:",
                content.history_moment.title,
                content.history_moment.paragraph,
            ]
        )
        if content.history_moment.source and content.history_moment.source_url:
            lines.append(
                "Source: "
                f"{content.history_moment.source} "
                f"({content.history_moment.source_url})"
            )
        lines.append("")

    if content.fun_fact:
        lines.extend(
            [
                "Fun fact of the day:",
                content.fun_fact.title,
                content.fun_fact.body,
                "",
            ]
        )
    return lines


def _daily_reads_html(content: CoupleBriefContent) -> str:
    cards = [
        _history_moment_html(content.history_moment),
        _fun_fact_html(content.fun_fact),
    ]
    cards_html = "\n".join(card for card in cards if card)
    if not cards_html:
        return ""

    return f"""
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:22px;border:1px solid #d4dde7;border-radius:16px;background:#f6f9fc">
                  <tr>
                    <td style="padding:22px 24px">
                      {cards_html}
                    </td>
                  </tr>
                </table>
    """


def _history_moment_html(moment: HistoryMoment | None) -> str:
    if moment is None:
        return ""

    source_html = ""
    if moment.source and moment.source_url:
        source_html = f"""
                      <p style="font-size:11px;line-height:1.4;margin:10px 0 0;color:#738290">
                        Source: <a href="{html.escape(moment.source_url, quote=True)}" style="color:#516b7a;text-decoration:none">{html.escape(moment.source)}</a>
                      </p>
        """

    return f"""
                      <div>
                        <div style="font-size:12px;color:#4c6980;font-weight:850;text-transform:uppercase;letter-spacing:.8px">What happened in history today</div>
                        <h2 style="font-size:22px;line-height:1.2;margin:7px 0 10px;color:#223747">{html.escape(moment.title)}</h2>
                        <p style="font-size:15px;line-height:1.58;margin:0;color:#314251">{html.escape(moment.paragraph)}</p>
                        {source_html}
                      </div>
    """


def _fun_fact_html(fun_fact: DailyFunFact | None) -> str:
    if fun_fact is None:
        return ""

    return f"""
                      <div style="margin-top:20px;padding-top:18px;border-top:1px solid #dbe5ec">
                        <div style="font-size:12px;color:#4c6980;font-weight:850;text-transform:uppercase;letter-spacing:.8px">Fun fact of the day</div>
                        <h2 style="font-size:22px;line-height:1.2;margin:7px 0 10px;color:#223747">{html.escape(fun_fact.title)}</h2>
                        <p style="font-size:15px;line-height:1.58;margin:0;color:#314251">{html.escape(fun_fact.body)}</p>
                      </div>
    """


def _calendar_text_lines(
    brief_date: datetime,
    content: CoupleBriefContent,
) -> list[str]:
    lines = ["Calendar snapshot:"]
    if content.calendar_events:
        for event in content.calendar_events:
            lines.append(f"- {_format_calendar_event_text(brief_date, event)}")
    else:
        lines.append("- No Google Calendar events loaded yet.")

    if content.calendar_note:
        lines.append(f"- {content.calendar_note}")
    lines.append("")
    return lines


def _calendar_events_html(
    brief_date: datetime,
    content: CoupleBriefContent,
) -> str:
    if not content.calendar_events:
        return """
                      <p style="font-size:15px;line-height:1.5;margin:8px 0 0;color:#6f6258">
                        No Google Calendar events loaded yet.
                      </p>
        """

    rows = "\n".join(
        f"""
                          <tr>
                            <td style="padding:9px 0;border-bottom:1px solid #ecdcc8;vertical-align:top;width:92px">
                              <div style="font-size:12px;line-height:1.35;color:#9b5a42;font-weight:850">{html.escape(_event_day_label(brief_date, event))}</div>
                              <div style="font-size:13px;line-height:1.35;color:#314251">{html.escape(_event_time_label(event))}</div>
                            </td>
                            <td style="padding:9px 0 9px 12px;border-bottom:1px solid #ecdcc8;vertical-align:top">
                              <div style="font-size:15px;line-height:1.35;color:#314251;font-weight:750">{html.escape(event.title)}</div>
                              <div style="font-size:12px;line-height:1.4;color:#76695f">{html.escape(_event_meta(event))}</div>
                            </td>
                          </tr>
        """
        for event in content.calendar_events
    )
    return f"""
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:9px">
                        {rows}
                      </table>
    """


def _calendar_note_html(content: CoupleBriefContent) -> str:
    if not content.calendar_note:
        return ""
    return f"""
                      <p style="font-size:13px;line-height:1.45;margin:12px 0 0;color:#9b5a42">
                        {html.escape(content.calendar_note)}
                      </p>
    """


def _meal_image_html(content: CoupleBriefContent) -> str:
    if not content.meal.image_url:
        return ""

    image_url = html.escape(content.meal.image_url, quote=True)
    image_alt = html.escape(content.meal.image_alt, quote=True)
    return f"""
                  <tr>
                    <td style="padding:0">
                      <img src="{image_url}" width="760" alt="{image_alt}" style="display:block;width:100%;max-width:760px;height:auto;border:0">
                    </td>
                  </tr>
    """


def _format_calendar_event_text(brief_date: datetime, event: CalendarEvent) -> str:
    parts = [
        _event_day_label(brief_date, event),
        _event_time_label(event),
        event.title,
        f"({event.calendar_name})",
    ]
    if event.location:
        parts.append(f"at {event.location}")
    return " - ".join(part for part in parts if part)


def _event_day_label(brief_date: datetime, event: CalendarEvent) -> str:
    event_date = event.start.date()
    today = brief_date.date()
    if event_date == today:
        return "Today"
    tomorrow = today.toordinal() + 1
    if event_date.toordinal() == tomorrow:
        return "Tomorrow"
    return event.start.strftime("%a %d %b")


def _event_time_label(event: CalendarEvent) -> str:
    if event.all_day:
        return "All day"
    return event.start.strftime("%H:%M")


def _event_meta(event: CalendarEvent) -> str:
    pieces = [event.calendar_name]
    if event.location:
        pieces.append(event.location)
    return " - ".join(piece for piece in pieces if piece)
