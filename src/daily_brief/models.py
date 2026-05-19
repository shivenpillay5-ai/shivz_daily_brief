from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class HourlyForecast:
    time_label: str
    temperature_c: float | None
    feels_like_c: float | None
    precipitation_probability_percent: float | None
    condition: str


@dataclass(frozen=True)
class WeatherReport:
    location_name: str
    temperature_c: float | None
    feels_like_c: float | None
    humidity_percent: float | None
    wind_kmh: float | None
    daily_min_c: float | None
    daily_max_c: float | None
    precipitation_probability_percent: float | None
    condition: str
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = ""
    hourly: list[HourlyForecast] = field(default_factory=list)


@dataclass(frozen=True)
class MarketQuote:
    label: str
    value: float | None
    prefix: str
    suffix: str
    source: str
    as_of: str
    decimals: int = 2
    change_percent: float | None = None


@dataclass(frozen=True)
class MarketPulse:
    quotes: list[MarketQuote] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MorningSummary:
    headline: str
    body: str
    bullets: list[str] = field(default_factory=list)
    used_openai: bool = False


@dataclass(frozen=True)
class ScriptureVerse:
    reference: str
    text: str
    translation: str


@dataclass(frozen=True)
class DevotionalContent:
    title: str
    verse: ScriptureVerse
    reflection: str
    motivation: str = ""
    used_openai: bool = False


@dataclass(frozen=True)
class MealIdea:
    title: str
    description: str
    ingredients: list[str]
    steps: list[str]
    prep_note: str
    image_url: str
    image_alt: str
    image_credit: str
    image_credit_url: str


@dataclass(frozen=True)
class MarriageSpark:
    title: str
    motivation: str
    fun_idea: str
    conversation_starter: str


@dataclass(frozen=True)
class HistoryMoment:
    title: str
    paragraph: str
    year: int | None = None
    source: str = ""
    source_url: str = ""


@dataclass(frozen=True)
class DailyFunFact:
    title: str
    body: str


@dataclass(frozen=True)
class CalendarEvent:
    calendar_id: str
    calendar_name: str
    title: str
    start: datetime
    end: datetime | None = None
    all_day: bool = False
    location: str = ""


@dataclass(frozen=True)
class CoupleBriefContent:
    names: str
    reminders: list[str]
    meal: MealIdea
    spark: MarriageSpark
    closing: str
    history_moment: HistoryMoment | None = None
    fun_fact: DailyFunFact | None = None
    calendar_events: list[CalendarEvent] = field(default_factory=list)
    calendar_note: str = ""


@dataclass(frozen=True)
class GrocerySpecial:
    store_name: str
    item_name: str
    price: str
    promotion: str = ""
    validity: str = ""
    source_name: str = ""
    source_url: str = ""
    category: str = ""
    image_url: str = ""
    product_url: str = ""
    catalogue_url: str = ""
    regular_price: str = ""
    saving_amount: str = ""
    saving_percent: float | None = None
    unit_price: str = ""
    deal_score: int = 0


@dataclass(frozen=True)
class GroceryStoreSpecials:
    store_name: str
    area: str
    specials: list[GrocerySpecial] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GrocerySpecialsContent:
    area: str
    generated_at: datetime
    stores: list[GroceryStoreSpecials] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FeedItem:
    title: str
    url: str
    source: str
    summary: str
    published_at: datetime | None
    category: str


@dataclass(frozen=True)
class RankedItem:
    title: str
    url: str
    source: str
    summary: str
    published_at: datetime | None = None
