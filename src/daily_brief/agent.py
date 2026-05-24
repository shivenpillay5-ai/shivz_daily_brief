from __future__ import annotations

import html
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from daily_brief.config import AppConfig
from daily_brief.models import (
    CoupleBriefContent,
    DevotionalContent,
    GrocerySpecialsContent,
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
from daily_brief.tools.email import EmailAttachment, InlineImage, send_email
from daily_brief.tools.email_images import fetch_inline_image
from daily_brief.tools.google_calendar import authorize_google_calendar
from daily_brief.tools.grocery_rendering import (
    render_grocery_html,
    render_grocery_text,
    write_grocery_store_pdfs,
)
from daily_brief.tools.grocery_specials import build_grocery_specials
from daily_brief.tools.market import fetch_market_pulse
from daily_brief.tools.news import fetch_feed_items
from daily_brief.tools.ranking import rank_items
from daily_brief.tools.rendering import (
    render_html,
    render_text,
    render_whatsapp_template_parameters,
    render_whatsapp_text,
)
from daily_brief.tools.story_enrichment import enrich_story_summaries
from daily_brief.tools.summary import write_morning_summary
from daily_brief.tools.weather import fetch_weather
from daily_brief.tools.whatsapp import send_whatsapp_message, send_whatsapp_template


@dataclass(frozen=True)
class Brief:
    subject: str
    text_body: str
    html_body: str
    whatsapp_body: str
    whatsapp_template_parameters: list[str]
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


@dataclass(frozen=True)
class GrocerySpecialsBrief:
    subject: str
    text_body: str
    html_body: str
    content: GrocerySpecialsContent
    document_paths: list[str]


COUPLE_MEAL_IMAGE_CID = "couple-meal-image@daily-brief-agent"


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

        print("Fetching South Africa news feeds...")
        south_africa_items, south_africa_warnings = fetch_feed_items(
            self.config.south_africa_feeds,
            category="south_africa",
        )

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

        print("Ranking South Africa stories...")
        south_africa_ranked = rank_items(
            south_africa_items,
            category_name="South Africa news",
            top_n=self.config.top_n,
            config=self.config,
            use_openai=use_openai,
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

        print("Enriching story summaries...")
        south_africa_ranked = enrich_story_summaries(south_africa_ranked)
        world_ranked = enrich_story_summaries(world_ranked)
        ai_tech_ranked = enrich_story_summaries(ai_tech_ranked)

        print("Writing morning summary...")
        morning_summary = write_morning_summary(
            brief_date=brief_date,
            weather_reports=weather_reports,
            market_pulse=market_pulse,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
            config=self.config,
            use_openai=use_openai,
            south_africa_items=south_africa_ranked,
        )

        warnings = south_africa_warnings + world_warnings + ai_tech_warnings
        if market_pulse:
            warnings += market_pulse.warnings
        text_body = render_text(
            brief_date=brief_date,
            weather_reports=weather_reports,
            morning_summary=morning_summary,
            market_pulse=market_pulse,
            south_africa_items=south_africa_ranked,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
            warnings=warnings,
        )
        html_body = render_html(
            brief_date=brief_date,
            weather_reports=weather_reports,
            morning_summary=morning_summary,
            market_pulse=market_pulse,
            south_africa_items=south_africa_ranked,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
            warnings=warnings,
        )
        whatsapp_body = render_whatsapp_text(
            brief_date=brief_date,
            weather_reports=weather_reports,
            morning_summary=morning_summary,
            market_pulse=market_pulse,
            south_africa_items=south_africa_ranked,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
        )
        whatsapp_template_parameters = render_whatsapp_template_parameters(
            brief_date=brief_date,
            weather_reports=weather_reports,
            world_items=world_ranked,
            ai_tech_items=ai_tech_ranked,
        )
        subject = f"{self.config.email.subject_prefix} - {brief_date:%Y-%m-%d}"

        return Brief(
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            whatsapp_body=whatsapp_body,
            whatsapp_template_parameters=whatsapp_template_parameters,
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

    def build_grocery_specials(self, brief_date: datetime) -> GrocerySpecialsBrief:
        print("Fetching grocery specials...")
        content = build_grocery_specials(
            brief_date=brief_date,
            config=self.config.grocery_specials,
        )
        document_paths = write_grocery_store_pdfs(
            brief_date=brief_date,
            content=content,
            output_dir=self.config.grocery_specials.output_dir,
        )
        subject = (
            f"{self.config.grocery_specials.subject_prefix} - "
            f"{brief_date:%Y-%m-%d}"
        )
        return GrocerySpecialsBrief(
            subject=subject,
            text_body=render_grocery_text(brief_date, content),
            html_body=render_grocery_html(brief_date, content),
            content=content,
            document_paths=[str(path) for path in document_paths],
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
        devotional_email = replace(
            self.config.email,
            email_to=self.config.email.devotional_email_to or self.config.email.email_to,
        )
        send_email(
            devotional_email,
            subject=brief.subject,
            text_body=brief.text_body,
            html_body=brief.html_body,
        )

    def send_couple(self, brief: CoupleBrief) -> None:
        if not self.config.couple.email_to:
            raise ValueError("COUPLE_EMAIL_TO must be set before sending the couple brief.")

        couple_email = replace(self.config.email, email_to=self.config.couple.email_to)
        html_body, inline_images = _prepare_couple_email_images(brief)
        send_email(
            couple_email,
            subject=brief.subject,
            text_body=brief.text_body,
            html_body=html_body,
            inline_images=inline_images,
        )

    def send_grocery_specials(self, brief: GrocerySpecialsBrief) -> None:
        email_to = (
            self.config.grocery_specials.email_to
            or self.config.couple.email_to
            or self.config.email.email_to
        )
        if not email_to:
            raise ValueError(
                "Set GROCERY_SPECIALS_EMAIL, COUPLE_EMAIL_TO, or EMAIL_TO before sending."
            )

        grocery_email = replace(self.config.email, email_to=email_to)
        attachments = [
            EmailAttachment(
                data=_read_document(path),
                maintype="application",
                subtype="pdf",
                filename=path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1],
            )
            for path in brief.document_paths
        ]
        send_email(
            grocery_email,
            subject=brief.subject,
            text_body=brief.text_body,
            html_body=brief.html_body,
            attachments=attachments,
        )

    def send_devotional_whatsapp(self, brief: DevotionalBrief) -> None:
        send_whatsapp_message(self.config.whatsapp, brief.whatsapp_body)

    def send_whatsapp_template(self, brief: Brief) -> None:
        send_whatsapp_template(
            self.config.whatsapp,
            body_parameters=brief.whatsapp_template_parameters,
        )

    def authorize_google_calendar(self) -> None:
        authorize_google_calendar(self.config.google_calendar)

    def send_failure_alert(
        self,
        brief_date: datetime,
        log_text: str,
        run_url: str = "",
        alert_name: str = "Shivz Daily Brief",
    ) -> None:
        alert_email = replace(
            self.config.email,
            email_to=self.config.email.alert_email_to or self.config.email.email_to,
        )
        send_failure_alert_email(
            alert_email,
            brief_date=brief_date,
            log_text=log_text,
            run_url=run_url,
            alert_name=alert_name,
        )


def _prepare_couple_email_images(brief: CoupleBrief) -> tuple[str, list[InlineImage]]:
    image_url = brief.content.meal.image_url
    if not image_url:
        return brief.html_body, []

    try:
        inline_image = fetch_inline_image(
            image_url,
            content_id=COUPLE_MEAL_IMAGE_CID,
            filename_stem=brief.content.meal.title,
        )
    except Exception as exc:
        print(f"Could not embed couple meal image; using remote URL instead: {exc}")
        return brief.html_body, []

    escaped_image_url = html.escape(image_url, quote=True)
    html_body = brief.html_body.replace(
        escaped_image_url,
        f"cid:{COUPLE_MEAL_IMAGE_CID}",
        1,
    )
    return html_body, [inline_image]


def _read_document(path: str) -> bytes:
    return Path(path).read_bytes()
