from __future__ import annotations

"""Email rendering tool used by DailyBriefAgent."""

import html
from datetime import datetime

from daily_brief.models import (
    HourlyForecast,
    MarketPulse,
    MarketQuote,
    MorningSummary,
    RankedItem,
    WeatherReport,
)


SUMMARY_MAX_CHARS = 360
BRIEF_NAME = "Shivz Daily Brief"


def render_text(
    brief_date: datetime,
    weather_reports: list[WeatherReport],
    world_items: list[RankedItem],
    ai_tech_items: list[RankedItem],
    morning_summary: MorningSummary | None = None,
    market_pulse: MarketPulse | None = None,
    warnings: list[str] | None = None,
) -> str:
    lines = [
        f"☕ {BRIEF_NAME} - {brief_date:%A, %d %B %Y}",
        "",
        *_summary_lines(morning_summary),
        "",
        "🌦 Weather",
        *_weather_lines(weather_reports),
    ]

    if market_pulse is not None:
        lines.extend(
            [
                "",
                "💸 Market Pulse",
                *_market_lines(market_pulse),
            ]
        )

    lines.extend(
        [
            "",
            "🌍 Top World News",
            *_story_lines(world_items),
            "",
            "🤖 Top AI and Tech Stories",
            *_story_lines(ai_tech_items),
        ]
    )

    if warnings:
        lines.extend(["", f"Note: {len(warnings)} source did not respond cleanly. The brief continued without it."])

    return "\n".join(lines)


def render_html(
    brief_date: datetime,
    weather_reports: list[WeatherReport],
    world_items: list[RankedItem],
    ai_tech_items: list[RankedItem],
    morning_summary: MorningSummary | None = None,
    market_pulse: MarketPulse | None = None,
    warnings: list[str] | None = None,
) -> str:
    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#edf4f8;font-family:Segoe UI,Arial,sans-serif;color:#202124">
    <div style="display:none;max-height:0;overflow:hidden;color:#edf4f8">
      {BRIEF_NAME}: weather, market pulse, world news, and AI stories for {brief_date:%A, %d %B %Y}.
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#edf4f8">
      <tr>
        <td align="center" style="padding:28px 12px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:760px;background:#ffffff;border-radius:22px;overflow:hidden;box-shadow:0 18px 45px rgba(27,55,73,0.16)">
            <tr>
              <td style="padding:0;background:#184e68;color:#ffffff">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="padding:34px 34px 30px">
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                        <tr>
                          <td valign="top">
                            <div style="display:inline-block;background:#d9f0f7;color:#184e68;border-radius:999px;padding:7px 11px;font-size:12px;letter-spacing:.8px;text-transform:uppercase;font-weight:800">Morning signal</div>
                            <h1 style="font-size:35px;line-height:1.08;margin:14px 0 0;font-weight:800">☕ {BRIEF_NAME}</h1>
                          </td>
                          <td valign="top" align="right" style="padding-left:18px">
                            <div style="display:inline-block;border:1px solid rgba(255,255,255,.35);border-radius:14px;padding:10px 12px;color:#e7f6fb;font-size:14px;font-weight:700;text-align:right;white-space:nowrap">
                              {brief_date:%A}<br>
                              <span style="font-weight:600;color:#b9e3f2">{brief_date:%d %B %Y}</span>
                            </div>
                          </td>
                        </tr>
                      </table>
                      <div style="margin-top:20px;padding:16px 18px;border-left:4px solid #b9e3f2;background:rgba(255,255,255,.08);border-radius:14px">
                        <p style="font-size:15px;line-height:1.5;margin:0;color:#e7f6fb">
                          Weather, world chaos, and AI plot twists, lightly toasted and served before your inbox starts making demands.
                        </p>
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 34px 12px">
                {_summary_section_html(morning_summary)}
                {_divider_html()}
                {_weather_section_html(weather_reports)}
                {_divider_html()}
                {_market_section_html(market_pulse)}
                {_divider_html()}
                {_section_html("🌍", "Top World News", "The five stories worth scanning first.", world_items)}
                {_divider_html()}
                {_section_html("🤖", "Top AI and Tech Stories", "Signals from AI, platforms, research, and startup land.", ai_tech_items)}
                <p style="margin:28px 0 8px;color:#718096;font-size:12px;text-align:center">
                  Built by your {BRIEF_NAME} Agent. Links open in your browser.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def render_whatsapp_text(
    brief_date: datetime,
    weather_reports: list[WeatherReport],
    world_items: list[RankedItem],
    ai_tech_items: list[RankedItem],
    morning_summary: MorningSummary | None = None,
    market_pulse: MarketPulse | None = None,
) -> str:
    lines = [
        f"☕ *{BRIEF_NAME}*",
        f"{brief_date:%A, %d %B %Y}",
        "",
        *_whatsapp_summary_lines(morning_summary),
        "🌦 *Weather*",
        *_whatsapp_weather_lines(weather_reports),
        "",
        *_whatsapp_market_section_lines(market_pulse),
        "🌍 *Top World News*",
        *_whatsapp_story_lines(world_items[:3]),
        "",
        "🤖 *AI + Tech*",
        *_whatsapp_story_lines(ai_tech_items[:3]),
        "",
        "Full pretty version is in your email inbox.",
    ]
    return _clip_message("\n".join(lines))


def _summary_lines(morning_summary: MorningSummary | None) -> list[str]:
    if morning_summary is None:
        return []

    lines = [
        "🧭 Morning Summary",
        morning_summary.headline,
        morning_summary.body,
    ]
    return lines


def _whatsapp_summary_lines(
    morning_summary: MorningSummary | None,
) -> list[str]:
    if morning_summary is None:
        return []

    return [
        f"🧭 *{morning_summary.headline}*",
        _shorten(morning_summary.body, max_chars=260),
        "",
    ]


def _summary_section_html(morning_summary: MorningSummary | None) -> str:
    if morning_summary is None:
        return ""

    return f"""
    <div style="margin-bottom:28px">
      <div style="font-size:13px;color:#4f6f7d;font-weight:700;text-transform:uppercase;letter-spacing:.8px">🧭 Morning read</div>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top:8px;border-radius:18px;background:#f3fbfd;border:1px solid #cce8f0">
        <tr>
          <td valign="top" style="width:72px;padding:22px 0 22px 22px">
            <div style="width:54px;height:54px;border-radius:16px;background:#184e68;color:#ffffff;text-align:center;line-height:54px;font-size:28px">⚡</div>
          </td>
          <td style="padding:22px">
            <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom:10px">
              <tr>
                <td style="background:#e6fffa;color:#1f7a8c;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px">🌦 Weather</td>
                <td style="width:6px"></td>
                <td style="background:#fff5db;color:#8a5a00;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px">💸 Markets</td>
                <td style="width:6px"></td>
                <td style="background:#eef2ff;color:#344e86;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px">🤖 Signals</td>
              </tr>
            </table>
            <h2 style="font-size:27px;line-height:1.15;margin:0 0 9px;color:#102a43">{html.escape(morning_summary.headline)}</h2>
            <p style="font-size:16px;line-height:1.58;margin:0;color:#334e68">{html.escape(morning_summary.body)}</p>
          </td>
        </tr>
      </table>
    </div>
    """


def _story_lines(items: list[RankedItem]) -> list[str]:
    if not items:
        return ["- No stories found."]

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item.title} ({item.source})")
        lines.append(f"   {_shorten(item.summary)}")
        lines.append(f"   {item.url}")
    return lines


def _market_lines(market_pulse: MarketPulse | None) -> list[str]:
    if market_pulse is None:
        return []
    if not market_pulse.quotes:
        return ["- No market data found."]

    return [
        (
            f"- {_market_icon(quote)} {quote.label}: {_format_market_value(quote)}"
            f"{_format_change(quote.change_percent)}"
            f"{_format_market_source(quote)}"
        )
        for quote in market_pulse.quotes
    ]


def _whatsapp_market_section_lines(
    market_pulse: MarketPulse | None,
) -> list[str]:
    if market_pulse is None or not market_pulse.quotes:
        return []

    fx_quotes = [
        quote for quote in market_pulse.quotes if quote.label in {"USD/ZAR", "GBP/ZAR"}
    ]
    commodity_quotes = [
        quote for quote in market_pulse.quotes if quote.label not in {"USD/ZAR", "GBP/ZAR"}
    ]
    lines = ["💸 *Market Pulse*"]
    if fx_quotes:
        lines.append(" | ".join(_format_market_compact(quote) for quote in fx_quotes))
    if commodity_quotes:
        lines.append(
            " | ".join(_format_market_compact(quote) for quote in commodity_quotes)
        )
    lines.append("")
    return lines


def _whatsapp_weather_lines(weather_reports: list[WeatherReport]) -> list[str]:
    if not weather_reports:
        return ["No weather found."]

    lines: list[str] = []
    for index, weather in enumerate(weather_reports):
        if index == 0:
            lines.append(
                f"{_condition_emoji(weather)} *{weather.location_name}*: "
                f"{_format_value(weather.temperature_c, 'C')} now, "
                f"high {_format_value(weather.daily_max_c, 'C')}, "
                f"rain {_format_value(weather.precipitation_probability_percent, '%')}. "
                f"{_whatsapp_weather_mood(weather)}"
            )
            continue

        lines.append(
            f"{_condition_emoji(weather)} *{weather.location_name}*: "
            f"{_format_value(weather.temperature_c, 'C')} now, "
            f"{_format_weather_range(weather)}, "
            f"rain {_format_value(weather.precipitation_probability_percent, '%')}."
        )

    return lines


def _whatsapp_story_lines(items: list[RankedItem]) -> list[str]:
    if not items:
        return ["No stories found."]

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. *{item.title}*")
        lines.append(f"   {item.url}")
    return lines


def _weather_lines(weather_reports: list[WeatherReport]) -> list[str]:
    if not weather_reports:
        return ["No weather found."]

    lines: list[str] = []
    for weather in weather_reports:
        lines.append(_weather_sentence(weather))
        lines.append(_weather_mood(weather))
        if weather.hourly:
            lines.append("   Hourly:")
            for forecast in weather.hourly:
                lines.append(
                    "   "
                    f"{forecast.time_label}: "
                    f"{_condition_emoji_for_condition(forecast.condition)} "
                    f"{_format_value(forecast.temperature_c, 'C')}, "
                    f"rain {_format_value(forecast.precipitation_probability_percent, '%')}"
                )
        lines.append("")

    return lines[:-1]


def _section_html(
    emoji: str,
    title: str,
    subtitle: str,
    items: list[RankedItem],
) -> str:
    return f"""
    <div style="margin-top:30px">
      <div style="font-size:13px;color:#4f6f7d;font-weight:700;text-transform:uppercase;letter-spacing:.8px">{emoji} {html.escape(title)}</div>
      <h2 style="font-size:23px;line-height:1.2;margin:6px 0 4px;color:#102a43">{html.escape(title)}</h2>
      <p style="margin:0 0 14px;color:#627d8a;font-size:14px">{html.escape(subtitle)}</p>
      {_story_list_html(items)}
    </div>
    """


def _divider_html() -> str:
    return """
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:30px 0">
      <tr>
        <td style="width:56px;height:4px;background:#1f7a8c;border-radius:999px 0 0 999px;font-size:0;line-height:0">&nbsp;</td>
        <td style="height:4px;background:#cce8f0;border-radius:0 999px 999px 0;font-size:0;line-height:0">&nbsp;</td>
      </tr>
    </table>
    """


def _story_list_html(items: list[RankedItem]) -> str:
    if not items:
        return """
        <div style="padding:18px;border-radius:14px;background:#f7fafc;border:1px solid #d9e2ec;color:#627d8a">
          No stories found.
        </div>
        """

    entries = []
    for index, item in enumerate(items, start=1):
        entries.append(
            f"""
            <tr>
              <td style="padding:0 0 12px">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #d9e2ec;border-radius:16px;background:#fbfdfe">
                  <tr>
                    <td valign="top" style="width:44px;padding:16px 0 16px 16px">
                      <div style="width:30px;height:30px;border-radius:999px;background:#d9f0f7;color:#184e68;text-align:center;line-height:30px;font-size:14px;font-weight:800">{index}</div>
                    </td>
                    <td style="padding:16px">
                      <div style="font-size:12px;color:#607d8b;font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin-bottom:5px">{html.escape(item.source)}</div>
                      <a href="{html.escape(item.url)}" style="font-size:18px;line-height:1.28;color:#0b3954;text-decoration:none;font-weight:800">{html.escape(item.title)}</a>
                      <p style="font-size:14px;line-height:1.5;color:#334e68;margin:8px 0 14px">{html.escape(_shorten(item.summary))}</p>
                      <a href="{html.escape(item.url)}" style="display:inline-block;background:#1f7a8c;color:#ffffff;text-decoration:none;padding:9px 13px;border-radius:999px;font-size:13px;font-weight:700">Read story →</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """
        )
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
      {''.join(entries)}
    </table>
    """


def _market_section_html(market_pulse: MarketPulse | None) -> str:
    if market_pulse is None:
        return ""

    if not market_pulse.quotes:
        cards = """
        <td style="padding:18px;border-radius:14px;background:#f7fafc;border:1px solid #d9e2ec;color:#627d8a">
          No market data found.
        </td>
        """
    else:
        cards = "".join(_market_quote_html(quote) for quote in market_pulse.quotes)

    return f"""
    <div style="margin:30px 0 28px">
      <div style="font-size:13px;color:#4f6f7d;font-weight:700;text-transform:uppercase;letter-spacing:.8px">💸 Market pulse</div>
      <h2 style="font-size:23px;line-height:1.2;margin:6px 0 4px;color:#102a43">Markets At A Glance</h2>
      <p style="margin:0 0 14px;color:#627d8a;font-size:14px">Rand crosses, metals, and Brent before the day gets ideas.</p>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
        <tr>{cards}</tr>
      </table>
    </div>
    """


def _market_quote_html(quote: MarketQuote) -> str:
    change = _format_change(quote.change_percent).strip()
    change_html = ""
    if change:
        change_color = "#276749" if (quote.change_percent or 0) >= 0 else "#9b2c2c"
        change_bg = "#e6fffa" if (quote.change_percent or 0) >= 0 else "#fff5f5"
        change_html = (
            f'<span style="display:inline-block;margin-top:8px;padding:4px 7px;'
            f'border-radius:999px;background:{change_bg};color:{change_color};'
            f'font-size:11px;font-weight:800">{html.escape(change)}</span>'
        )

    source = "Latest available"
    if quote.as_of:
        source = quote.as_of

    return f"""
    <td valign="top" style="width:20%;padding:4px 6px 4px 0">
      <div style="min-height:98px;background:#fbfdfe;border-radius:14px;border:1px solid #d9e2ec;padding:13px 11px">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
          <tr>
            <td valign="middle" style="font-size:21px;line-height:1;padding-right:6px;width:34px">{_market_icon(quote)}</td>
            <td valign="middle" style="font-size:11px;color:#718096;text-transform:uppercase;font-weight:800;letter-spacing:.5px">{html.escape(quote.label)}</td>
          </tr>
        </table>
        <div style="font-size:19px;line-height:1.15;color:#102a43;font-weight:900;margin-top:5px">{html.escape(_format_market_value(quote))}</div>
        {change_html}
        <div style="font-size:10px;color:#7b8794;margin-top:8px;line-height:1.35">{html.escape(source)}</div>
      </div>
    </td>
    """


def _weather_section_html(weather_reports: list[WeatherReport]) -> str:
    if not weather_reports:
        return """
        <div style="padding:18px;border-radius:14px;background:#f7fafc;border:1px solid #d9e2ec;color:#627d8a">
          No weather found.
        </div>
        """

    featured = _weather_card_html(weather_reports[0], featured=True)
    other_cards = "".join(
        _weather_card_html(weather, featured=False) for weather in weather_reports[1:]
    )
    return f"""
    <div style="margin-bottom:28px">
      <div style="font-size:13px;color:#4f6f7d;font-weight:700;text-transform:uppercase;letter-spacing:.8px">🌦 Weather watch</div>
      <h2 style="font-size:23px;line-height:1.2;margin:6px 0 14px;color:#102a43">Weather Around The People</h2>
      {featured}
      <div style="height:12px"></div>
      {other_cards}
    </div>
    """


def _weather_card_html(weather: WeatherReport, featured: bool) -> str:
    temp = _format_value(weather.temperature_c, "C")
    feels_like = _format_value(weather.feels_like_c, "C")
    range_value = "Unavailable"
    if weather.daily_min_c is not None and weather.daily_max_c is not None:
        range_value = f"{weather.daily_min_c:.0f}-{weather.daily_max_c:.0f}C"
    rain = _format_value(weather.precipitation_probability_percent, "%")
    wind = _format_value(weather.wind_kmh, " km/h")
    condition_emoji = _condition_emoji(weather)
    temp_emoji = _temperature_emoji(weather)
    hourly_html = _hourly_html(weather.hourly) if weather.hourly else ""
    card_background = "#f3fbfd" if featured else "#fbfdfe"
    title_size = "26px" if featured else "22px"
    padding = "24px" if featured else "20px"

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:12px;border-radius:18px;background:{card_background};border:1px solid #cce8f0">
      <tr>
        <td style="padding:{padding}">
          <h2 style="font-size:{title_size};line-height:1.2;margin:0 0 4px;color:#102a43">{html.escape(weather.location_name)}</h2>
          <p style="font-size:15px;line-height:1.5;margin:0 0 8px;color:#334e68">{condition_emoji} {html.escape(weather.condition.title())}</p>
          <p style="font-size:14px;line-height:1.5;margin:0 0 16px;color:#486581">{html.escape(_weather_mood(weather))}</p>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
              {_metric_html(f"{temp_emoji} Now", temp)}
              {_metric_html("🤔 Feels Like", feels_like)}
              {_metric_html("🌡 Range", range_value)}
              {_metric_html("☔ Rain", rain)}
              {_metric_html("💨 Wind", wind)}
            </tr>
          </table>
          {hourly_html}
        </td>
      </tr>
    </table>
    """


def _hourly_html(hourly: list[HourlyForecast]) -> str:
    if not hourly:
        return ""

    entries = []
    for forecast in hourly:
        entries.append(
            f"""
            <td style="padding:4px 6px 4px 0">
              <div style="background:#ffffff;border-radius:12px;border:1px solid #d9e2ec;padding:10px 9px;text-align:center">
                <div style="font-size:11px;color:#718096;font-weight:800">{html.escape(forecast.time_label)}</div>
                <div style="font-size:18px;line-height:1;margin:6px 0">{_condition_emoji_for_condition(forecast.condition)}</div>
                <div style="font-size:15px;color:#102a43;font-weight:800">{html.escape(_format_value(forecast.temperature_c, "C"))}</div>
                <div style="font-size:11px;color:#627d8a;margin-top:3px">☔ {html.escape(_format_value(forecast.precipitation_probability_percent, "%"))}</div>
              </div>
            </td>
            """
        )

    return f"""
    <div style="height:14px"></div>
    <div style="font-size:12px;color:#4f6f7d;font-weight:800;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px">Next few hours</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
      <tr>{''.join(entries)}</tr>
    </table>
    """


def _metric_html(label: str, value: str) -> str:
    return f"""
    <td style="padding:4px 6px 4px 0">
      <div style="background:#ffffff;border-radius:12px;border:1px solid #d9e2ec;padding:11px 10px">
        <div style="font-size:11px;color:#718096;text-transform:uppercase;font-weight:700;letter-spacing:.5px">{html.escape(label)}</div>
        <div style="font-size:17px;color:#102a43;font-weight:800;margin-top:3px">{html.escape(value)}</div>
      </div>
    </td>
    """


def _weather_sentence(weather: WeatherReport) -> str:
    pieces = [weather.location_name, f"{_condition_emoji(weather)} {weather.condition}"]
    if weather.temperature_c is not None:
        pieces.append(f"{weather.temperature_c:.0f}C now")
    if weather.feels_like_c is not None:
        pieces.append(f"feels like {weather.feels_like_c:.0f}C")
    if weather.daily_min_c is not None and weather.daily_max_c is not None:
        pieces.append(f"range {weather.daily_min_c:.0f}-{weather.daily_max_c:.0f}C")
    if weather.precipitation_probability_percent is not None:
        pieces.append(f"rain chance {weather.precipitation_probability_percent:.0f}%")
    if weather.wind_kmh is not None:
        pieces.append(f"wind {weather.wind_kmh:.0f} km/h")
    return "; ".join(pieces) + "."


def _condition_emoji(weather: WeatherReport) -> str:
    return _condition_emoji_for_condition(weather.condition)


def _condition_emoji_for_condition(condition_text: str) -> str:
    condition = condition_text.lower()
    if "thunder" in condition:
        return "⛈️"
    if "rain" in condition or "drizzle" in condition or "shower" in condition:
        return "🌧️"
    if "snow" in condition:
        return "❄️"
    if "fog" in condition:
        return "🌫️"
    if "clear" in condition:
        return "☀️"
    if "cloud" in condition or "overcast" in condition:
        return "☁️"
    return "🌤️"


def _temperature_emoji(weather: WeatherReport) -> str:
    temperature = weather.feels_like_c if weather.feels_like_c is not None else weather.temperature_c
    if temperature is None:
        return "🌡️"
    if temperature <= 10:
        return "🥶"
    if temperature <= 17:
        return "🧥"
    if temperature <= 25:
        return "😎"
    if temperature <= 31:
        return "🔥"
    return "🫠"


def _weather_mood(weather: WeatherReport) -> str:
    temperature = weather.feels_like_c if weather.feels_like_c is not None else weather.temperature_c
    if temperature is None:
        return "Weather mood: mysterious. The sky is keeping its cards close today."
    if temperature <= 10:
        return "Weather mood: very cold. Blanket diplomacy is strongly advised."
    if temperature <= 17:
        return "Weather mood: crisp. Bring a jacket and pretend you planned the outfit."
    if temperature <= 25:
        return "Weather mood: pleasant. Main-character weather has entered the chat."
    if temperature <= 31:
        return "Weather mood: warm. Hydrate like your inbox depends on it."
    return "Weather mood: spicy. The sun woke up and chose drama."


def _whatsapp_weather_mood(weather: WeatherReport) -> str:
    temperature = weather.feels_like_c if weather.feels_like_c is not None else weather.temperature_c
    if temperature is None:
        return "Sky is being mysterious."
    if temperature <= 10:
        return "Blanket diplomacy advised."
    if temperature <= 17:
        return "Jacket earns its keep."
    if temperature <= 25:
        return "Civilised weather. Suspiciously nice."
    if temperature <= 31:
        return "Hydrate like a professional."
    return "Sun chose drama."


def _format_weather_range(weather: WeatherReport) -> str:
    if weather.daily_min_c is None or weather.daily_max_c is None:
        return "range unavailable"
    return f"{weather.daily_min_c:.0f}-{weather.daily_max_c:.0f}C"


def _format_market_value(quote: MarketQuote) -> str:
    if quote.value is None:
        return "Unavailable"
    value = f"{quote.value:,.{quote.decimals}f}"
    return f"{quote.prefix}{value}{quote.suffix}"


def _format_market_compact(quote: MarketQuote) -> str:
    return (
        f"{_market_icon(quote)} {quote.label} "
        f"{_format_market_value(quote)}{_format_change(quote.change_percent)}"
    )


def _format_change(change_percent: float | None) -> str:
    if change_percent is None:
        return ""

    arrow = "↑" if change_percent >= 0 else "↓"
    return f" {arrow} {abs(change_percent):.1f}%"


def _market_icon(quote: MarketQuote) -> str:
    icons = {
        "USD/ZAR": "💵",
        "GBP/ZAR": "💷",
        "Gold": "🥇",
        "Silver": "🥈",
        "Brent": "🛢️",
    }
    return icons.get(quote.label, "💸")


def _format_market_source(quote: MarketQuote) -> str:
    if not quote.as_of:
        return ""
    return f" ({quote.source}, {quote.as_of})"


def _format_value(value: float | None, suffix: str) -> str:
    if value is None:
        return "Unavailable"
    return f"{value:.0f}{suffix}"


def _shorten(value: str, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    value = " ".join(value.split())
    if len(value) <= max_chars:
        return value

    truncated = value[: max_chars - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated}..."


def _clip_message(value: str, max_chars: int = 3800) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 30].rstrip() + "\n\n...trimmed for WhatsApp"
