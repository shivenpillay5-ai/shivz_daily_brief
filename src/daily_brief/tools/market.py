from __future__ import annotations

"""Market pulse fetching tool used by DailyBriefAgent."""

from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

from daily_brief.http_client import get_json
from daily_brief.models import MarketPulse, MarketQuote


FRANKFURTER_API_ROOT = "https://api.frankfurter.dev/v1"
FRANKFURTER_BASE_URL = f"{FRANKFURTER_API_ROOT}/latest"
YAHOO_CHART_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

FX_QUOTES = (
    ("USD/ZAR", "USD", "ZAR"),
    ("GBP/ZAR", "GBP", "ZAR"),
)

COMMODITY_QUOTES = (
    ("Gold", "GC=F", "$", "/oz"),
    ("Silver", "SI=F", "$", "/oz"),
    ("Brent", "BZ=F", "$", "/bbl"),
)


def fetch_market_pulse() -> MarketPulse:
    quotes: list[MarketQuote] = []
    warnings: list[str] = []

    for label, base_currency, quote_currency in FX_QUOTES:
        try:
            quotes.append(_fetch_fx_quote(label, base_currency, quote_currency))
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            warnings.append(f"{label}: {exc}")

    for label, symbol, prefix, suffix in COMMODITY_QUOTES:
        try:
            quotes.append(_fetch_yahoo_quote(label, symbol, prefix, suffix))
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            warnings.append(f"{label}: {exc}")

    return MarketPulse(quotes=quotes, warnings=warnings)


def _fetch_fx_quote(
    label: str,
    base_currency: str,
    quote_currency: str,
) -> MarketQuote:
    query = urlencode({"base": base_currency, "symbols": quote_currency})
    data = get_json(f"{FRANKFURTER_BASE_URL}?{query}")
    rate = float(data["rates"][quote_currency])
    latest_date = str(data.get("date", ""))
    change_percent = None
    try:
        previous_rate = _fetch_previous_fx_rate(
            base_currency,
            quote_currency,
            latest_date,
        )
        change_percent = _change_percent(rate, previous_rate)
    except (KeyError, TypeError, ValueError, RuntimeError):
        change_percent = None

    return MarketQuote(
        label=label,
        value=rate,
        prefix="R",
        suffix="",
        source="Frankfurter",
        as_of=latest_date,
        decimals=2,
        change_percent=change_percent,
    )


def _fetch_previous_fx_rate(
    base_currency: str,
    quote_currency: str,
    latest_date: str,
) -> float:
    end_date = datetime.strptime(latest_date, "%Y-%m-%d").date()
    start_date = end_date - timedelta(days=10)
    query = urlencode({"base": base_currency, "symbols": quote_currency})
    data = get_json(f"{FRANKFURTER_API_ROOT}/{start_date}..{end_date}?{query}")
    rates_by_date = data["rates"]
    previous_dates = sorted(date for date in rates_by_date if date < latest_date)
    if not previous_dates:
        raise ValueError("previous rate unavailable")

    previous_date = previous_dates[-1]
    return float(rates_by_date[previous_date][quote_currency])


def _fetch_yahoo_quote(
    label: str,
    symbol: str,
    prefix: str,
    suffix: str,
) -> MarketQuote:
    encoded_symbol = quote(symbol, safe="")
    data = get_json(f"{YAHOO_CHART_BASE_URL}/{encoded_symbol}?range=1d&interval=1d")
    result = data["chart"]["result"][0]
    meta = result["meta"]
    price = _first_number(
        meta.get("regularMarketPrice"),
        meta.get("previousClose"),
        meta.get("chartPreviousClose"),
    )
    previous_close = _first_number(
        meta.get("previousClose"),
        meta.get("chartPreviousClose"),
    )

    return MarketQuote(
        label=label,
        value=price,
        prefix=prefix,
        suffix=suffix,
        source="Yahoo Finance delayed futures",
        as_of=_format_market_time(meta.get("regularMarketTime")),
        decimals=2,
        change_percent=_change_percent(price, previous_close),
    )


def _change_percent(current: float, previous: float | None) -> float | None:
    if previous in {None, 0}:
        return None
    return ((current - previous) / previous) * 100


def _first_number(*values: object) -> float:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
    raise ValueError("market price unavailable")


def _format_market_time(raw_timestamp: object) -> str:
    if not isinstance(raw_timestamp, int | float):
        return ""

    return datetime.fromtimestamp(raw_timestamp, timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )
