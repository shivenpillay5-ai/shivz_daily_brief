from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from daily_brief.agent import DailyBriefAgent
from daily_brief.config import load_config


def main() -> None:
    _configure_console_encoding()

    parser = argparse.ArgumentParser(description="Build and send a daily email brief.")
    parser.add_argument("--env-file", type=Path, help="Optional path to a .env file.")
    parser.add_argument("--send", action="store_true", help="Send email instead of previewing.")
    parser.add_argument(
        "--send-whatsapp",
        action="store_true",
        help="Send the WhatsApp text brief to configured WhatsApp recipients.",
    )
    parser.add_argument(
        "--send-whatsapp-template",
        action="store_true",
        help="Send Meta's hello_world WhatsApp template to test delivery.",
    )
    parser.add_argument(
        "--save-html",
        type=Path,
        help="Save the rendered HTML email to a file for browser preview.",
    )
    parser.add_argument(
        "--no-openai",
        action="store_true",
        help="Use fallback ranking even when OPENAI_API_KEY is set.",
    )
    args = parser.parse_args()

    config = load_config(args.env_file)
    brief_date = _now(config.location.timezone)
    agent = DailyBriefAgent(config)

    if args.send_whatsapp_template:
        print("Sending WhatsApp template...")
        agent.send_whatsapp_template()
        print("WhatsApp template sent.")
        return

    use_openai = not args.no_openai
    brief = agent.build(brief_date=brief_date, use_openai=use_openai)

    if args.save_html:
        args.save_html.write_text(brief.html_body, encoding="utf-8")
        print(f"Saved HTML preview to {args.save_html}")

    if args.send:
        print("Sending email...")
        agent.send(brief)
        print("Email sent.")

    if args.send_whatsapp:
        print("Sending WhatsApp...")
        agent.send_whatsapp(brief)
        print("WhatsApp sent.")

    if args.send or args.send_whatsapp:
        return

    print("")
    print("=" * 72)
    print(f"Preview only. Subject: {brief.subject}")
    print("=" * 72)
    print(brief.text_body)
    print("")
    print("=" * 72)
    print("WhatsApp preview")
    print("=" * 72)
    print(brief.whatsapp_body)
    print("")
    print("Run with --send when your .env email settings are ready.")


def _now(timezone_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        print(
            f"Timezone '{timezone_name}' was not found. Falling back to local time.",
            file=sys.stderr,
        )
        return datetime.now()


def _configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    main()
