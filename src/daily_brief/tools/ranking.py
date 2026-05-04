from __future__ import annotations

"""Story ranking tool used by DailyBriefAgent."""

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

from daily_brief.config import AppConfig
from daily_brief.http_client import post_json
from daily_brief.models import FeedItem, RankedItem
from daily_brief.prompts.ranking_prompt import RANKING_INSTRUCTIONS, build_ranking_input


RESPONSES_API_URL = "https://api.openai.com/v1/responses"


def rank_items(
    items: list[FeedItem],
    category_name: str,
    top_n: int,
    config: AppConfig,
    use_openai: bool = True,
) -> list[RankedItem]:
    deduped = _deduplicate(items)
    if not deduped:
        return []

    if use_openai and config.openai_api_key:
        try:
            return _rank_with_openai(deduped, category_name, top_n, config)
        except Exception as exc:
            print(f"OpenAI ranking failed for {category_name}; using fallback. {exc}")

    return _fallback_rank(deduped, top_n)


def _rank_with_openai(
    items: list[FeedItem],
    category_name: str,
    top_n: int,
    config: AppConfig,
) -> list[RankedItem]:
    candidates = [
        {
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "summary": item.summary[:500],
            "published_at": item.published_at.isoformat() if item.published_at else None,
        }
        for item in items[:40]
    ]
    candidate_urls = {item["url"] for item in candidates}
    payload = {
        "model": config.openai_model,
        "instructions": RANKING_INSTRUCTIONS,
        "input": build_ranking_input(
            category_name=category_name,
            top_n=min(top_n, len(candidates)),
            candidates_json=json.dumps(candidates, ensure_ascii=True, indent=2),
        ),
        "max_output_tokens": 2000,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "ranked_daily_brief_stories",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "stories": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "source": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                                "required": ["title", "url", "source", "summary"],
                            },
                        }
                    },
                    "required": ["stories"],
                },
            }
        },
    }
    response = post_json(
        RESPONSES_API_URL,
        payload=payload,
        headers={"Authorization": f"Bearer {config.openai_api_key}"},
    )
    output_text = _extract_output_text(response)
    data = json.loads(output_text)
    ranked: list[RankedItem] = []
    item_by_url = {item.url: item for item in items}

    for story in data.get("stories", []):
        url = str(story.get("url", "")).strip()
        if url not in candidate_urls:
            continue
        original = item_by_url.get(url)
        title = str(story.get("title") or (original.title if original else "")).strip()
        source = str(story.get("source") or (original.source if original else "")).strip()
        summary = str(
            story.get("summary") or (original.summary if original else "")
        ).strip()
        ranked.append(
            RankedItem(
                title=title,
                url=url,
                source=source,
                summary=summary,
                published_at=original.published_at if original else None,
            )
        )
        if len(ranked) == top_n:
            break

    if not ranked:
        raise RuntimeError("The model returned no usable stories.")

    return ranked


def _fallback_rank(items: list[FeedItem], top_n: int) -> list[RankedItem]:
    now = datetime.now(timezone.utc)

    def score(item: FeedItem) -> tuple[int, float, str]:
        published = item.published_at
        if published is None:
            freshness = 0.0
        else:
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age_hours = max((now - published.astimezone(timezone.utc)).total_seconds() / 3600, 0)
            freshness = max(72 - age_hours, 0)

        has_summary = 1 if item.summary else 0
        return (has_summary, freshness, item.title)

    sorted_items = sorted(items, key=score, reverse=True)
    source_buckets: dict[str, list[FeedItem]] = defaultdict(list)
    for item in sorted_items:
        source_buckets[item.source].append(item)

    source_order = sorted(
        source_buckets,
        key=lambda source: score(source_buckets[source][0]),
        reverse=True,
    )

    diversified: list[FeedItem] = []
    while len(diversified) < top_n and source_order:
        next_order: list[str] = []
        for source in source_order:
            bucket = source_buckets[source]
            if bucket and len(diversified) < top_n:
                diversified.append(bucket.pop(0))
            if bucket:
                next_order.append(source)
        source_order = next_order

    return [
        RankedItem(
            title=item.title,
            url=item.url,
            source=item.source,
            summary=item.summary or "Read the linked story for details.",
            published_at=item.published_at,
        )
        for item in diversified
    ]


def _deduplicate(items: list[FeedItem]) -> list[FeedItem]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    deduped: list[FeedItem] = []

    for item in items:
        normalized_url = _normalize_url(item.url)
        normalized_title = _normalize_title(item.title)
        if normalized_url in seen_urls or normalized_title in seen_titles:
            continue

        seen_urls.add(normalized_url)
        seen_titles.add(normalized_title)
        deduped.append(item)

    return deduped


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.netloc.lower()}{parsed.path.rstrip('/')}"


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


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
