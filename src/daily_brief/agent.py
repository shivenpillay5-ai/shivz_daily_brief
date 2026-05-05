from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from daily_brief.config import AppConfig
from daily_brief.models import (
    CoupleBriefContent,
    DevotionalContent,
    MarketPulse,
    MorningSummary,
)
from daily_brief.tools.alerts import send_failure_alert as send_failure_alert_email
from daily_brief.tools.couple import build_couple_brief
from daily_brief.tools.couple_rendering import render_couple_html, render_couple_text
from daily_brief.tools.devotional import build_daily_devotional
from daily_brief.tools.devotional_rendering import (
    render_devotional_html,
    render_devotional_text,
    render_devotional_whatsapp_text,
)
from daily_brief.tools.email import send_email
from daily_brief.tools.google_calendar import authorize_google_calendar
from daily_brief.tools.market import fetch_market_pulse
from daily_brief.tools.news import fetch_feed_items
from daily_brief.tools.ranking import rank_items
from daily_brief.tools.rendering import render_html, render_text, render_whatsapp_text
from daily_brief.tools.summary import write_morning_summary
from daily_brief.tools.weather import fetch_weather
from daily_brief.tools.whatsapp import send_whatsapp_message, send_whatsapp_template


@dataclass(frozen=True)
class Brief:
    subject: str
    text_body: str
    html_body: str
    whatsapp_body: str
    morning_summary: MorningSummary
    warnings: list[str]


@dataclass(frozen=True)
class DevotionalBrief:
    subject: str
    text_body: str
    html_body: str
    whatsapp_body: str
    devotional: DevotionalContent


@dataclass(frozen=True)
class CoupleBrief:
    subject: str
    text_body: str
    html_body: str
    content: CoupleBriefContent


class DailyBriefAgent:
    """Coordinates the brief-building skills in one daily workflow."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def build(self, brief_date: datetime, use_openai: bool = True) -> Brief:
        print("Fetching weather...")
        weather_reports = [
            fetch_weather(location) for location in self.config.weather_locations
        ]

        market_pulse: MarketPulse | None = None
        if self.config.market_pulse_enabled:
            print("Fetching market pulse...")
            market_pulse = fetch_market_pulse()

        print("Fetching world news feeds...")
        world_items, world_warnings = fetch_feed_items(
            self.config.news_feeds,
            category="world",
        )

        print("Fetching AI and tech feeds...")
        ai_tech_items, ai_tech_warnings = fetch_feed_items(
            self.config.ai_tech_feeds,
            category="ai_tech",
        )

        print("Ranking world stories...")
        world_ranked = rank_items(
            world_items,
            category_name="World news",
            top_n=self.config.top_n,
            config=self.config,
            use_openai=use_openai,
        )

        print("Ranking AI and tech stories...")
        ai_tech_ranked = rank_items(
            ai_tech_items,
            category_name="AI and tech news",
            top_n=self.config.top_n,
            config=self.config,
            use_openai=use_openai,
        )

        print("Writing morning summary...")
        morning_summary = write_morning_summary(
            brief_date=brief_date,
            weather_reports=weather_reports,
            market_pulse=market_pulse,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
            config=self.config,
            use_openai=use_openai,
        )

        warnings = world_warnings + ai_tech_warnings
        if market_pulse:
            warnings += market_pulse.warnings
        text_body = render_text(
            brief_date=brief_date,
            weather_reports=weather_reports,
            morning_summary=morning_summary,
            market_pulse=market_pulse,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
            warnings=warnings,
        )
        html_body = render_html(
            brief_date=brief_date,
            weather_reports=weather_reports,
            morning_summary=morning_summary,
            market_pulse=market_pulse,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
            warnings=warnings,
        )
        whatsapp_body = render_whatsapp_text(
            brief_date=brief_date,
            weather_reports=weather_reports,
            morning_summary=morning_summary,
            market_pulse=market_pulse,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
        )
        subject = f"{self.config.email.subject_prefix} - {brief_date:%Y-%m-%d}"

        return Brief(
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            whatsapp_body=whatsapp_body,
            morning_summary=morning_summary,
            warnings=warnings,
        )

    def build_devotional(
        self,
        brief_date: datetime,
        use_openai: bool = True,
    ) -> DevotionalBrief:
        print("Building daily devotional...")
        devotional = build_daily_devotional(
            brief_date=brief_date,
            config=self.config,
            use_openai=use_openai,
        )
        subject = f"{self.config.devotional_subject_prefix} - {brief_date:%Y-%m-%d}"
        return DevotionalBrief(
            subject=subject,
            text_body=render_devotional_text(brief_date, devotional),
            html_body=render_devotional_html(brief_date, devotional),
            whatsapp_body=render_devotional_whatsapp_text(brief_date, devotional),
            devotional=devotional,
        )

    def build_couple(self, brief_date: datetime) -> CoupleBrief:
        print("Building couple brief...")
        content = build_couple_brief(brief_date=brief_date, config=self.config)
        subject = f"{self.config.couple.subject_prefix} - {brief_date:%Y-%m-%d}"
        return CoupleBrief(
            subject=subject,
            text_body=render_couple_text(brief_date, content),
            html_body=render_couple_html(brief_date, content),
            content=content,
        )

    def send(self, brief: Brief) -> None:
        send_email(
            self.config.email,
            subject=brief.subject,
            text_body=brief.text_body,
            html_body=brief.html_body,
        )

    def send_whatsapp(self, brief: Brief) -> None:
        send_whatsapp_message(self.config.whatsapp, brief.whatsapp_body)

    def send_devotional(self, brief: DevotionalBrief) -> None:
        send_email(
            self.config.email,
            subject=brief.subject,
            text_body=brief.text_body,
            html_body=brief.html_body,
        )

    def send_couple(self, brief: CoupleBrief) -> None:
        if not self.config.couple.email_to:
            raise ValueError("COUPLE_EMAIL_TO must be set before sending the couple brief.")

        couple_email = replace(self.config.email, email_to=self.config.couple.email_to)
        send_email(
            couple_email,
            subject=brief.subject,
            text_body=brief.text_body,
            html_body=brief.html_body,
        )

    def send_devotional_whatsapp(self, brief: DevotionalBrief) -> None:
        send_whatsapp_message(self.config.whatsapp, brief.whatsapp_body)

    def send_whatsapp_template(self) -> None:
        send_whatsapp_template(self.config.whatsapp)

    def authorize_google_calendar(self) -> None:
        authorize_google_calendar(self.config.google_calendar)

    def send_failure_alert(
        self,
        brief_date: datetime,
        log_text: str,
        run_url: str = "",
        alert_name: str = "Shivz Daily Brief",
    ) -> None:
        send_failure_alert_email(
            self.config.email,
            brief_date=brief_date,
            log_text=log_text,
            run_url=run_url,
            alert_name=alert_name,
        )
