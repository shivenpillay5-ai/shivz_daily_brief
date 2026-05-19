from __future__ import annotations

"""Scrape grocery specials from configured retailer and catalogue pages."""

import json
import re
from collections import defaultdict
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse

from daily_brief.config import GrocerySourceConfig, GrocerySpecialsConfig
from daily_brief.http_client import get_text
from daily_brief.models import (
    GrocerySpecial,
    GrocerySpecialsContent,
    GroceryStoreSpecials,
)


RAND_PATTERN = re.compile(r"R\s*([\d\s]+(?:[,.]\d{2})?)", re.IGNORECASE)
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
WOOLWORTHS_HOST = "woolworths.co.za"
CATEGORY_RULES = (
    (
        "Meat & Protein",
        (
            "bacon",
            "beef",
            "chicken",
            "egg",
            "fish",
            "mince",
            "mussel",
            "pork",
            "protein",
            "steak",
            "t-bone",
        ),
    ),
    (
        "Fresh Produce",
        (
            "apple",
            "avocado",
            "banana",
            "blueberr",
            "cabbage",
            "carrot",
            "citrus",
            "clemengold",
            "cucumber",
            "fruit",
            "grape",
            "lettuce",
            "mandarin",
            "orange",
            "pepper",
            "potato",
            "salad",
            "sweetcorn",
            "tomato",
            "vegetable",
        ),
    ),
    (
        "Pantry Staples",
        (
            "bran",
            "canola",
            "cereal",
            "coffee",
            "corn flakes",
            "flour",
            "maize",
            "oil",
            "pasta",
            "rice",
            "sugar",
        ),
    ),
    (
        "Bakery",
        (
            "bakery",
            "bread",
            "bun",
            "cupcake",
            "roll",
            "sourdough",
        ),
    ),
    (
        "Dairy & Eggs",
        (
            "butter",
            "cheddar",
            "cheese",
            "cream",
            "custard",
            "dairy",
            "gouda",
            "milk",
            "mozzarella",
            "ricotta",
            "yoghurt",
        ),
    ),
    (
        "Cleaning & Household",
        (
            "battery",
            "clean",
            "detergent",
            "dishwash",
            "laundry",
            "omo",
            "toilet",
            "washing powder",
        ),
    ),
    (
        "Baby & Pets",
        (
            "baby",
            "cat",
            "dog",
            "husky",
            "johnson",
            "pet",
            "whiskas",
        ),
    ),
    (
        "Drinks",
        (
            "beer",
            "coca",
            "cold drink",
            "drink",
            "gin",
            "juice",
            "water",
            "wine",
        ),
    ),
    (
        "Home & General",
        (
            "ladder",
            "microwave",
            "oven",
        ),
    ),
)
CATEGORY_WEIGHTS = {
    "Meat & Protein": 42,
    "Pantry Staples": 38,
    "Fresh Produce": 35,
    "Cleaning & Household": 34,
    "Dairy & Eggs": 32,
    "Baby & Pets": 28,
    "Bakery": 24,
    "Drinks": 18,
    "Home & General": 8,
    "Treats & Snacks": 12,
    "Other": 5,
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
        image_cache: dict[str, str] = {}

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
        store_specials = _enrich_store_product_images(store_specials, image_cache)
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

    if WOOLWORTHS_HOST in host:
        specials.extend(_parse_woolworths_specials(source, page_html))
        if specials:
            return _dedupe_specials(specials)

    if MY_CATALOGUE_HOST in host:
        specials.extend(_parse_my_catalogue_specials(source, page_html))
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
                _enrich_special(
                    GrocerySpecial(
                    store_name=source.store_name,
                    item_name=item_name,
                    price=price,
                    validity=validity,
                    source_name=source.source_name,
                    source_url=source.url,
                    )
                )
            )

    return specials


def _parse_my_catalogue_specials(
    source: GrocerySourceConfig,
    page_html: str,
) -> list[GrocerySpecial]:
    table_html = _monitoring_table_html(page_html)
    if not table_html:
        return []

    specials: list[GrocerySpecial] = []
    current_image_url = ""
    current_validity = ""
    current_catalogue_url = source.url

    for row_html in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table_html, re.IGNORECASE | re.DOTALL):
        cells = re.findall(r"<td\b([^>]*)>(.*?)</td>", row_html, re.IGNORECASE | re.DOTALL)
        if not cells:
            continue

        data_cells: list[tuple[str, str]] = []
        for attrs, cell_html in cells:
            attrs_lower = attrs.lower()
            if "image-cell" in attrs_lower:
                image_url = _extract_first_attr(cell_html, "img", "src")
                href = _extract_first_attr(cell_html, "a", "href")
                validity = _first_tag_text(cell_html, "span")
                current_image_url = _catalogue_image_url(
                    urljoin(source.url, image_url)
                )
                current_catalogue_url = urljoin(source.url, href) if href else source.url
                current_validity = validity or current_validity
                continue

            text = _clean_text(_strip_html(cell_html))
            if DATE_RANGE_PATTERN.fullmatch(text):
                current_validity = text
            elif text:
                data_cells.append((text, _extract_first_attr(cell_html, "a", "href")))

        if len(data_cells) < 3:
            continue
        if not PRICE_PATTERN.fullmatch(data_cells[-1][0]):
            continue
        item_name = _clean_item_name(data_cells[-2][0])
        product_group = _clean_text(data_cells[-3][0])
        product_url = urljoin(source.url, data_cells[-3][1]) if data_cells[-3][1] else ""
        if not _looks_like_item_name(item_name):
            continue

        special = _enrich_special(
            GrocerySpecial(
                store_name=source.store_name,
                item_name=item_name,
                price=_normalize_price(data_cells[-1][0]),
                validity=current_validity,
                source_name=source.source_name,
                source_url=source.url,
                category=_classify_category(item_name, product_group),
                product_url=product_url,
                catalogue_url=current_catalogue_url,
            )
        )
        specials.append(special)

    return specials


def _parse_woolworths_specials(
    source: GrocerySourceConfig,
    page_html: str,
) -> list[GrocerySpecial]:
    specials: list[GrocerySpecial] = []
    for record in _extract_woolworths_records(page_html):
        attrs = record.get("attributes", {})
        item_name = _clean_item_name(str(attrs.get("p_displayName", "")))
        if not _looks_like_item_name(item_name):
            continue

        price_info = _woolworths_price_info(record.get("startingPrice", {}))
        if not price_info:
            continue

        price, regular_price, saving_amount, saving_percent, unit_price = price_info
        detail_url = urljoin(source.url, str(attrs.get("detailPageURL", "")))
        category = _classify_category(
            item_name,
            str(attrs.get("p_defaultCategoryName", "")),
        )
        special = _enrich_special(
            GrocerySpecial(
                store_name=source.store_name,
                item_name=item_name,
                price=price,
                promotion=_promotion_from_detail_url(detail_url),
                source_name=source.source_name,
                source_url=source.url,
                category=category,
                image_url=str(attrs.get("p_externalImageReference", "")),
                product_url=detail_url,
                catalogue_url=detail_url,
                regular_price=regular_price,
                saving_amount=saving_amount,
                saving_percent=saving_percent,
                unit_price=unit_price,
            )
        )
        specials.append(special)

    return specials


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
            _enrich_special(
                GrocerySpecial(
                store_name=source.store_name,
                item_name=item_name,
                price=price,
                promotion=promotion,
                source_name=source.source_name,
                source_url=source.url,
                )
            )
        )

    return specials


def _monitoring_table_html(page_html: str) -> str:
    start = page_html.find('<table class="table monitoring-products-table">')
    if start == -1:
        return ""
    end = page_html.find("</table>", start)
    if end == -1:
        return ""
    return page_html[start : end + len("</table>")]


def _extract_woolworths_records(page_html: str) -> list[dict]:
    all_records: list[dict] = []
    search_from = 0
    while True:
        marker_index = page_html.find('"records":', search_from)
        if marker_index == -1:
            break
        array_start = page_html.find("[", marker_index)
        if array_start == -1:
            break
        array_text = _extract_json_array(page_html, array_start)
        search_from = array_start + max(1, len(array_text))
        if not array_text:
            continue
        try:
            records = json.loads(array_text)
        except json.JSONDecodeError:
            continue
        if isinstance(records, list):
            all_records.extend(record for record in records if isinstance(record, dict))

    return all_records


def _extract_json_array(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return ""


def _woolworths_price_info(
    starting_price: object,
) -> tuple[str, str, str, float | None, str] | None:
    if not isinstance(starting_price, dict):
        return None

    price_values: list[float] = []
    unit_price = ""
    for key, value in starting_price.items():
        if not isinstance(value, (int, float)) or value <= 0:
            continue
        if key.endswith("_wp"):
            continue
        if "kilogramPrice" in key:
            unit_price = unit_price or f"{_format_rand(float(value))}/kg"
            continue
        price_values.append(float(value))

    if not price_values:
        return None

    current = min(price_values)
    regular = max(price_values)
    saving = regular - current
    saving_percent = (saving / regular * 100) if saving > 0 and regular > 0 else None
    return (
        _format_rand(current),
        _format_rand(regular) if saving > 0.01 else "",
        _format_rand(saving) if saving > 0.01 else "",
        round(saving_percent, 1) if saving_percent is not None else None,
        unit_price,
    )


def _promotion_from_detail_url(detail_url: str) -> str:
    parts = [unquote(part) for part in urlparse(detail_url).path.split("/") if part]
    for index, part in enumerate(parts):
        normalized = part.replace("-", " ")
        lowered = normalized.lower()
        if "save" in lowered or lowered.startswith("buy"):
            return normalized
        if part == "Promotions" and index + 1 < len(parts):
            return parts[index + 1].replace("-", " ")
    return ""


def _enrich_special(special: GrocerySpecial) -> GrocerySpecial:
    category = special.category or _classify_category(special.item_name, "")
    score = special.deal_score or _deal_score(
        item_name=special.item_name,
        category=category,
        saving_percent=special.saving_percent,
        promotion=special.promotion,
        price=special.price,
    )
    return GrocerySpecial(
        store_name=special.store_name,
        item_name=special.item_name,
        price=special.price,
        promotion=special.promotion,
        validity=special.validity,
        source_name=special.source_name,
        source_url=special.source_url,
        category=category,
        image_url=special.image_url,
        product_url=special.product_url,
        catalogue_url=special.catalogue_url,
        regular_price=special.regular_price,
        saving_amount=special.saving_amount,
        saving_percent=special.saving_percent,
        unit_price=special.unit_price,
        deal_score=score,
    )


def _classify_category(item_name: str, source_category: str) -> str:
    haystack = f"{item_name} {source_category}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category
    if any(word in haystack for word in ("chocolate", "snack", "sweet", "biscuit")):
        return "Treats & Snacks"
    return "Other"


def _deal_score(
    item_name: str,
    category: str,
    saving_percent: float | None,
    promotion: str,
    price: str,
) -> int:
    lowered = f"{item_name} {promotion}".lower()
    score = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS["Other"])
    if saving_percent is not None:
        score += min(45, int(saving_percent * 1.8))
    if any(word in lowered for word in ("bulk", "2kg", "5 l", "5l", "10kg", "30s")):
        score += 12
    if any(word in lowered for word in ("buy any", "save", "combo", "assorted")):
        score += 8
    amount = _price_amount(price)
    if amount is not None and 20 <= amount <= 150:
        score += 6
    return score


def _enrich_store_product_images(
    specials: list[GrocerySpecial],
    image_cache: dict[str, str],
) -> list[GrocerySpecial]:
    ranked_for_images = {
        id(special)
        for special in sorted(
            specials,
            key=lambda item: item.deal_score,
            reverse=True,
        )[:32]
        if special.product_url and MY_CATALOGUE_HOST in urlparse(special.product_url).netloc
    }

    enriched: list[GrocerySpecial] = []
    for special in specials:
        if id(special) not in ranked_for_images:
            enriched.append(special)
            continue
        image_url = _my_catalogue_product_image(special, image_cache)
        if not image_url:
            enriched.append(special)
            continue
        enriched.append(
            GrocerySpecial(
                store_name=special.store_name,
                item_name=special.item_name,
                price=special.price,
                promotion=special.promotion,
                validity=special.validity,
                source_name=special.source_name,
                source_url=special.source_url,
                category=special.category,
                image_url=image_url,
                product_url=special.product_url,
                catalogue_url=special.catalogue_url,
                regular_price=special.regular_price,
                saving_amount=special.saving_amount,
                saving_percent=special.saving_percent,
                unit_price=special.unit_price,
                deal_score=special.deal_score,
            )
        )
    return enriched


def _my_catalogue_product_image(
    special: GrocerySpecial,
    image_cache: dict[str, str],
) -> str:
    cache_key = f"{special.store_name}|{special.product_url}|{special.item_name}|{special.price}"
    if cache_key in image_cache:
        return image_cache[cache_key]

    try:
        page_html = get_text(special.product_url, timeout_seconds=12)
    except RuntimeError:
        image_cache[cache_key] = ""
        return ""

    image_url = _extract_product_image_from_my_catalogue_page(page_html, special)
    image_cache[cache_key] = image_url
    return image_url


def _extract_product_image_from_my_catalogue_page(
    page_html: str,
    special: GrocerySpecial,
) -> str:
    expected_store = _normalize_lookup_text(special.store_name).replace("hypermarket", "")
    expected_item = _normalize_lookup_text(special.item_name)
    expected_price = _normalize_price(special.price)

    for row_html in re.findall(r"<tr\b[^>]*>(.*?)</tr>", page_html, re.IGNORECASE | re.DOTALL):
        row_text = _normalize_lookup_text(_strip_html(row_html))
        if expected_store not in row_text:
            continue
        if expected_item not in row_text:
            continue
        if expected_price and _normalize_price(_clean_text(_strip_html(row_html))) and expected_price not in _normalize_price(_clean_text(_strip_html(row_html))):
            continue

        for img_html in re.findall(r"<img\b[^>]*>", row_html, re.IGNORECASE | re.DOTALL):
            alt = _clean_text(_extract_attr_from_tag(img_html, "alt"))
            src = _extract_attr_from_tag(img_html, "src")
            lowered_alt = alt.lower()
            if not src or "logo" in lowered_alt or "close" in lowered_alt:
                continue
            if not _looks_like_product_image_src(src):
                continue
            if alt and _normalize_lookup_text(alt) not in row_text:
                continue
            return _catalogue_image_url(urljoin(special.product_url, src))

    return ""


def _normalize_lookup_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", unescape(value).lower()).strip()


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def _extract_first_attr(value: str, tag_name: str, attr_name: str) -> str:
    pattern = (
        rf"<{tag_name}\b[^>]*\b{attr_name}="
        rf"(?P<quote>['\"])(?P<value>.*?)(?P=quote)"
    )
    match = re.search(pattern, value, re.IGNORECASE | re.DOTALL)
    return unescape(match.group("value")) if match else ""


def _extract_attr_from_tag(tag_html: str, attr_name: str) -> str:
    pattern = rf"\b{attr_name}=(?P<quote>['\"])(?P<value>.*?)(?P=quote)"
    match = re.search(pattern, tag_html, re.IGNORECASE | re.DOTALL)
    return unescape(match.group("value")) if match else ""


def _first_tag_text(value: str, tag_name: str) -> str:
    match = re.search(
        rf"<{tag_name}\b[^>]*>(.*?)</{tag_name}>",
        value,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    return _clean_text(_strip_html(match.group(1)))


def _catalogue_image_url(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"-\d+-\d+(\.[A-Za-z0-9]+)$", r"-1080-1080\1", value)


def _looks_like_product_image_src(value: str) -> bool:
    filename = urlparse(value).path.rsplit("/", 1)[-1]
    stem = filename.rsplit(".", 1)[0]
    return bool(re.search(r"[A-Za-z]", stem))


def _format_rand(value: float) -> str:
    return f"R{value:.2f}"


def _price_amount(value: str) -> float | None:
    match = RAND_PATTERN.search(value)
    if not match:
        return None
    normalized = match.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


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
