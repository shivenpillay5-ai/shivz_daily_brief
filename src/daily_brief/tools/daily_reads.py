from __future__ import annotations

"""Short daily reading snippets for the private couple brief."""

import re
from datetime import datetime
from typing import Any

from daily_brief.http_client import get_json
from daily_brief.models import DailyFunFact, HistoryMoment


WIKIPEDIA_ON_THIS_DAY_URLS = (
    (
        "https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/"
        "{month:02d}/{day:02d}"
    ),
    (
        "https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/"
        "{month:02d}/{day:02d}"
    ),
)


HISTORY_FALLBACK_ROTATION: tuple[HistoryMoment, ...] = (
    HistoryMoment(
        title="A fair opens a doorway",
        year=1889,
        paragraph=(
            "In 1889, the Exposition Universelle opened in Paris. Its entrance"
            " arch, the Eiffel Tower, was meant as a temporary showpiece, but it"
            " became one of the world's most recognizable landmarks."
        ),
        source="Curated fallback",
    ),
    HistoryMoment(
        title="A blue marble changes the view",
        year=1972,
        paragraph=(
            "In 1972, the Apollo 17 crew photographed Earth fully lit from space."
            " The image became known as The Blue Marble and helped many people see"
            " the planet as one shared home."
        ),
        source="Curated fallback",
    ),
    HistoryMoment(
        title="A small message reshapes communication",
        year=1971,
        paragraph=(
            "In 1971, Ray Tomlinson sent one of the first networked email messages"
            " and chose the @ symbol to separate a user's name from the host"
            " computer. A tiny character became part of everyday language."
        ),
        source="Curated fallback",
    ),
    HistoryMoment(
        title="A library for the world",
        year=2001,
        paragraph=(
            "In 2001, Wikipedia began as a free, volunteer-built encyclopedia."
            " It grew from a simple experiment into one of the most consulted"
            " reference works on the internet."
        ),
        source="Curated fallback",
    ),
    HistoryMoment(
        title="A practical breakthrough in medicine",
        year=1928,
        paragraph=(
            "In 1928, Alexander Fleming noticed that a mold had killed bacteria"
            " in one of his lab dishes. That observation helped lead to penicillin,"
            " a medicine that changed modern infection treatment."
        ),
        source="Curated fallback",
    ),
    HistoryMoment(
        title="A new sound becomes public",
        year=1877,
        paragraph=(
            "In 1877, Thomas Edison demonstrated the phonograph, making it possible"
            " to record and replay sound. For the first time, voices and music"
            " could travel through time rather than only across a room."
        ),
        source="Curated fallback",
    ),
)


FUN_FACT_ROTATION: tuple[DailyFunFact, ...] = (
    DailyFunFact(
        title="Venus keeps a strange clock",
        body=(
            "A day on Venus is longer than a Venus year. The planet rotates so"
            " slowly that it takes about 243 Earth days to turn once, but only"
            " about 225 Earth days to orbit the Sun."
        ),
    ),
    DailyFunFact(
        title="Aglets are doing quiet work",
        body=(
            "The little plastic or metal tips on shoelaces are called aglets."
            " Their whole job is to stop fraying and make the lace easier to"
            " thread through the eyelets."
        ),
    ),
    DailyFunFact(
        title="The Eiffel Tower stretches",
        body=(
            "On hot days, the Eiffel Tower can grow taller by several centimetres."
            " The iron expands in heat and contracts again as temperatures fall."
        ),
    ),
    DailyFunFact(
        title="Bubble wrap had a different first pitch",
        body=(
            "Bubble wrap was originally marketed as textured wallpaper in the"
            " late 1950s. Its much better destiny turned out to be protecting"
            " fragile things in boxes."
        ),
    ),
    DailyFunFact(
        title="The dot has a name",
        body=(
            "The small dot above a lowercase i or j is called a tittle. It is"
            " one of those tiny design details that quietly keeps writing legible."
        ),
    ),
    DailyFunFact(
        title="Mars is almost on our rhythm",
        body=(
            "A Martian day, called a sol, lasts about 24 hours and 39 minutes."
            " That is close enough to Earth's day that Mars mission teams can"
            " sometimes work on Mars time."
        ),
    ),
    DailyFunFact(
        title="Nepal chose a different shape",
        body=(
            "Nepal's national flag is the only national flag that is not a"
            " rectangle or square. It is made from two stacked triangular pennants."
        ),
    ),
    DailyFunFact(
        title="Old LEGO still clicks",
        body=(
            "LEGO bricks made from 1958 onward were designed around the same"
            " coupling system, which means many old bricks can still connect with"
            " modern ones."
        ),
    ),
    DailyFunFact(
        title="Rain has a word",
        body=(
            "The earthy smell after rain is called petrichor. It comes from oils"
            " released by plants and a compound called geosmin that is lifted into"
            " the air when raindrops hit the ground."
        ),
    ),
    DailyFunFact(
        title="A coffee pot helped start webcams",
        body=(
            "One of the first webcams watched a coffee pot at the University of"
            " Cambridge. It saved people a walk when the pot was empty, which is"
            " a deeply understandable use of technology."
        ),
    ),
    DailyFunFact(
        title="The hashtag has a formal name",
        body=(
            "The # symbol is also called an octothorpe. The name became popular"
            " in telecom circles before the symbol found a second life online."
        ),
    ),
    DailyFunFact(
        title="Oxford predates a whole empire",
        body=(
            "Teaching at Oxford existed by 1096, which makes the university older"
            " than the Aztec Empire. History has some wild calendar overlaps."
        ),
    ),
)


def build_daily_history_moment(brief_date: datetime) -> HistoryMoment:
    try:
        return fetch_history_moment(brief_date)
    except Exception:
        return select_fallback_history_moment(brief_date)


def fetch_history_moment(brief_date: datetime) -> HistoryMoment:
    errors: list[str] = []
    for url_template in WIKIPEDIA_ON_THIS_DAY_URLS:
        try:
            payload = get_json(
                url_template.format(
                    month=brief_date.month,
                    day=brief_date.day,
                ),
                timeout_seconds=12,
            )
            event = _select_event(payload, brief_date)
            return _history_moment_from_event(event)
        except Exception as exc:
            errors.append(str(exc))

    raise RuntimeError("; ".join(errors) or "No on-this-day source responded")


def select_fallback_history_moment(brief_date: datetime) -> HistoryMoment:
    return HISTORY_FALLBACK_ROTATION[
        brief_date.toordinal() % len(HISTORY_FALLBACK_ROTATION)
    ]


def select_daily_fun_fact(brief_date: datetime) -> DailyFunFact:
    return FUN_FACT_ROTATION[brief_date.toordinal() % len(FUN_FACT_ROTATION)]


def _select_event(payload: dict[str, Any], brief_date: datetime) -> dict[str, Any]:
    raw_events = payload.get("selected") or payload.get("events") or []
    events = [
        event
        for event in raw_events
        if isinstance(event, dict)
        and event.get("text")
        and event.get("year") is not None
    ]
    if not events:
        raise RuntimeError("No on-this-day events were returned")
    return events[brief_date.toordinal() % len(events)]


def _history_moment_from_event(event: dict[str, Any]) -> HistoryMoment:
    text = _clean_text(str(event.get("text", "")))
    year = _parse_year(event.get("year"))
    page = _first_article_page(event)
    page_title = _page_title(page)
    title = _history_title(year, page_title, text)
    paragraph = _history_paragraph(year, text, page)
    return HistoryMoment(
        title=title,
        year=year,
        paragraph=paragraph,
        source="Wikipedia",
        source_url=_page_url(page),
    )


def _first_article_page(event: dict[str, Any]) -> dict[str, Any]:
    pages = event.get("pages") or []
    if not isinstance(pages, list):
        return {}

    for page in pages:
        if isinstance(page, dict) and page.get("extract"):
            return page
    for page in pages:
        if isinstance(page, dict):
            return page
    return {}


def _history_title(year: int | None, page_title: str, text: str) -> str:
    prefix = f"{year}: " if year is not None else ""
    if page_title:
        return f"{prefix}{page_title}"
    return f"{prefix}{_clip(text, 64)}"


def _history_paragraph(
    year: int | None,
    text: str,
    page: dict[str, Any],
) -> str:
    event_sentence = _ensure_sentence(text)
    if (
        year is not None
        and event_sentence
        and not event_sentence.lower().startswith("in ")
    ):
        event_sentence = (
            f"On this date in {year}, "
            f"{event_sentence[0].lower()}{event_sentence[1:]}"
        )

    extract_value = page.get("extract", "") if page else ""
    extract = _clean_text(str(extract_value or ""))
    extract = _clip(extract, 230)
    if extract and not _same_opening(extract, text):
        return f"{event_sentence} {extract}"
    return event_sentence


def _page_title(page: dict[str, Any]) -> str:
    titles = page.get("titles") if page else None
    if isinstance(titles, dict):
        title = titles.get("normalized") or titles.get("display")
        if title:
            return _clean_text(str(title))

    title = page.get("title") if page else ""
    return _clean_text(str(title).replace("_", " ")) if title else ""


def _page_url(page: dict[str, Any]) -> str:
    urls = page.get("content_urls") if page else None
    if not isinstance(urls, dict):
        return ""

    desktop = urls.get("desktop")
    if isinstance(desktop, dict):
        page_url = desktop.get("page")
        if page_url:
            return str(page_url)
    return ""


def _parse_year(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value: str) -> str:
    without_parentheticals = re.sub(
        r"\s*\((?:pictured|pictured today)\)",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", without_parentheticals).strip()


def _ensure_sentence(value: str) -> str:
    value = _clean_text(value)
    if not value:
        return ""
    if value[-1] in ".!?":
        return value
    return f"{value}."


def _clip(value: str, limit: int) -> str:
    value = _clean_text(value)
    if len(value) <= limit:
        return value

    sentence_boundary = value.rfind(". ", 0, limit)
    if sentence_boundary >= 80:
        return value[: sentence_boundary + 1]

    return f"{value[: limit - 3].rstrip()}..."


def _same_opening(left: str, right: str) -> bool:
    left_words = _word_prefix(left)
    right_words = _word_prefix(right)
    return bool(left_words and left_words == right_words)


def _word_prefix(value: str, words: int = 8) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", value.lower())[:words])
