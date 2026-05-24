from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_NEWS_FEEDS = (
    "BBC World|https://feeds.bbci.co.uk/news/world/rss.xml;"
    "The Guardian World|https://www.theguardian.com/world/rss;"
    "NPR World|https://feeds.npr.org/1004/rss.xml;"
    "UN News|https://news.un.org/feed/subscribe/en/news/all/rss.xml"
)

DEFAULT_AI_TECH_FEEDS = (
    "OpenAI News|https://openai.com/news/rss.xml;"
    "Google AI Blog|https://blog.google/technology/ai/rss/;"
    "TechCrunch AI|https://techcrunch.com/category/artificial-intelligence/feed/;"
    "VentureBeat AI|https://venturebeat.com/category/ai/feed/;"
    "MIT Technology Review AI|https://www.technologyreview.com/topic/artificial-intelligence/feed/"
)

DEFAULT_SOUTH_AFRICA_FEEDS = (
    "BusinessTech|https://businesstech.co.za/news/feed/;"
    "News24 South Africa|https://feeds.news24.com/articles/news24/SouthAfrica/rss"
)

DEFAULT_WEATHER_LOCATIONS = (
    "Midrand|-25.9992|28.1263|Africa/Johannesburg|hourly;"
    "Johannesburg|-26.2041|28.0473|Africa/Johannesburg;"
    "Cape Town|-33.9249|18.4241|Africa/Johannesburg;"
    "Durban|-29.8587|31.0218|Africa/Johannesburg"
)

DEFAULT_GROCERY_SOURCES = (
    "Woolworths|Woolworths Food Promotions|"
    "https://www.woolworths.co.za/cat/Promotions/Save/Food/_/N-1z13sk5;"
    "Checkers|My Catalogue Product Table|https://my-catalogue.co.za/checkers-specials;"
    "Pick n Pay|My Catalogue Product Table|https://my-catalogue.co.za/pick-n-pay-specials"
)


@dataclass(frozen=True)
class FeedConfig:
    name: str
    url: str


@dataclass(frozen=True)
class LocationConfig:
    name: str
    latitude: float
    longitude: float
    timezone: str
    hourly: bool = False


@dataclass(frozen=True)
class EmailConfig:
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: list[str]
    subject_prefix: str
    devotional_email_to: list[str] = field(default_factory=list)
    alert_email_to: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WhatsAppConfig:
    enabled: bool
    phone_number_id: str
    business_account_id: str
    access_token: str
    recipients: list[str]
    api_version: str
    template_name: str = "shivz_daily_brief_v1"
    template_language: str = "en"


@dataclass(frozen=True)
class CoupleBriefConfig:
    email_to: list[str]
    subject_prefix: str
    names: str
    reminders: list[str]
    daily_reads_enabled: bool = True


@dataclass(frozen=True)
class GrocerySourceConfig:
    store_name: str
    source_name: str
    url: str


@dataclass(frozen=True)
class GrocerySpecialsConfig:
    email_to: list[str]
    subject_prefix: str
    area: str
    sources: list[GrocerySourceConfig]
    max_items_per_store: int
    output_dir: Path


def _default_grocery_specials_config() -> GrocerySpecialsConfig:
    return GrocerySpecialsConfig(
        email_to=[],
        subject_prefix="Midrand Grocery Specials",
        area="Midrand, Gauteng",
        sources=_parse_grocery_sources(DEFAULT_GROCERY_SOURCES),
        max_items_per_store=120,
        output_dir=Path("grocery-specials"),
    )


@dataclass(frozen=True)
class CalendarSourceConfig:
    calendar_id: str
    label: str


@dataclass(frozen=True)
class GoogleCalendarConfig:
    enabled: bool
    credentials_file: Path
    token_file: Path
    calendars: list[CalendarSourceConfig]
    lookahead_days: int
    max_events_per_calendar: int


@dataclass(frozen=True)
class AppConfig:
    location: LocationConfig
    email: EmailConfig
    whatsapp: WhatsAppConfig
    couple: CoupleBriefConfig
    google_calendar: GoogleCalendarConfig
    news_feeds: list[FeedConfig]
    ai_tech_feeds: list[FeedConfig]
    top_n: int
    openai_api_key: str
    openai_model: str
    market_pulse_enabled: bool
    south_africa_feeds: list[FeedConfig] = field(default_factory=list)
    weather_locations: list[LocationConfig] = field(default_factory=list)
    devotional_subject_prefix: str = "Daily Motivation and Bible Verse"
    grocery_specials: GrocerySpecialsConfig = field(
        default_factory=_default_grocery_specials_config
    )


def load_env_file(path: Path, override: bool = False) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)


def load_config(env_file: Path | None = None) -> AppConfig:
    project_root = Path(__file__).resolve().parents[2]
    load_env_file(project_root / ".env")
    if env_file is not None:
        load_env_file(env_file, override=True)

    primary_location = LocationConfig(
        name=_get("LOCATION_NAME", "Johannesburg"),
        latitude=float(_get("LATITUDE", "-26.2041")),
        longitude=float(_get("LONGITUDE", "28.0473")),
        timezone=_get("TIMEZONE", "Africa/Johannesburg"),
    )

    return AppConfig(
        location=primary_location,
        email=EmailConfig(
            smtp_host=_get("SMTP_HOST", ""),
            smtp_port=int(_get("SMTP_PORT", "587")),
            smtp_use_tls=_get_bool("SMTP_USE_TLS", True),
            smtp_username=_get("SMTP_USERNAME", ""),
            smtp_password=_get_secret("SMTP_PASSWORD", ""),
            email_from=_get("EMAIL_FROM", ""),
            email_to=_split_csv(_get("EMAIL_TO", "")),
            subject_prefix=_get("EMAIL_SUBJECT_PREFIX", "Shivz Daily Brief"),
            devotional_email_to=_split_csv(_get("DEVOTIONAL_EMAIL_TO", "")),
            alert_email_to=_split_csv(_get("ALERT_EMAIL_TO", "")),
        ),
        whatsapp=WhatsAppConfig(
            enabled=_get_bool("WHATSAPP_ENABLED", False),
            phone_number_id=_get("WHATSAPP_PHONE_NUMBER_ID", ""),
            business_account_id=_get("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
            access_token=_get_secret("WHATSAPP_ACCESS_TOKEN", ""),
            recipients=_split_phone_numbers(_get("WHATSAPP_TO", "")),
            api_version=_get("WHATSAPP_API_VERSION", "v24.0"),
            template_name=_get("WHATSAPP_TEMPLATE_NAME", "shivz_daily_brief_v1"),
            template_language=_get("WHATSAPP_TEMPLATE_LANGUAGE", "en"),
        ),
        couple=CoupleBriefConfig(
            email_to=_split_csv(_get("COUPLE_EMAIL_TO", "")),
            subject_prefix=_get(
                "COUPLE_SUBJECT_PREFIX",
                "Team ShiNola - Our Daily Brief",
            ),
            names=_get("COUPLE_NAMES", "you two"),
            reminders=_split_semicolon(
                _get(
                    "COUPLE_REMINDERS",
                    (
                        "Check the shared Gmail calendars for anything that needs a"
                        " family handoff.;Pick one small admin item to close before it"
                        " becomes background noise.;Keep dinner simple enough that the"
                        " evening still has breathing room."
                    ),
                )
            ),
            daily_reads_enabled=_get_bool("COUPLE_DAILY_READS_ENABLED", True),
        ),
        grocery_specials=GrocerySpecialsConfig(
            email_to=_split_csv(
                _get_any(
                    ("GROCERY_SPECIALS_EMAIL", "GROCERY_SPECIALS_EMAIL_TO"),
                    "",
                )
            ),
            subject_prefix=_get(
                "GROCERY_SPECIALS_SUBJECT_PREFIX",
                "Midrand Grocery Specials",
            ),
            area=_get("GROCERY_SPECIALS_AREA", "Midrand, Gauteng"),
            sources=_parse_grocery_sources(
                _get("GROCERY_SPECIALS_SOURCES", DEFAULT_GROCERY_SOURCES)
            ),
            max_items_per_store=max(
                1,
                int(_get("GROCERY_SPECIALS_MAX_ITEMS_PER_STORE", "120")),
            ),
            output_dir=_project_path(
                project_root,
                _get("GROCERY_SPECIALS_OUTPUT_DIR", "grocery-specials"),
            ),
        ),
        google_calendar=GoogleCalendarConfig(
            enabled=_get_bool("GOOGLE_CALENDAR_ENABLED", False),
            credentials_file=_project_path(
                project_root,
                _get("GOOGLE_CALENDAR_CREDENTIALS_FILE", "credentials.json"),
            ),
            token_file=_project_path(
                project_root,
                _get("GOOGLE_CALENDAR_TOKEN_FILE", "token.json"),
            ),
            calendars=_parse_calendar_sources(
                _get("GOOGLE_CALENDAR_IDS", "primary|Primary")
            ),
            lookahead_days=max(1, int(_get("GOOGLE_CALENDAR_LOOKAHEAD_DAYS", "3"))),
            max_events_per_calendar=max(
                1,
                int(_get("GOOGLE_CALENDAR_MAX_EVENTS_PER_CALENDAR", "12")),
            ),
        ),
        news_feeds=_parse_feeds(_get("NEWS_FEEDS", DEFAULT_NEWS_FEEDS)),
        ai_tech_feeds=_parse_feeds(_get("AI_TECH_FEEDS", DEFAULT_AI_TECH_FEEDS)),
        south_africa_feeds=_parse_feeds(
            _get("SOUTH_AFRICA_NEWS_FEEDS", DEFAULT_SOUTH_AFRICA_FEEDS)
        ),
        top_n=int(_get("TOP_N", "5")),
        openai_api_key=_get("OPENAI_API_KEY", ""),
        openai_model=_get("OPENAI_MODEL", "gpt-5"),
        market_pulse_enabled=_get_bool("MARKET_PULSE_ENABLED", True),
        weather_locations=_parse_locations(
            _get("WEATHER_LOCATIONS", DEFAULT_WEATHER_LOCATIONS)
        )
        or [primary_location],
        devotional_subject_prefix=_get(
            "DEVOTIONAL_SUBJECT_PREFIX",
            "Daily Motivation and Bible Verse",
        ),
    )


def _get(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _get_any(names: tuple[str, ...], default: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip() != "":
            return value.strip()
    return default


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_secret(name: str, default: str) -> str:
    value = _get(name, default)
    return re.sub(r"\s+", "", value)


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _split_phone_numbers(value: str) -> list[str]:
    numbers: list[str] = []
    for part in _split_csv(value):
        normalized = re.sub(r"\D+", "", part)
        if normalized:
            numbers.append(normalized)
    return numbers


def _project_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root / path


def _parse_calendar_sources(value: str) -> list[CalendarSourceConfig]:
    calendars: list[CalendarSourceConfig] = []
    for raw_part in value.split(";"):
        part = raw_part.strip()
        if not part:
            continue

        if "|" in part:
            calendar_id, label = part.split("|", 1)
        else:
            calendar_id, label = part, part

        calendar_id = calendar_id.strip()
        label = label.strip() or calendar_id
        if calendar_id:
            calendars.append(CalendarSourceConfig(calendar_id=calendar_id, label=label))

    return calendars or [CalendarSourceConfig(calendar_id="primary", label="Primary")]


def _parse_feeds(value: str) -> list[FeedConfig]:
    feeds: list[FeedConfig] = []
    for raw_part in value.split(";"):
        part = raw_part.strip()
        if not part:
            continue

        if "|" not in part:
            raise ValueError(f"Feed entry must be Name|URL: {part}")

        name, url = part.split("|", 1)
        feeds.append(FeedConfig(name=name.strip(), url=url.strip()))

    return feeds


def _parse_grocery_sources(value: str) -> list[GrocerySourceConfig]:
    sources: list[GrocerySourceConfig] = []
    for raw_part in value.split(";"):
        part = raw_part.strip()
        if not part:
            continue

        pieces = [piece.strip() for piece in part.split("|")]
        if len(pieces) == 2:
            store_name, url = pieces
            source_name = store_name
        elif len(pieces) == 3:
            store_name, source_name, url = pieces
        else:
            raise ValueError(
                "Grocery source must be Store|URL or Store|Source name|URL"
            )

        if store_name and url:
            sources.append(
                GrocerySourceConfig(
                    store_name=store_name,
                    source_name=source_name or store_name,
                    url=url,
                )
            )

    return sources


def _parse_locations(value: str) -> list[LocationConfig]:
    locations: list[LocationConfig] = []
    for raw_part in value.split(";"):
        part = raw_part.strip()
        if not part:
            continue

        pieces = [piece.strip() for piece in part.split("|")]
        if len(pieces) not in {4, 5}:
            raise ValueError(
                "Weather location must be Name|Latitude|Longitude|Timezone"
                " or Name|Latitude|Longitude|Timezone|hourly"
            )

        name, latitude, longitude, timezone = pieces[:4]
        hourly = len(pieces) == 5 and pieces[4].lower() in {
            "hourly",
            "true",
            "yes",
            "1",
        }
        locations.append(
            LocationConfig(
                name=name,
                latitude=float(latitude),
                longitude=float(longitude),
                timezone=timezone,
                hourly=hourly,
            )
        )

    return locations
