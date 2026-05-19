from __future__ import annotations

"""Render grocery specials to email HTML/text and simple PDF documents."""

import html
import re
import textwrap
from datetime import datetime
from pathlib import Path

from daily_brief.models import (
    GrocerySpecial,
    GrocerySpecialsContent,
    GroceryStoreSpecials,
)


PDF_PAGE_WIDTH = 595
PDF_PAGE_HEIGHT = 842
PDF_LEFT_MARGIN = 48
PDF_TOP_Y = 792
PDF_FONT_SIZE = 10
PDF_LEADING = 14
PDF_LINES_PER_PAGE = 52
PDF_WRAP_WIDTH = 92


def render_grocery_text(
    brief_date: datetime,
    content: GrocerySpecialsContent,
) -> str:
    lines = [
        f"Midrand Grocery Specials - {brief_date:%A, %d %B %Y}",
        f"Area: {content.area}",
        "",
        "Attached PDFs break the specials out by store.",
    ]

    for store in content.stores:
        lines.extend(["", f"{store.store_name}", "-" * len(store.store_name)])
        if not store.specials:
            lines.append("No specials could be extracted cleanly.")
        else:
            for special in store.specials[:25]:
                lines.append(_special_text_line(special))
            if len(store.specials) > 25:
                lines.append(f"...and {len(store.specials) - 25} more in the PDF.")

        if store.warnings:
            lines.append("Notes: " + " | ".join(store.warnings))

    if content.warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"- {warning}" for warning in content.warnings)

    return "\n".join(lines)


def render_grocery_html(
    brief_date: datetime,
    content: GrocerySpecialsContent,
) -> str:
    store_sections = "\n".join(_store_section_html(store) for store in content.stores)
    warnings_html = _warnings_html(content.warnings)
    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;padding:0;background:#f3f6f2;font-family:Segoe UI,Arial,sans-serif;color:#1f2933">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6f2">
      <tr>
        <td align="center" style="padding:28px 12px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:820px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid #d7e0d5">
            <tr>
              <td style="padding:30px 34px;background:#2f5d50;color:#ffffff">
                <div style="font-size:12px;text-transform:uppercase;letter-spacing:.8px;font-weight:800;color:#cfe6dc">Monthly grocery scan</div>
                <h1 style="font-size:30px;line-height:1.12;margin:10px 0 0">Midrand Grocery Specials</h1>
                <p style="margin:12px 0 0;font-size:15px;line-height:1.5;color:#edf8f2">
                  Specials gathered for {html.escape(content.area)} on {brief_date:%A, %d %B %Y}.
                  Store PDFs are attached for easier month-end shopping.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 34px 30px">
                {store_sections}
                {warnings_html}
                <p style="margin:24px 0 0;color:#687782;font-size:12px;text-align:center">
                  Prices and availability can change by branch. Please check the retailer before checkout.
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

    for store in content.stores:
        filename = f"{brief_date:%Y-%m-%d}-{_slugify(store.store_name)}-specials.pdf"
        path = output_dir / filename
        _write_simple_pdf(path, _store_pdf_lines(brief_date, content.area, store))
        paths.append(path)

    return paths


def _store_section_html(store: GroceryStoreSpecials) -> str:
    rows = "\n".join(_special_row_html(special) for special in store.specials[:30])
    if not rows:
        rows = """<tr><td colspan="4" style="padding:12px;border-bottom:1px solid #e2e8df;color:#687782">No specials could be extracted cleanly.</td></tr>"""
    extra = ""
    if len(store.specials) > 30:
        extra = f"""
        <p style="margin:10px 0 0;color:#687782;font-size:12px">
          Plus {len(store.specials) - 30} more in the attached PDF.
        </p>"""
    warnings = _warnings_html(store.warnings, compact=True)
    return f"""
    <section style="margin:0 0 24px">
      <h2 style="font-size:21px;line-height:1.2;margin:0 0 10px;color:#1f2933">{html.escape(store.store_name)}</h2>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;border:1px solid #dfe7dd;border-radius:8px;overflow:hidden">
        <tr style="background:#edf4ea">
          <th align="left" style="padding:9px 10px;font-size:12px;color:#394b41">Item</th>
          <th align="left" style="padding:9px 10px;font-size:12px;color:#394b41">Price</th>
          <th align="left" style="padding:9px 10px;font-size:12px;color:#394b41">Promotion</th>
          <th align="left" style="padding:9px 10px;font-size:12px;color:#394b41">Source</th>
        </tr>
        {rows}
      </table>
      {extra}
      {warnings}
    </section>"""


def _special_row_html(special: GrocerySpecial) -> str:
    source = special.source_name or special.store_name
    if special.source_url:
        source_html = (
            f'<a href="{html.escape(special.source_url, quote=True)}" '
            f'style="color:#2f5d50;text-decoration:none">{html.escape(source)}</a>'
        )
    else:
        source_html = html.escape(source)

    promo = special.promotion or special.validity or "-"
    return f"""
        <tr>
          <td style="padding:10px;border-top:1px solid #e2e8df;font-size:13px;line-height:1.35">{html.escape(special.item_name)}</td>
          <td style="padding:10px;border-top:1px solid #e2e8df;font-size:13px;font-weight:800;color:#2f5d50;white-space:nowrap">{html.escape(special.price)}</td>
          <td style="padding:10px;border-top:1px solid #e2e8df;font-size:12px;color:#52645b">{html.escape(promo)}</td>
          <td style="padding:10px;border-top:1px solid #e2e8df;font-size:12px">{source_html}</td>
        </tr>"""


def _warnings_html(warnings: list[str], compact: bool = False) -> str:
    if not warnings:
        return ""

    items = "".join(f"<li>{html.escape(warning)}</li>" for warning in warnings)
    margin = "10px 0 0" if compact else "20px 0 0"
    return f"""
    <div style="margin:{margin};padding:12px 14px;background:#fff7e6;border:1px solid #f2d399;border-radius:8px;color:#5f4b1b;font-size:12px;line-height:1.45">
      <strong>Notes</strong>
      <ul style="margin:6px 0 0 18px;padding:0">{items}</ul>
    </div>"""


def _store_pdf_lines(
    brief_date: datetime,
    area: str,
    store: GroceryStoreSpecials,
) -> list[str]:
    lines = [
        f"{store.store_name} specials",
        f"Area: {area}",
        f"Generated: {brief_date:%A, %d %B %Y}",
        "",
    ]

    if not store.specials:
        lines.append("No specials could be extracted cleanly from the configured sources.")
    else:
        for index, special in enumerate(store.specials, start=1):
            lines.append(f"{index}. {_special_text_line(special)}")
            if special.source_name:
                lines.append(f"   Source: {special.source_name}")
            if special.source_url:
                lines.append(f"   Link: {special.source_url}")
            lines.append("")

    if store.warnings:
        lines.extend(["Notes:"])
        lines.extend(f"- {warning}" for warning in store.warnings)

    lines.extend(
        [
            "",
            "Retailer prices, availability, branch participation, and loyalty-card rules can change.",
            "Please check the shelf, app, or retailer site before checkout.",
        ]
    )
    return lines


def _special_text_line(special: GrocerySpecial) -> str:
    parts = [special.item_name, special.price]
    if special.promotion:
        parts.append(special.promotion)
    elif special.validity:
        parts.append(f"valid for {special.validity}")
    return " - ".join(part for part in parts if part)


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    pages = _paginate_pdf_lines(lines)
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    page_ids: list[int] = []
    next_id = 4

    for page_lines in pages:
        content_id = next_id
        page_id = next_id + 1
        next_id += 2

        stream = _pdf_content_stream(page_lines)
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        )
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PDF_PAGE_WIDTH} {PDF_PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "ascii"
    )

    _write_pdf_objects(path, objects)


def _paginate_pdf_lines(lines: list[str]) -> list[list[str]]:
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(
            textwrap.wrap(
                line,
                width=PDF_WRAP_WIDTH,
                subsequent_indent="  ",
                break_long_words=False,
                replace_whitespace=False,
            )
            or [""]
        )

    pages = [
        wrapped[index : index + PDF_LINES_PER_PAGE]
        for index in range(0, len(wrapped), PDF_LINES_PER_PAGE)
    ]
    return pages or [["No content."]]


def _pdf_content_stream(lines: list[str]) -> bytes:
    parts = [
        "BT",
        f"/F1 {PDF_FONT_SIZE} Tf",
        f"{PDF_LEFT_MARGIN} {PDF_TOP_Y} Td",
        f"{PDF_LEADING} TL",
    ]
    for line in lines:
        parts.append(f"({_pdf_escape(line)}) Tj")
        parts.append("T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", errors="replace")


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


def _pdf_escape(value: str) -> str:
    cleaned = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "store"
