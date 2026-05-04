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
