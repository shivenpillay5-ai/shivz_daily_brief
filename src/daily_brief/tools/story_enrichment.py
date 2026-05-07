from __future__ import annotations

"""Best-effort article summary enrichment for selected news stories."""

import html
import re
from dataclasses import replace
from html.parser import HTMLParser

from daily_brief.http_client import get_text
from daily_brief.models import RankedItem


ARTICLE_FETCH_TIMEOUT_SECONDS = 6
ARTICLE_SUMMARY_MAX_CHARS = 850
MIN_SUMMARY_WORDS_BEFORE_ENRICHMENT = 35
MIN_EXTRACT_WORDS = 28


def enrich_story_summaries(items: list[RankedItem]) -> list[RankedItem]:
    """Fill thin RSS summaries from the linked article page when possible."""
    enriched: list[RankedItem] = []

    for item in items:
        if _word_count(item.summary) >= MIN_SUMMARY_WORDS_BEFORE_ENRICHMENT:
            enriched.append(item)
            continue

        try:
            article_html = get_text(
                item.url,
                timeout_seconds=ARTICLE_FETCH_TIMEOUT_SECONDS,
            )
            article_summary = extract_article_summary(article_html)
        except Exception:
            enriched.append(item)
            continue

        if _is_better_summary(article_summary, item.summary):
            enriched.append(replace(item, summary=article_summary))
        else:
            enriched.append(item)

    return enriched


def extract_article_summary(article_html: str) -> str:
    parser = _ArticleTextParser()
    parser.feed(article_html)

    paragraph_summary = _join_candidates(parser.paragraphs)
    if paragraph_summary:
        return paragraph_summary

    return _join_candidates(parser.meta_descriptions)


def _join_candidates(candidates: list[str]) -> str:
    selected: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        text = _clean_text(candidate)
        key = text.lower()
        if key in seen or not _is_useful_article_text(text):
            continue

        seen.add(key)
        selected.append(text)
        if _word_count(" ".join(selected)) >= 95:
            break

    if not selected:
        return ""

    return _shorten(" ".join(selected), ARTICLE_SUMMARY_MAX_CHARS)


def _is_better_summary(candidate: str, current: str) -> bool:
    if _word_count(candidate) < MIN_EXTRACT_WORDS:
        return False
    return len(candidate) > len(current.strip()) + 60


def _is_useful_article_text(value: str) -> bool:
    if _word_count(value) < MIN_EXTRACT_WORDS:
        return False

    lowered = value.lower()
    blocked_phrases = (
        "accept cookies",
        "advertisement",
        "all rights reserved",
        "click here",
        "cookie policy",
        "follow us",
        "newsletter",
        "privacy policy",
        "sign up",
        "subscribe",
        "terms of use",
    )
    return not any(phrase in lowered for phrase in blocked_phrases)


def _clean_text(value: str) -> str:
    unescaped = html.unescape(value)
    return " ".join(unescaped.split()).strip()


def _shorten(value: str, max_chars: int) -> str:
    value = _clean_text(value)
    if len(value) <= max_chars:
        return value

    truncated = value[: max_chars - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated}..."


def _word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


class _ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta_descriptions: list[str] = []
        self.paragraphs: list[str] = []
        self._capturing_paragraph = False
        self._paragraph_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "form", "footer", "nav"}:
            self._skip_depth += 1
            return

        if tag == "meta":
            self._record_meta(attrs)
            return

        if tag == "p" and self._skip_depth == 0:
            self._capturing_paragraph = True
            self._paragraph_parts = []

    def handle_data(self, data: str) -> None:
        if self._capturing_paragraph and self._skip_depth == 0:
            self._paragraph_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "form", "footer", "nav"}:
            self._skip_depth = max(self._skip_depth - 1, 0)
            return

        if tag == "p" and self._capturing_paragraph:
            text = _clean_text(" ".join(self._paragraph_parts))
            if text:
                self.paragraphs.append(text)
            self._capturing_paragraph = False
            self._paragraph_parts = []

    def _record_meta(self, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs if key}
        name = values.get("name", "").lower()
        property_name = values.get("property", "").lower()
        if name in {"description", "twitter:description"} or property_name in {
            "og:description",
            "twitter:description",
        }:
            content = _clean_text(values.get("content", ""))
            if content:
                self.meta_descriptions.append(content)
