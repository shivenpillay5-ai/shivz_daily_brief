from __future__ import annotations

"""News collection tool used by DailyBriefAgent."""

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from daily_brief.config import FeedConfig
from daily_brief.http_client import get_text
from daily_brief.models import FeedItem


HTML_TAG_RE = re.compile(r"<[^>]+>")


def fetch_feed_items(
    feeds: list[FeedConfig],
    category: str,
    per_feed_limit: int = 12,
) -> tuple[list[FeedItem], list[str]]:
    items: list[FeedItem] = []
    warnings: list[str] = []

    for feed in feeds:
        try:
            xml_text = get_text(feed.url)
            parsed_items = parse_feed(xml_text, source=feed.name, category=category)
            items.extend(parsed_items[:per_feed_limit])
        except Exception as exc:  # Keep one broken feed from ruining the brief.
            warnings.append(f"{feed.name}: {exc}")

    return items, warnings


def parse_feed(xml_text: str, source: str, category: str) -> list[FeedItem]:
    root = ET.fromstring(xml_text)
    if _local_name(root.tag) == "feed":
        return _parse_atom(root, source=source, category=category)
    return _parse_rss(root, source=source, category=category)


def _parse_rss(root: ET.Element, source: str, category: str) -> list[FeedItem]:
    items: list[FeedItem] = []
    for item in root.findall(".//item"):
        title = _clean_text(_find_text(item, "title"))
        url = _clean_text(_find_text(item, "link"))
        summary = _clean_text(
            _find_text(item, "description") or _find_text(item, "summary")
        )
        published = _parse_date(
            _find_text(item, "pubDate")
            or _find_text(item, "published")
            or _find_text(item, "updated")
        )

        if title and url:
            items.append(
                FeedItem(
                    title=title,
                    url=url,
                    source=source,
                    summary=summary,
                    published_at=published,
                    category=category,
                )
            )
    return items


def _parse_atom(root: ET.Element, source: str, category: str) -> list[FeedItem]:
    items: list[FeedItem] = []
    for entry in root.findall(".//{*}entry"):
        title = _clean_text(_find_text(entry, "title"))
        summary = _clean_text(_find_text(entry, "summary") or _find_text(entry, "content"))
        published = _parse_date(
            _find_text(entry, "published") or _find_text(entry, "updated")
        )
        url = _atom_link(entry)

        if title and url:
            items.append(
                FeedItem(
                    title=title,
                    url=url,
                    source=source,
                    summary=summary,
                    published_at=published,
                    category=category,
                )
            )
    return items


def _find_text(element: ET.Element, local_name: str) -> str:
    child = element.find(f"./{{*}}{local_name}")
    if child is None:
        child = element.find(local_name)
    return child.text or "" if child is not None else ""


def _atom_link(entry: ET.Element) -> str:
    links = entry.findall("./{*}link") or entry.findall("link")
    for link in links:
        rel = link.attrib.get("rel", "alternate")
        href = link.attrib.get("href", "")
        if href and rel == "alternate":
            return href.strip()
    for link in links:
        href = link.attrib.get("href", "")
        if href:
            return href.strip()
    return ""


def _clean_text(value: str) -> str:
    without_tags = HTML_TAG_RE.sub(" ", value)
    normalized = " ".join(without_tags.split())
    return html.unescape(normalized).strip()


def _parse_date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        pass

    try:
        iso_value = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(iso_value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
