from __future__ import annotations

"""Morning summary writing tool used by DailyBriefAgent."""

import json
from datetime import datetime

from daily_brief.config import AppConfig
from daily_brief.http_client import post_json
from daily_brief.models import MarketPulse, MorningSummary, RankedItem, WeatherReport
from daily_brief.prompts.summary_prompt import (
    SUMMARY_INSTRUCTIONS,
    build_summary_input,
)
from daily_brief.tools.ranking import RESPONSES_API_URL


SUMMARY_OPENERS = (
    (
        "Morning, Lightly Stirred",
        "{location} starts with {weather_cue}, while {market_cue} and the headlines are lining up their little arguments. Take the first sip before the tabs start multiplying.",
    ),
    (
        "Coffee Before The Plot",
        "{location} is opening on {weather_cue}; {market_cue}, and the news desk has already found the day's moving parts. Breathe first, scroll second, panic nowhere.",
    ),
    (
        "The Day Checks In",
        "{location} begins with {weather_cue}, with {market_cue} somewhere nearby doing its morning stretches. The rest of the brief is awake, dressed, and suspiciously full of context.",
    ),
    (
        "Signals With A Smile",
        "{location} brings {weather_cue} to the front door, while {market_cue} and the headlines do their best impression of a dashboard. Nothing needs panic yet; it just needs a decent read.",
    ),
    (
        "Morning Board Is Open",
        "{location} has {weather_cue} on the weather board, and {market_cue} before the day gets too confident. The news below has range, opinions, and at least one raised eyebrow.",
    ),
    (
        "Small Sip, Big Picture",
        "{location} opens with {weather_cue}, while {market_cue} and the wider world start making little noises. This is the calm scan before the calendar remembers your name.",
    ),
    (
        "Today's Opening Scene",
        "{location} walks in with {weather_cue}; {market_cue}, and the headlines are already shuffling papers. Coffee gets first chair, the chaos can wait its turn.",
    ),
    (
        "Brain, Meet Morning",
        "{location} is serving {weather_cue}, with {market_cue} and the news cycle warming up in the background. It is a gentle on-ramp, not a fire drill.",
    ),
    (
        "The Briefing Wakes Up",
        "{location} starts the day on {weather_cue}, while {market_cue} and the headlines blink into view. The important bits are below, neatly folded and mostly house-trained.",
    ),
    (
        "Plot Twists On Low Heat",
        "{location} opens with {weather_cue}; {market_cue}, and the news desk is already simmering. Read this like a weatherproof jacket for the brain.",
    ),
    (
        "Morning Without The Noise",
        "{location} brings {weather_cue}, while {market_cue} and the headlines keep the signal lights on. The trick is to notice enough without inviting the whole circus in.",
    ),
    (
        "A Civilised Start",
        "{location} begins with {weather_cue}, and {market_cue} before the day starts asking for decisions. The rest is a quick map, not a maze.",
    ),
    (
        "Weather, Money, Mischief",
        "{location} rolls out {weather_cue}; {market_cue}, and the headlines are already making eye contact. Consider this the useful version of peeking through the curtains.",
    ),
    (
        "The Morning Dashboard",
        "{location} is showing {weather_cue}, while {market_cue} and the news desk add a few blinking lights. We are checking the panel, not wrestling the machine.",
    ),
    (
        "Today's First Look",
        "{location} opens on {weather_cue}; {market_cue}, and the broader story board has started filling itself in. Sip slowly, the day is not allowed to sprint yet.",
    ),
    (
        "Notes From The Start Line",
        "{location} starts with {weather_cue}, while {market_cue} and the headlines shuffle into their lanes. The morning has range, but at least the brief has order.",
    ),
    (
        "Morning, With Context",
        "{location} gives us {weather_cue}, with {market_cue} and the news cycle already clearing its throat. A quick scan now should save at least three confused glances later.",
    ),
    (
        "The Calm Before Tabs",
        "{location} begins on {weather_cue}; {market_cue}, and the headlines are stretching like they have plans. Read the essentials before the browser becomes a jungle.",
    ),
    (
        "Little Signals Everywhere",
        "{location} opens with {weather_cue}, while {market_cue} and the news below start dropping breadcrumbs. Follow the useful ones, ignore the crumbs with attitude.",
    ),
    (
        "Today, Gently Decoded",
        "{location} starts with {weather_cue}; {market_cue}, and the world is already adding footnotes. This is the friendly decode before everything gets louder.",
    ),
    (
        "The Morning Scan",
        "{location} has {weather_cue} in the air, with {market_cue} and enough headlines to make the coffee feel employed. The signal is below, trimmed and ready.",
    ),
    (
        "First Sip Intelligence",
        "{location} opens with {weather_cue}, while {market_cue} and the headlines do their early-morning paperwork. No drama required, just a useful scan.",
    ),
    (
        "Before The Inbox Roars",
        "{location} is starting on {weather_cue}; {market_cue}, and the news desk has already put its shoes on. Get the shape of the day before the inbox starts narrating.",
    ),
    (
        "Morning With A Wink",
        "{location} begins with {weather_cue}, while {market_cue} and the headlines try to look casual. They are not casual, but they are neatly arranged below.",
    ),
    (
        "Today's Useful Gossip",
        "{location} has {weather_cue} to report, with {market_cue} and the day's bigger stories waiting in the wings. Useful gossip only, no doom garnish.",
    ),
    (
        "The Day's First Draft",
        "{location} opens on {weather_cue}; {market_cue}, and the headlines are sketching the outline. We will keep the pen steady and the panic budget low.",
    ),
    (
        "Quietly Useful Morning",
        "{location} starts with {weather_cue}, while {market_cue} and the news cycle hum in the background. Nothing here needs shouting; the useful bits can speak clearly.",
    ),
    (
        "A Neat Little Runway",
        "{location} gives the day {weather_cue}; {market_cue}, and the headlines are ready for takeoff. This is your runway check before the meetings taxi in.",
    ),
    (
        "Morning Signal Check",
        "{location} opens with {weather_cue}, while {market_cue} and the wider world start blinking on the board. Enough to orient you, not enough to steal your breakfast.",
    ),
    (
        "The Friendly Brief",
        "{location} starts on {weather_cue}; {market_cue}, and the headlines have brought snacks and opinions. We will take the snacks, inspect the opinions, and move calmly.",
    ),
)


def write_morning_summary(
    brief_date: datetime,
    weather_reports: list[WeatherReport],
    market_pulse: MarketPulse | None,
    world_items: list[RankedItem],
    ai_tech_items: list[RankedItem],
    config: AppConfig,
    use_openai: bool = True,
    south_africa_items: list[RankedItem] | None = None,
) -> MorningSummary:
    facts = _build_summary_facts(
        brief_date=brief_date,
        weather_reports=weather_reports,
        market_pulse=market_pulse,
        world_items=world_items,
        ai_tech_items=ai_tech_items,
        south_africa_items=south_africa_items or [],
    )

    if use_openai and config.openai_api_key:
        try:
            return _write_with_openai(facts, config, brief_date)
        except Exception as exc:
            print(f"OpenAI summary failed; using fallback. {exc}")

    return _fallback_summary(facts, brief_date)


def _write_with_openai(
    facts: dict[str, object],
    config: AppConfig,
    brief_date: datetime,
) -> MorningSummary:
    payload = {
        "model": config.openai_model,
        "instructions": SUMMARY_INSTRUCTIONS,
        "input": build_summary_input(
            json.dumps(facts, ensure_ascii=True, indent=2),
        ),
        "max_output_tokens": 800,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "daily_brief_morning_summary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "headline": {"type": "string"},
                        "body": {"type": "string"},
                        "bullets": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["headline", "body", "bullets"],
                },
            }
        },
    }
    response = post_json(
        RESPONSES_API_URL,
        payload=payload,
        headers={"Authorization": f"Bearer {config.openai_api_key}"},
    )
    data = json.loads(_extract_output_text(response))
    return MorningSummary(
        headline=str(data.get("headline", "")).strip() or "Morning Signal",
        body=str(data.get("body", "")).strip()
        or _fallback_summary(facts, brief_date).body,
        bullets=[
            str(bullet).strip()
            for bullet in data.get("bullets", [])
            if str(bullet).strip()
        ][:3],
        used_openai=True,
    )


def _build_summary_facts(
    brief_date: datetime,
    weather_reports: list[WeatherReport],
    market_pulse: MarketPulse | None,
    world_items: list[RankedItem],
    ai_tech_items: list[RankedItem],
    south_africa_items: list[RankedItem],
) -> dict[str, object]:
    return {
        "date": brief_date.strftime("%A, %d %B %Y"),
        "opener_style": _summary_opener(brief_date)[0],
        "weather": [
            {
                "location": weather.location_name,
                "condition": weather.condition,
                "temperature_c": weather.temperature_c,
                "daily_min_c": weather.daily_min_c,
                "daily_max_c": weather.daily_max_c,
                "rain_percent": weather.precipitation_probability_percent,
            }
            for weather in weather_reports
        ],
        "markets": [
            {
                "label": quote.label,
                "value": quote.value,
                "prefix": quote.prefix,
                "suffix": quote.suffix,
                "change_percent": quote.change_percent,
                "as_of": quote.as_of,
            }
            for quote in (market_pulse.quotes if market_pulse else [])
        ],
        "south_africa_news": [_story_fact(item) for item in south_africa_items[:3]],
        "world_news": [_story_fact(item) for item in world_items[:3]],
        "ai_tech_news": [_story_fact(item) for item in ai_tech_items[:3]],
    }


def _story_fact(item: RankedItem) -> dict[str, str]:
    return {
        "title": item.title,
        "source": item.source,
        "summary": item.summary,
    }


def _fallback_summary(facts: dict[str, object], brief_date: datetime) -> MorningSummary:
    weather = _first_dict(facts.get("weather"))
    markets = [_ensure_dict(item) for item in _ensure_list(facts.get("markets"))]

    location = str(weather.get("location", "your area"))
    weather_cue = _weather_teaser(weather)
    market_cue = _market_teaser_short(markets)
    headline, body_template = _summary_opener(brief_date)

    body = body_template.format(
        location=location,
        weather_cue=weather_cue,
        market_cue=market_cue,
    )
    return MorningSummary(
        headline=headline,
        body=body,
        bullets=[],
        used_openai=False,
    )


def _summary_opener(brief_date: datetime) -> tuple[str, str]:
    return SUMMARY_OPENERS[brief_date.toordinal() % len(SUMMARY_OPENERS)]


def _market_teaser_short(markets: list[dict[str, object]]) -> str:
    if not markets:
        return "the market board is still waking up"

    movers = sum(
        1
        for quote in markets
        if isinstance(quote.get("change_percent"), (int, float))
    )
    if movers >= 3:
        return "the market board is already flashing a few signals"
    if movers:
        return "the market board has started blinking"

    return "the market board is on standby"


def _weather_teaser(weather: dict[str, object]) -> str:
    rain = weather.get("rain_percent")
    temperature = weather.get("temperature_c")
    if isinstance(rain, (int, float)) and rain >= 50:
        return "umbrella energy in the forecast"
    if isinstance(temperature, (int, float)) and temperature >= 28:
        return "the sun clearly auditioning for a bigger role"
    if isinstance(temperature, (int, float)) and temperature <= 15:
        return "a jacket making a strong case for itself"
    return "a fairly civilised weather opening"


def _first_dict(value: object) -> dict[str, object]:
    items = _ensure_list(value)
    if items and isinstance(items[0], dict):
        return items[0]
    return {}


def _ensure_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _ensure_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _extract_output_text(response: dict[str, object]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    parts: list[str] = []
    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)

    text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("OpenAI response did not include output text.")
    return text
