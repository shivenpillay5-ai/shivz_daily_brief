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


def write_morning_summary(
    brief_date: datetime,
    weather_reports: list[WeatherReport],
    market_pulse: MarketPulse | None,
    world_items: list[RankedItem],
    ai_tech_items: list[RankedItem],
    config: AppConfig,
    use_openai: bool = True,
) -> MorningSummary:
    facts = _build_summary_facts(
        brief_date=brief_date,
        weather_reports=weather_reports,
        market_pulse=market_pulse,
        world_items=world_items,
        ai_tech_items=ai_tech_items,
    )

    if use_openai and config.openai_api_key:
        try:
            return _write_with_openai(facts, config)
        except Exception as exc:
            print(f"OpenAI summary failed; using fallback. {exc}")

    return _fallback_summary(facts)


def _write_with_openai(
    facts: dict[str, object],
    config: AppConfig,
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
        body=str(data.get("body", "")).strip() or _fallback_summary(facts).body,
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
) -> dict[str, object]:
    return {
        "date": brief_date.strftime("%A, %d %B %Y"),
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
        "world_news": [_story_fact(item) for item in world_items[:3]],
        "ai_tech_news": [_story_fact(item) for item in ai_tech_items[:3]],
    }


def _story_fact(item: RankedItem) -> dict[str, str]:
    return {
        "title": item.title,
        "source": item.source,
        "summary": item.summary,
    }


def _fallback_summary(facts: dict[str, object]) -> MorningSummary:
    weather = _first_dict(facts.get("weather"))
    markets = [_ensure_dict(item) for item in _ensure_list(facts.get("markets"))]

    location = str(weather.get("location", "your area"))
    weather_cue = _weather_teaser(weather)
    market_cue = _market_teaser_short(markets)

    body = (
        f"{location} opens the day with {weather_cue}; meanwhile {market_cue} "
        "and the news desk has a few plot twists warming up below. Coffee first, scroll second, panic nowhere."
    )
    return MorningSummary(
        headline="Your Morning, Lightly Stirred",
        body=body,
        bullets=[],
        used_openai=False,
    )


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
