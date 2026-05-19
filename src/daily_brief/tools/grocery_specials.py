from __future__ import annotations

"""Scrape grocery specials from configured retailer and catalogue pages."""

import re
from collections import defaultdict
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse

from daily_brief.config import GrocerySourceConfig, GrocerySpecialsConfig
from daily_brief.http_client import get_text
from daily_brief.models import (
    GrocerySpecial,
    GrocerySpecialsContent,
    GroceryStoreSpecials,
)


PRICE_PATTERN = re.compile(
    r"(?:ANY\s+)?\d+\s+FOR\s+(?<![A-Za-z])R\s*\d[\d\s]*(?:[,.]\d{2})?"
    r"|SAVE\s+(?<![A-Za-z])R\s*\d[\d\s]*(?:[,.]\d{2})?"
    r"|(?<![A-Za-z])R\s*\d[\d\s]*(?:[,.]\d{2})?",
    re.IGNORECASE,
)
CATALOGUE_SPECIAL_PATTERN = re.compile(
    r"(?:^|\s)(?:\d+\s+)?(?P<name>.+?)\s+"
    r"(?P<validity>\d+\s+(?:hours?|days?|weeks?))\s+"
    r"(?P<price>R\s*[\d\s]+(?:[,.]\d{2})?)"
    r"(?=\s+\d+\s+[A-Za-z0-9]|\s*$)",
    re.IGNORECASE,
)
DATE_RANGE_PATTERN = re.compile(r"\d{2}/\d{2}\s*-\s*\d{2}/\d{2}/\d{4}")
WHITESPACE_PATTERN = re.compile(r"\s+")

BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "button",
    "dd",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "option",
    "p",
    "section",
    "select",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
IGNORED_TAGS = {"script", "style", "svg", "noscript"}
ANCHOR_TAGS = {"a"}

NOISE_WORDS = {
    "about us",
    "account",
    "add catalogue",
    "advertise",
    "all offers",
    "already have an account",
    "brands",
    "buy",
    "cancel",
    "catalogues",
    "categories",
    "city",
    "compare",
    "contact us",
    "cookie policy",
    "create account",
    "download our app",
    "email address",
    "favorites",
    "filter",
    "forgotten password",
    "go to website",
    "home",
    "information",
    "latest catalogues",
    "locations",
    "login",
    "menu",
    "more",
    "most wanted",
    "my location",
    "newest",
    "notifications",
    "password",
    "popular",
    "popular choices",
    "privacy policy",
    "products",
    "register",
    "related stores",
    "reset filters",
    "results",
    "saved",
    "services",
    "show results",
    "specials",
    "stores",
    "terms and conditions",
    "trending",
    "unknown",
}
NOISE_PREFIXES = (
    "by creating an account",
    "cataloguespecials.co.za",
    "continue without",
    "download the free app",
    "enter your e-mail",
    "forgotten password",
    "is this deal",
    "log in",
    "login",
    "more info",
    "popular searches",
    "recent searches",
    "scan the qr",
    "set your location",
    "sign up",
    "something went wrong",
    "this e-mail",
    "we need your location",
    "your e-mail address",
)
PROMOTION_HINTS = (
    "buy",
    "deal",
    "for r",
    "only",
    "save",
    "special",
    "valid",
    "xtra",
)
MY_CATALOGUE_HOST = "my-catalogue.co.za"
MY_CATALOGUE_STOP_LINES = {
    "latest specials",
    "retailers - groceries",
    "retailers",
    "overview",
}
MY_CATALOGUE_HEADER_LINES = {
    "catalogue",
    "page",
    "products",
    "description",
    "price",
}


def build_grocery_specials(
    brief_date: datetime,
    config: GrocerySpecialsConfig,
) -> GrocerySpecialsContent:
    stores: list[GroceryStoreSpecials] = []
    warnings: list[str] = []
    sources_by_store = _sources_by_store(config.sources)

    for store_name, sources in sources_by_store.items():
        store_specials: list[GrocerySpecial] = []
        store_warnings: list[str] = []
        source_urls: list[str] = []

        for source in sources:
            source_urls.append(source.url)
            try:
                page_text = get_text(source.url, timeout_seconds=30)
            except RuntimeError as exc:
                store_warnings.append(f"{source.source_name}: {exc}")
                continue

            parsed = _parse_source_specials(source, page_text)
            if not parsed:
                store_warnings.append(
                    f"{source.source_name}: no clear specials were found on the page."
                )
                continue

            store_specials.extend(parsed)

        store_specials = _dedupe_specials(store_specials)
        if len(store_specials) > config.max_items_per_store:
            store_warnings.append(
                "Only the first "
                f"{config.max_items_per_store} specials are included; "
                f"{len(store_specials) - config.max_items_per_store} were clipped."
            )
            store_specials = store_specials[: config.max_items_per_store]

        stores.append(
            GroceryStoreSpecials(
                store_name=store_name,
                area=config.area,
                specials=store_specials,
                source_urls=source_urls,
                warnings=store_warnings,
            )
        )
        warnings.extend(f"{store_name}: {warning}" for warning in store_warnings)

    return GrocerySpecialsContent(
        area=config.area,
        generated_at=brief_date,
        stores=stores,
        warnings=warnings,
    )


def _sources_by_store(
    sources: list[GrocerySourceConfig],
) -> dict[str, list[GrocerySourceConfig]]:
    grouped: dict[str, list[GrocerySourceConfig]] = defaultdict(list)
    for source in sources:
        grouped[source.store_name].append(source)
    return dict(grouped)


def _parse_source_specials(
    source: GrocerySourceConfig,
    page_html: str,
) -> list[GrocerySpecial]:
    lines = _extract_visible_text_lines(page_html)
    specials: list[GrocerySpecial] = []
    host = urlparse(source.url).netloc

    if MY_CATALOGUE_HOST in host:
        specials.extend(_parse_my_catalogue_specials(source, lines))
        if specials:
            return _dedupe_specials(specials)

    if "cataloguespecials.co.za" in host:
        specials.extend(_parse_catalogue_specials(source, lines))

    specials.extend(_parse_generic_price_lines(source, lines))
    return _dedupe_specials(specials)


def _parse_catalogue_specials(
    source: GrocerySourceConfig,
    lines: list[str],
) -> list[GrocerySpecial]:
    specials: list[GrocerySpecial] = []
    for line in lines:
        for match in CATALOGUE_SPECIAL_PATTERN.finditer(line):
            item_name = _clean_item_name(match.group("name"))
            price = _normalize_price(match.group("price"))
            validity = _clean_text(match.group("validity"))
            if not _looks_like_item_name(item_name):
                continue

            specials.append(
                GrocerySpecial(
                    store_name=source.store_name,
                    item_name=item_name,
                    price=price,
                    validity=validity,
                    source_name=source.source_name,
                    source_url=source.url,
                )
            )

    return specials


def _parse_my_catalogue_specials(
    source: GrocerySourceConfig,
    lines: list[str],
) -> list[GrocerySpecial]:
    specials: list[GrocerySpecial] = []
    in_table = False
    validity = ""

    for index, line in enumerate(lines):
        lowered = line.lower()
        if lowered.startswith("products in ") and " specials" in lowered:
            in_table = True
            continue

        if not in_table:
            continue
        if lowered in MY_CATALOGUE_STOP_LINES:
            break
        if lowered in MY_CATALOGUE_HEADER_LINES:
            continue
        if DATE_RANGE_PATTERN.fullmatch(line):
            validity = line
            continue
        if not PRICE_PATTERN.fullmatch(line):
            continue

        item_name = _previous_my_catalogue_item(lines, index)
        if not _looks_like_item_name(item_name):
            continue

        specials.append(
            GrocerySpecial(
                store_name=source.store_name,
                item_name=item_name,
                price=_normalize_price(line),
                validity=validity,
                source_name=source.source_name,
                source_url=source.url,
            )
        )

    return specials


def _previous_my_catalogue_item(lines: list[str], price_index: int) -> str:
    for candidate_index in range(price_index - 1, max(-1, price_index - 6), -1):
        candidate = _clean_item_name(lines[candidate_index])
        lowered = candidate.lower()
        if not candidate:
            continue
        if lowered in MY_CATALOGUE_HEADER_LINES:
            continue
        if DATE_RANGE_PATTERN.fullmatch(candidate):
            continue
        if re.fullmatch(r"\d+", candidate):
            continue
        if PRICE_PATTERN.fullmatch(candidate):
            continue
        if _looks_like_item_name(candidate):
            return candidate
    return ""


def _parse_generic_price_lines(
    source: GrocerySourceConfig,
    lines: list[str],
) -> list[GrocerySpecial]:
    specials: list[GrocerySpecial] = []
    for index, line in enumerate(lines):
        if CATALOGUE_SPECIAL_PATTERN.search(line):
            continue
        if _is_noise_line(line) or not PRICE_PATTERN.search(line):
            continue

        price = _best_price_fragment(line)
        if not price:
            continue

        inline_name = _item_name_from_price_line(line, price)
        item_name, promotion = _choose_item_context(lines, index)
        if _looks_like_item_name(inline_name):
            item_name = inline_name

        if not _looks_like_item_name(item_name):
            continue

        if not promotion and _looks_like_promotion(line):
            promotion = _promotion_from_price_line(line, price)

        specials.append(
            GrocerySpecial(
                store_name=source.store_name,
                item_name=item_name,
                price=price,
                promotion=promotion,
                source_name=source.source_name,
                source_url=source.url,
            )
        )

    return specials


def _choose_item_context(lines: list[str], price_index: int) -> tuple[str, str]:
    promotion = ""
    for offset in range(1, 8):
        candidate_index = price_index - offset
        if candidate_index < 0:
            break

        candidate = _clean_text(lines[candidate_index])
        if not candidate or _is_noise_line(candidate) or PRICE_PATTERN.search(candidate):
            continue
        if _looks_like_promotion(candidate):
            promotion = promotion or candidate
            continue
        if _looks_like_item_name(candidate):
            return candidate, promotion

    return "", promotion


def _item_name_from_price_line(line: str, price: str) -> str:
    price_index = _price_start_index(line, price)
    if price_index <= 4:
        return ""

    candidate = _clean_item_name(line[:price_index])
    if _looks_like_promotion(candidate):
        return ""
    return candidate


def _promotion_from_price_line(line: str, price: str) -> str:
    price_index = _price_start_index(line, price)
    if price_index <= 0:
        return _clean_text(line)
    return _clean_text(line[:price_index])


def _price_start_index(line: str, price: str) -> int:
    for match in PRICE_PATTERN.finditer(line):
        if _normalize_price(match.group(0)) == price:
            return match.start()
    return line.lower().find(price.lower())


def _best_price_fragment(line: str) -> str:
    matches = [match.group(0) for match in PRICE_PATTERN.finditer(line)]
    if not matches:
        return ""

    if len(matches) == 1:
        return _normalize_price(matches[0])

    if "(" in line and ")" in line:
        return _normalize_price(matches[0])

    return _normalize_price(matches[-1])


def _extract_visible_text_lines(page_html: str) -> list[str]:
    parser = _VisibleTextParser()
    parser.feed(page_html)
    parser.close()
    return _dedupe_lines(parser.lines)


def _dedupe_specials(specials: list[GrocerySpecial]) -> list[GrocerySpecial]:
    deduped: list[GrocerySpecial] = []
    seen: set[str] = set()
    for special in specials:
        key = _dedupe_key(special)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(special)
    return deduped


def _dedupe_key(special: GrocerySpecial) -> str:
    return "|".join(
        [
            _key_text(special.store_name),
            _key_text(special.item_name),
            _key_text(special.price),
        ]
    )


def _key_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _dedupe_lines(lines: list[str]) -> list[str]:
    deduped: list[str] = []
    previous = ""
    for line in lines:
        cleaned = _clean_text(line)
        if not cleaned or cleaned == previous:
            continue
        previous = cleaned
        deduped.append(cleaned)
    return deduped


def _clean_item_name(value: str) -> str:
    cleaned = _clean_text(value)
    cleaned = re.sub(r"^\d+\s+", "", cleaned)
    cleaned = re.sub(r"^(?:Image:?\s*)+", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" -:|")
    return cleaned


def _clean_text(value: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", unescape(value)).strip()


def _normalize_price(value: str) -> str:
    cleaned = _clean_text(value).upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.replace("R ", "R")


def _is_noise_line(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    if lowered in NOISE_WORDS:
        return True
    if any(lowered.startswith(prefix) for prefix in NOISE_PREFIXES):
        return True
    if re.fullmatch(r"[\d\s*./|>-]+", lowered):
        return True
    if len(lowered) > 180 and " r " not in f" {lowered} ":
        return True
    return False


def _looks_like_item_name(value: str) -> bool:
    cleaned = _clean_item_name(value)
    lowered = cleaned.lower()
    if len(cleaned) < 4 or len(cleaned) > 140:
        return False
    if _is_noise_line(cleaned):
        return False
    if not re.search(r"[A-Za-z]", cleaned):
        return False
    if lowered.startswith(("r ", "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9")):
        return False
    return True


def _looks_like_promotion(value: str) -> bool:
    lowered = value.lower()
    return any(hint in lowered for hint in PROMOTION_HINTS)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._current_parts: list[str] = []
        self.lines: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if tag in BLOCK_TAGS or tag in ANCHOR_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in IGNORED_TAGS:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if tag in BLOCK_TAGS or tag in ANCHOR_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        cleaned = _clean_text(data)
        if cleaned:
            self._current_parts.append(cleaned)

    def close(self) -> None:
        self._flush()
        super().close()

    def _flush(self) -> None:
        if not self._current_parts:
            return
        line = _clean_text(" ".join(self._current_parts))
        self._current_parts = []
        if line:
            self.lines.append(line)
