from __future__ import annotations

"""Weather tool used by DailyBriefAgent."""

from datetime import datetime
from urllib.parse import urlencode

from daily_brief.config import LocationConfig
from daily_brief.http_client import get_json
from daily_brief.models import HourlyForecast, WeatherReport


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def fetch_weather(location: LocationConfig, hourly_hours: int = 8) -> WeatherReport:
    hourly_variables = [
        "temperature_2m",
        "apparent_temperature",
        "precipitation_probability",
        "weather_code",
    ]
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "timezone": location.timezone,
        "forecast_days": 1,
        "current": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "wind_speed_10m",
                "weather_code",
            ]
        ),
        "daily": ",".join(
            [
                "temperature_2m_min",
                "temperature_2m_max",
                "precipitation_probability_max",
                "weather_code",
            ]
        ),
    }
    if location.hourly:
        params["hourly"] = ",".join(hourly_variables)
    query = urlencode(params)
    data = get_json(f"{OPEN_METEO_URL}?{query}")
    current = data.get("current", {})
    daily = data.get("daily", {})
    current_code = _as_int(current.get("weather_code"))
    daily_codes = daily.get("weather_code") or []
    daily_code = _as_int(daily_codes[0]) if daily_codes else current_code
    code = current_code if current_code is not None else daily_code

    return WeatherReport(
        location_name=location.name,
        temperature_c=_as_float(current.get("temperature_2m")),
        feels_like_c=_as_float(current.get("apparent_temperature")),
        humidity_percent=_as_float(current.get("relative_humidity_2m")),
        wind_kmh=_as_float(current.get("wind_speed_10m")),
        daily_min_c=_first_float(daily.get("temperature_2m_min")),
        daily_max_c=_first_float(daily.get("temperature_2m_max")),
        precipitation_probability_percent=_first_float(
            daily.get("precipitation_probability_max")
        ),
        condition=WEATHER_CODES.get(code, "conditions unavailable"),
        hourly=_parse_hourly(data.get("hourly", {}), limit=hourly_hours)
        if location.hourly
        else [],
    )


def _parse_hourly(hourly: object, limit: int) -> list[HourlyForecast]:
    if not isinstance(hourly, dict):
        return []

    times = hourly.get("time") or []
    temperatures = hourly.get("temperature_2m") or []
    feels_like = hourly.get("apparent_temperature") or []
    rain = hourly.get("precipitation_probability") or []
    codes = hourly.get("weather_code") or []
    if not isinstance(times, list):
        return []

    start_index = _first_future_hour_index(times)
    forecasts: list[HourlyForecast] = []
    for index in range(start_index, min(start_index + limit, len(times))):
        code = _list_int(codes, index)
        forecasts.append(
            HourlyForecast(
                time_label=_format_hour_label(times[index]),
                temperature_c=_list_float(temperatures, index),
                feels_like_c=_list_float(feels_like, index),
                precipitation_probability_percent=_list_float(rain, index),
                condition=WEATHER_CODES.get(code, "conditions unavailable"),
            )
        )

    return forecasts


def _first_future_hour_index(times: list[object]) -> int:
    now = datetime.now()
    for index, raw_time in enumerate(times):
        try:
            forecast_time = datetime.fromisoformat(str(raw_time))
        except ValueError:
            continue
        if forecast_time >= now.replace(minute=0, second=0, microsecond=0):
            return index
    return 0


def _format_hour_label(raw_time: object) -> str:
    try:
        return datetime.fromisoformat(str(raw_time)).strftime("%H:%M")
    except ValueError:
        return str(raw_time)


def _list_float(values: object, index: int) -> float | None:
    if not isinstance(values, list) or index >= len(values):
        return None
    return _as_float(values[index])


def _list_int(values: object, index: int) -> int | None:
    if not isinstance(values, list) or index >= len(values):
        return None
    return _as_int(values[index])


def _first_float(values: object) -> float | None:
    if not isinstance(values, list) or not values:
        return None
    return _as_float(values[0])


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
