from __future__ import annotations

"""Render grocery specials to useful email and visual PDF shopping guides."""

import html
import math
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from daily_brief.http_client import get_bytes
from daily_brief.models import (
    GrocerySpecial,
    GrocerySpecialsContent,
    GroceryStoreSpecials,
)


PDF_PAGE_WIDTH = 595
PDF_PAGE_HEIGHT = 842
PDF_MARGIN = 34
PDF_TOP = 800
PDF_BOTTOM = 42
EMAIL_CARD_LIMIT = 8
CATEGORY_LIMIT = 5
PDF_CARD_LIMIT = 32

STORE_COLORS = {
    "Woolworths": ("#1f2933", "#eef7f0"),
    "Checkers": ("#d71920", "#fff1f1"),
    "Pick n Pay": ("#005baa", "#eef5ff"),
}
CATEGORY_COLORS = {
    "Meat & Protein": "#7f1d1d",
    "Fresh Produce": "#166534",
    "Pantry Staples": "#92400e",
    "Cleaning & Household": "#1d4ed8",
    "Dairy & Eggs": "#6d28d9",
    "Bakery": "#9a3412",
    "Baby & Pets": "#0f766e",
    "Drinks": "#0369a1",
    "Home & General": "#374151",
    "Treats & Snacks": "#be185d",
    "Other": "#4b5563",
}


def render_grocery_text(
    brief_date: datetime,
    content: GrocerySpecialsContent,
) -> str:
    top_deals = _top_specials(content, 12)
    lines = [
        f"Midrand Grocery Specials - {brief_date:%A, %d %B %Y}",
        f"Area: {content.area}",
        "",
        "Best buys",
    ]

    if top_deals:
        lines.extend(_special_text_line(special) for special in top_deals)
    else:
        lines.append("No specials could be extracted cleanly.")

    lines.extend(["", "Store readout"])
    for store in content.stores:
        lines.append(
            f"{store.store_name}: {len(store.specials)} specials"
            f" | worth checking for {_top_categories_text(store.specials)}"
        )
        if store.warnings:
            lines.append("Notes: " + " | ".join(store.warnings))

    if content.warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"- {warning}" for warning in content.warnings)

    lines.extend(
        [
            "",
            "Attached PDFs include a month-end shopping pack and store guides.",
            "Prices and availability can change by branch.",
        ]
    )
    return "\n".join(lines)


def render_grocery_html(
    brief_date: datetime,
    content: GrocerySpecialsContent,
) -> str:
    top_deals = _top_specials(content, EMAIL_CARD_LIMIT)
    category_sections = "\n".join(
        _category_section_html(category, specials[:4])
        for category, specials in _category_groups(top_deals or _all_specials(content)).items()
        if specials
    )
    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f5f1ea;font-family:Segoe UI,Arial,sans-serif;color:#1f2933">
    <div style="display:none;max-height:0;overflow:hidden;color:#f5f1ea">
      Your month-end grocery specials pack for {html.escape(content.area)}.
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f1ea">
      <tr>
        <td align="center" style="padding:26px 12px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:880px;background:#fffdf8;border-radius:18px;overflow:hidden;border:1px solid #e6ded1">
            <tr>
              <td style="padding:30px 34px;background:#183b35;color:#ffffff">
                <div style="font-size:12px;text-transform:uppercase;letter-spacing:.8px;font-weight:800;color:#bde7d4">Household buying guide</div>
                <h1 style="font-size:32px;line-height:1.1;margin:10px 0 0">Midrand Grocery Specials</h1>
                <p style="margin:12px 0 0;font-size:15px;line-height:1.5;color:#edf8f2">
                  A practical month-end view of where the strongest specials are,
                  with product images where the sources expose them.
                </p>
                <p style="margin:12px 0 0;font-size:13px;color:#cfe6dc">
                  {brief_date:%A, %d %B %Y} | {html.escape(content.area)}
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 34px 30px">
                {_stats_html(content)}
                {_store_cards_html(content)}
                {_section_heading_html("Best buys first", "Start here before opening the full attachments.")}
                {_deal_grid_html(top_deals)}
                {_section_heading_html("Shop by household need", "Grouped so planning the basket is easier.")}
                {category_sections}
                {_warnings_html(content.warnings)}
                <p style="margin:26px 0 0;color:#687782;font-size:12px;text-align:center">
                  Attached: a month-end shopping pack plus store-specific guides.
                  Prices, branch participation, and loyalty-card rules can change.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def write_grocery_store_pdfs(
    brief_date: datetime,
    content: GrocerySpecialsContent,
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    pack_path = output_dir / f"{brief_date:%Y-%m-%d}-month-end-grocery-pack.pdf"
    _write_shopping_pack_pdf(pack_path, brief_date, content)
    paths.append(pack_path)

    for store in content.stores:
        filename = f"{brief_date:%Y-%m-%d}-{_slugify(store.store_name)}-specials.pdf"
        path = output_dir / filename
        _write_store_pdf(path, brief_date, content.area, store)
        paths.append(path)

    return paths


def _stats_html(content: GrocerySpecialsContent) -> str:
    total = len(_all_specials(content))
    categories = len(_category_groups(_all_specials(content)))
    stores = len([store for store in content.stores if store.specials])
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 22px">
      <tr>
        {_stat_cell_html(str(total), "specials found")}
        {_stat_cell_html(str(stores), "stores with deals")}
        {_stat_cell_html(str(categories), "basket categories")}
      </tr>
    </table>"""


def _stat_cell_html(value: str, label: str) -> str:
    return f"""
    <td width="33.33%" style="padding:0 6px 0 0">
      <div style="background:#f1eadf;border:1px solid #e1d5c5;border-radius:10px;padding:14px 12px;text-align:center">
        <div style="font-size:24px;font-weight:900;color:#183b35">{html.escape(value)}</div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#6b5f53;font-weight:800">{html.escape(label)}</div>
      </div>
    </td>"""


def _store_cards_html(content: GrocerySpecialsContent) -> str:
    cards = "".join(_store_card_html(store) for store in content.stores)
    return f"""
    {_section_heading_html("Where to shop", "Each store's strongest basket areas at a glance.")}
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 18px">
      <tr>{cards}</tr>
    </table>"""


def _store_card_html(store: GroceryStoreSpecials) -> str:
    color, tint = STORE_COLORS.get(store.store_name, ("#183b35", "#eef7f0"))
    best = _top_categories_text(store.specials)
    return f"""
    <td width="33.33%" valign="top" style="padding:0 8px 12px 0">
      <div style="background:{tint};border:1px solid #e1d5c5;border-radius:12px;overflow:hidden">
        <div style="height:6px;background:{color}"></div>
        <div style="padding:14px 13px">
          <div style="font-size:16px;font-weight:900;color:{color}">{html.escape(store.store_name)}</div>
          <div style="font-size:26px;font-weight:900;color:#1f2933;margin-top:7px">{len(store.specials)}</div>
          <div style="font-size:11px;color:#6b7280;text-transform:uppercase;font-weight:800">specials</div>
          <p style="font-size:12px;line-height:1.4;color:#374151;margin:9px 0 0">
            Worth checking for: {html.escape(best)}
          </p>
        </div>
      </div>
    </td>"""


def _section_heading_html(title: str, subtitle: str) -> str:
    return f"""
    <div style="margin:24px 0 12px">
      <h2 style="font-size:21px;line-height:1.2;margin:0;color:#183b35">{html.escape(title)}</h2>
      <p style="font-size:13px;line-height:1.4;margin:5px 0 0;color:#69746f">{html.escape(subtitle)}</p>
    </div>"""


def _deal_grid_html(specials: list[GrocerySpecial]) -> str:
    if not specials:
        return """<p style="margin:0;color:#687782">No specials could be extracted cleanly.</p>"""

    rows = []
    for index in range(0, len(specials), 2):
        left = _deal_card_html(specials[index])
        right = _deal_card_html(specials[index + 1]) if index + 1 < len(specials) else ""
        rows.append(f"<tr>{left}{right}</tr>")

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
      {''.join(rows)}
    </table>"""


def _deal_card_html(special: GrocerySpecial) -> str:
    color, tint = STORE_COLORS.get(special.store_name, ("#183b35", "#eef7f0"))
    category_color = CATEGORY_COLORS.get(special.category, CATEGORY_COLORS["Other"])
    image_html = _email_image_html(special)
    savings = _savings_html(special)
    meta = _special_meta(special)
    return f"""
    <td width="50%" valign="top" style="padding:0 8px 12px 0">
      <div style="background:#ffffff;border:1px solid #e4dccf;border-radius:12px;overflow:hidden">
        <div style="padding:12px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
              <td width="104" valign="top">{image_html}</td>
              <td valign="top" style="padding-left:12px">
                <div style="display:inline-block;background:{tint};color:{color};border-radius:999px;padding:4px 8px;font-size:10px;font-weight:900;text-transform:uppercase">
                  {html.escape(special.store_name)}
                </div>
                <div style="display:inline-block;background:#f3f4f6;color:{category_color};border-radius:999px;padding:4px 8px;font-size:10px;font-weight:900;text-transform:uppercase;margin-left:4px">
                  {html.escape(special.category or "Other")}
                </div>
                <h3 style="font-size:15px;line-height:1.25;margin:9px 0 8px;color:#1f2933">{html.escape(special.item_name)}</h3>
                <div style="font-size:23px;font-weight:900;color:{color};line-height:1">{html.escape(special.price)}</div>
                {savings}
                <p style="font-size:11px;line-height:1.35;margin:8px 0 0;color:#69746f">{html.escape(meta)}</p>
              </td>
            </tr>
          </table>
        </div>
      </div>
    </td>"""


def _email_image_html(special: GrocerySpecial) -> str:
    if special.image_url:
        return (
            f'<img src="{html.escape(special.image_url, quote=True)}" '
            f'alt="{html.escape(special.item_name, quote=True)}" width="104" '
            'style="display:block;width:104px;height:104px;object-fit:contain;'
            'background:#f7f4ee;border-radius:10px;border:1px solid #eadfce">'
        )
    label = special.category or "Deal"
    return f"""
    <div style="width:104px;height:104px;background:#f1eadf;border:1px solid #eadfce;border-radius:10px;text-align:center">
      <div style="font-size:11px;color:#6b5f53;font-weight:800;padding:38px 8px 0">{html.escape(label)}</div>
    </div>"""


def _savings_html(special: GrocerySpecial) -> str:
    parts = []
    if special.regular_price:
        parts.append(f"Was {special.regular_price}")
    if special.saving_amount:
        parts.append(f"Save {special.saving_amount}")
    if special.saving_percent is not None:
        parts.append(f"{special.saving_percent:.0f}% off")
    if special.unit_price:
        parts.append(special.unit_price)
    if not parts:
        return ""
    return f"""
    <div style="font-size:11px;line-height:1.4;color:#4b5563;margin-top:5px">
      {html.escape(' | '.join(parts))}
    </div>"""


def _category_section_html(category: str, specials: list[GrocerySpecial]) -> str:
    if not specials:
        return ""
    rows = "".join(_compact_special_row_html(special) for special in specials)
    return f"""
    <div style="margin:0 0 16px;border:1px solid #e4dccf;border-radius:12px;overflow:hidden;background:#ffffff">
      <div style="padding:10px 13px;background:#f1eadf;color:{CATEGORY_COLORS.get(category, '#4b5563')};font-weight:900;font-size:14px">
        {html.escape(category)}
      </div>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0">{rows}</table>
    </div>"""


def _compact_special_row_html(special: GrocerySpecial) -> str:
    return f"""
    <tr>
      <td style="padding:9px 12px;border-top:1px solid #eee5d8;font-size:13px;line-height:1.35">{html.escape(special.item_name)}</td>
      <td style="padding:9px 12px;border-top:1px solid #eee5d8;font-size:12px;color:#6b7280">{html.escape(special.store_name)}</td>
      <td align="right" style="padding:9px 12px;border-top:1px solid #eee5d8;font-size:14px;font-weight:900;color:#183b35;white-space:nowrap">{html.escape(special.price)}</td>
    </tr>"""


def _warnings_html(warnings: list[str]) -> str:
    if not warnings:
        return ""
    items = "".join(f"<li>{html.escape(warning)}</li>" for warning in warnings)
    return f"""
    <div style="margin:20px 0 0;padding:12px 14px;background:#fff7e6;border:1px solid #f2d399;border-radius:8px;color:#5f4b1b;font-size:12px;line-height:1.45">
      <strong>Notes</strong>
      <ul style="margin:6px 0 0 18px;padding:0">{items}</ul>
    </div>"""


def _write_shopping_pack_pdf(
    path: Path,
    brief_date: datetime,
    content: GrocerySpecialsContent,
) -> None:
    pdf = _PdfBuilder()
    page = pdf.new_page()
    y = _draw_pdf_header(
        page,
        "Month-End Grocery Specials Pack",
        f"{content.area} | {brief_date:%A, %d %B %Y}",
        "#183b35",
    )
    y = _draw_pdf_store_summary(page, content, y)
    y = _draw_pdf_section_title(page, "Best buys across the basket", y)
    page, y = _draw_pdf_cards(page, pdf, _top_specials(content, 10), y)

    category_groups = _category_groups(_all_specials(content))
    for category, specials in category_groups.items():
        if y < 210:
            page = pdf.new_page()
            y = _draw_pdf_header(page, "Month-End Grocery Specials Pack", category, "#183b35")
        y = _draw_pdf_section_title(page, category, y)
        y = _draw_pdf_compact_rows(page, specials[:CATEGORY_LIMIT], y)

    pdf.write(path)


def _write_store_pdf(
    path: Path,
    brief_date: datetime,
    area: str,
    store: GroceryStoreSpecials,
) -> None:
    color = STORE_COLORS.get(store.store_name, ("#183b35", "#eef7f0"))[0]
    pdf = _PdfBuilder()
    page = pdf.new_page()
    y = _draw_pdf_header(
        page,
        f"{store.store_name} Specials",
        f"{area} | {brief_date:%A, %d %B %Y}",
        color,
    )
    y = _draw_pdf_store_intro(page, store, y, color)
    y = _draw_pdf_section_title(page, "Best store picks", y)
    ranked = sorted(store.specials, key=lambda special: special.deal_score, reverse=True)
    page, y = _draw_pdf_cards(page, pdf, ranked[:PDF_CARD_LIMIT], y, color=color)

    if store.warnings:
        if y < 120:
            page = pdf.new_page()
            y = _draw_pdf_header(page, f"{store.store_name} Specials", "Notes", color)
        y = _draw_pdf_section_title(page, "Notes", y)
        for warning in store.warnings:
            y = page.draw_wrapped_text(f"- {warning}", PDF_MARGIN, y, 10, "#5f4b1b", 88)

    pdf.write(path)


def _draw_pdf_header(
    page: "_PdfPage",
    title: str,
    subtitle: str,
    color: str,
) -> float:
    page.rect(0, PDF_PAGE_HEIGHT - 118, PDF_PAGE_WIDTH, 118, color)
    page.text(title, PDF_MARGIN, PDF_PAGE_HEIGHT - 58, 22, "#ffffff", bold=True)
    page.text(subtitle, PDF_MARGIN, PDF_PAGE_HEIGHT - 82, 11, "#d8efe5")
    return PDF_PAGE_HEIGHT - 148


def _draw_pdf_store_summary(
    page: "_PdfPage",
    content: GrocerySpecialsContent,
    y: float,
) -> float:
    card_w = (PDF_PAGE_WIDTH - PDF_MARGIN * 2 - 16) / 3
    for index, store in enumerate(content.stores[:3]):
        x = PDF_MARGIN + index * (card_w + 8)
        color, tint = STORE_COLORS.get(store.store_name, ("#183b35", "#eef7f0"))
        page.rect(x, y - 76, card_w, 76, tint)
        page.rect(x, y - 76, 5, 76, color)
        page.text(store.store_name, x + 13, y - 20, 12, color, bold=True)
        page.text(str(len(store.specials)), x + 13, y - 43, 22, "#1f2933", bold=True)
        page.draw_wrapped_text(_top_categories_text(store.specials), x + 13, y - 58, 8, "#4b5563", 21)
    return y - 104


def _draw_pdf_store_intro(
    page: "_PdfPage",
    store: GroceryStoreSpecials,
    y: float,
    color: str,
) -> float:
    page.rect(PDF_MARGIN, y - 72, PDF_PAGE_WIDTH - PDF_MARGIN * 2, 72, "#f5f1ea")
    page.text(f"{len(store.specials)} specials found", PDF_MARGIN + 14, y - 22, 18, color, bold=True)
    page.draw_wrapped_text(
        f"Worth checking for: {_top_categories_text(store.specials)}",
        PDF_MARGIN + 14,
        y - 44,
        10,
        "#374151",
        78,
    )
    return y - 96


def _draw_pdf_section_title(page: "_PdfPage", title: str, y: float) -> float:
    page.text(title, PDF_MARGIN, y, 15, "#183b35", bold=True)
    page.line(PDF_MARGIN, y - 8, PDF_PAGE_WIDTH - PDF_MARGIN, y - 8, "#d7cbbb")
    return y - 25


def _draw_pdf_cards(
    page: "_PdfPage",
    pdf: "_PdfBuilder",
    specials: list[GrocerySpecial],
    y: float,
    color: str = "#183b35",
) -> tuple["_PdfPage", float]:
    card_w = (PDF_PAGE_WIDTH - PDF_MARGIN * 2 - 12) / 2
    card_h = 116
    x_positions = [PDF_MARGIN, PDF_MARGIN + card_w + 12]
    column = 0

    current_page = page
    for special in specials:
        if y - card_h < PDF_BOTTOM:
            current_page = pdf.new_page()
            y = _draw_pdf_header(current_page, "Grocery Specials", "continued", color)
            column = 0

        x = x_positions[column]
        _draw_pdf_card(current_page, pdf, special, x, y, card_w, card_h)
        column += 1
        if column == 2:
            column = 0
            y -= card_h + 12

    if column == 1:
        y -= card_h + 12
    return current_page, y


def _draw_pdf_card(
    page: "_PdfPage",
    pdf: "_PdfBuilder",
    special: GrocerySpecial,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    color, tint = STORE_COLORS.get(special.store_name, ("#183b35", "#eef7f0"))
    page.rect(x, y - height, width, height, "#ffffff")
    page.rect(x, y - height, 5, height, color)
    page.rect(x + 10, y - 32, 72, 72, "#f5f1ea")
    if special.image_url:
        page.image(pdf, special.image_url, x + 13, y - 99, 66, 66)
    else:
        page.draw_wrapped_text(special.category or "Deal", x + 17, y - 62, 8, "#6b5f53", 11, bold=True)

    text_x = x + 92
    page.text(special.store_name, text_x, y - 18, 8, color, bold=True)
    page.text(special.category or "Other", text_x + 70, y - 18, 8, "#6b7280")
    page.draw_wrapped_text(special.item_name, text_x, y - 36, 10, "#1f2933", 27, bold=True, max_lines=2)
    page.text(special.price, text_x, y - 77, 16, color, bold=True)

    saving = _savings_text(special)
    if saving:
        page.draw_wrapped_text(saving, text_x + 78, y - 76, 8, "#4b5563", 24, max_lines=2)
    meta = _special_meta(special)
    if meta:
        page.draw_wrapped_text(meta, text_x, y - 96, 7, "#6b7280", 40, max_lines=2)


def _draw_pdf_compact_rows(
    page: "_PdfPage",
    specials: list[GrocerySpecial],
    y: float,
) -> float:
    for special in specials:
        if y < PDF_BOTTOM + 34:
            break
        color = STORE_COLORS.get(special.store_name, ("#183b35", "#eef7f0"))[0]
        page.text(special.store_name, PDF_MARGIN, y, 8, color, bold=True)
        page.draw_wrapped_text(special.item_name, PDF_MARGIN + 76, y, 9, "#1f2933", 55)
        page.text(special.price, PDF_PAGE_WIDTH - PDF_MARGIN - 58, y, 10, color, bold=True)
        y -= 28
    return y - 4


def _all_specials(content: GrocerySpecialsContent) -> list[GrocerySpecial]:
    return [special for store in content.stores for special in store.specials]


def _top_specials(
    content: GrocerySpecialsContent,
    limit: int,
) -> list[GrocerySpecial]:
    return sorted(
        _all_specials(content),
        key=lambda special: (
            special.deal_score,
            special.saving_percent or 0,
            _price_amount(special.price) or 0,
        ),
        reverse=True,
    )[:limit]


def _category_groups(
    specials: list[GrocerySpecial],
) -> dict[str, list[GrocerySpecial]]:
    grouped: dict[str, list[GrocerySpecial]] = {}
    for special in sorted(specials, key=lambda item: item.deal_score, reverse=True):
        category = special.category or "Other"
        grouped.setdefault(category, []).append(special)
    return grouped


def _top_categories_text(specials: list[GrocerySpecial]) -> str:
    if not specials:
        return "no clear category yet"
    counts: dict[str, int] = {}
    for special in specials:
        counts[special.category or "Other"] = counts.get(special.category or "Other", 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    if len(ranked) > 1:
        ranked = [item for item in ranked if item[0] != "Other"] or ranked
    top = ranked[:3]
    return ", ".join(category for category, _ in top)


def _special_text_line(special: GrocerySpecial) -> str:
    pieces = [special.store_name, special.item_name, special.price]
    savings = _savings_text(special)
    if savings:
        pieces.append(savings)
    if special.validity:
        pieces.append(f"valid {special.validity}")
    return " - ".join(piece for piece in pieces if piece)


def _special_meta(special: GrocerySpecial) -> str:
    pieces = []
    if special.promotion:
        pieces.append(special.promotion)
    if special.validity:
        pieces.append(f"Valid {special.validity}")
    if special.catalogue_url:
        pieces.append("Source linked")
    return " | ".join(pieces)


def _savings_text(special: GrocerySpecial) -> str:
    parts = []
    if special.regular_price:
        parts.append(f"Was {special.regular_price}")
    if special.saving_amount:
        parts.append(f"Save {special.saving_amount}")
    if special.saving_percent is not None:
        parts.append(f"{special.saving_percent:.0f}% off")
    if special.unit_price:
        parts.append(special.unit_price)
    return " | ".join(parts)


def _price_amount(value: str) -> float | None:
    match = re.search(r"R\s*([\d\s]+(?:[,.]\d{2})?)", value, re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1).replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "store"


@dataclass
class _ImageResource:
    name: str
    data: bytes
    width: int
    height: int
    object_id: int = 0


@dataclass
class _PdfPage:
    commands: list[str] = field(default_factory=list)

    def rect(self, x: float, y: float, width: float, height: float, color: str) -> None:
        r, g, b = _hex_to_rgb(color)
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} {width:.2f} {height:.2f} re f")

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str) -> None:
        r, g, b = _hex_to_rgb(color)
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG 0.8 w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def text(
        self,
        text: str,
        x: float,
        y: float,
        size: int,
        color: str,
        bold: bool = False,
    ) -> None:
        r, g, b = _hex_to_rgb(color)
        font = "F2" if bold else "F1"
        self.commands.append(
            f"BT /{font} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} Td ({_pdf_escape(text)}) Tj ET"
        )

    def draw_wrapped_text(
        self,
        text: str,
        x: float,
        y: float,
        size: int,
        color: str,
        width_chars: int,
        bold: bool = False,
        max_lines: int | None = None,
    ) -> float:
        lines = textwrap.wrap(
            text,
            width=max(8, width_chars),
            break_long_words=False,
            replace_whitespace=False,
        ) or [""]
        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip(". ") + "..."
        for line in lines:
            self.text(line, x, y, size, color, bold=bold)
            y -= size + 3
        return y

    def image(
        self,
        pdf: "_PdfBuilder",
        url: str,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        image = pdf.image(url)
        if image is None:
            return
        fitted_w, fitted_h = _fit_image(image.width, image.height, width, height)
        offset_x = x + (width - fitted_w) / 2
        offset_y = y + (height - fitted_h) / 2
        self.commands.append(
            f"q {fitted_w:.2f} 0 0 {fitted_h:.2f} {offset_x:.2f} {offset_y:.2f} cm /{image.name} Do Q"
        )


class _PdfBuilder:
    def __init__(self) -> None:
        self.pages: list[_PdfPage] = []
        self.images_by_url: dict[str, _ImageResource] = {}

    def new_page(self) -> _PdfPage:
        page = _PdfPage()
        self.pages.append(page)
        return page

    def image(self, url: str) -> _ImageResource | None:
        if url in self.images_by_url:
            return self.images_by_url[url]
        try:
            data, media_type = get_bytes(url, timeout_seconds=12)
        except RuntimeError:
            return None
        if media_type not in {"image/jpeg", "image/jpg"} and not data.startswith(b"\xff\xd8"):
            return None
        dimensions = _jpeg_dimensions(data)
        if dimensions is None:
            return None
        image = _ImageResource(
            name=f"Im{len(self.images_by_url) + 1}",
            data=data,
            width=dimensions[0],
            height=dimensions[1],
        )
        self.images_by_url[url] = image
        return image

    def write(self, path: Path) -> None:
        if not self.pages:
            self.new_page()

        objects: dict[int, bytes] = {
            1: b"<< /Type /Catalog /Pages 2 0 R >>",
            3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        }
        next_id = 5
        for image in self.images_by_url.values():
            image.object_id = next_id
            next_id += 1
            objects[image.object_id] = _image_object(image)

        page_ids: list[int] = []
        for page in self.pages:
            content = "\n".join(page.commands).encode("latin-1", errors="replace")
            content_id = next_id
            page_id = next_id + 1
            next_id += 2
            objects[content_id] = (
                f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
                + content
                + b"\nendstream"
            )
            objects[page_id] = _page_object(content_id, self.images_by_url)
            page_ids.append(page_id)

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
            "ascii"
        )
        _write_pdf_objects(path, objects)


def _page_object(
    content_id: int,
    images_by_url: dict[str, _ImageResource],
) -> bytes:
    xobjects = " ".join(
        f"/{image.name} {image.object_id} 0 R"
        for image in images_by_url.values()
        if image.object_id
    )
    return (
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PDF_PAGE_WIDTH} {PDF_PAGE_HEIGHT}] "
        f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << {xobjects} >> >> "
        f"/Contents {content_id} 0 R >>"
    ).encode("ascii")


def _image_object(image: _ImageResource) -> bytes:
    return (
        f"<< /Type /XObject /Subtype /Image /Width {image.width} /Height {image.height} "
        f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(image.data)} >>\n"
    ).encode("ascii") + b"stream\n" + image.data + b"\nendstream"


def _write_pdf_objects(path: Path, objects: dict[int, bytes]) -> None:
    offsets: dict[int, int] = {}
    output = bytearray(b"%PDF-1.4\n")
    for object_id in range(1, max(objects) + 1):
        offsets[object_id] = len(output)
        output.extend(f"{object_id} 0 obj\n".encode("ascii"))
        output.extend(objects[object_id])
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {max(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for object_id in range(1, max(objects) + 1):
        output.extend(f"{offsets[object_id]:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {max(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(output))


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    while index < len(data) - 9:
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        length = int.from_bytes(data[index : index + 2], "big")
        if marker in {0xC0, 0xC1, 0xC2, 0xC3}:
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += length
    return None


def _fit_image(
    image_width: int,
    image_height: int,
    box_width: float,
    box_height: float,
) -> tuple[float, float]:
    if image_width <= 0 or image_height <= 0:
        return box_width, box_height
    scale = min(box_width / image_width, box_height / image_height)
    return image_width * scale, image_height * scale


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    cleaned = value.lstrip("#")
    return (
        int(cleaned[0:2], 16) / 255,
        int(cleaned[2:4], 16) / 255,
        int(cleaned[4:6], 16) / 255,
    )


def _pdf_escape(value: str) -> str:
    cleaned = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")
