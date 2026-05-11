from __future__ import annotations

"""Helpers for embedding remote images into outgoing email."""

import mimetypes
import re
from urllib.parse import urlparse

from daily_brief.http_client import get_bytes
from daily_brief.tools.email import InlineImage


MAX_INLINE_IMAGE_BYTES = 2_500_000
SUPPORTED_IMAGE_TYPES = {
    "image/gif": ("image", "gif", ".gif"),
    "image/jpeg": ("image", "jpeg", ".jpg"),
    "image/png": ("image", "png", ".png"),
    "image/webp": ("image", "webp", ".webp"),
}


def fetch_inline_image(
    url: str,
    content_id: str,
    filename_stem: str,
) -> InlineImage:
    data, media_type = get_bytes(url, timeout_seconds=20)
    if len(data) > MAX_INLINE_IMAGE_BYTES:
        raise RuntimeError(
            f"Image is too large to embed: {len(data)} bytes from {url}"
        )

    maintype, subtype, extension = _image_type(url, media_type)
    return InlineImage(
        content_id=content_id,
        data=data,
        maintype=maintype,
        subtype=subtype,
        filename=f"{_slugify(filename_stem)}{extension}",
    )


def _image_type(url: str, media_type: str) -> tuple[str, str, str]:
    if media_type in SUPPORTED_IMAGE_TYPES:
        return SUPPORTED_IMAGE_TYPES[media_type]

    guessed_type, _ = mimetypes.guess_type(urlparse(url).path)
    if guessed_type in SUPPORTED_IMAGE_TYPES:
        return SUPPORTED_IMAGE_TYPES[guessed_type]

    raise RuntimeError(f"Unsupported image content type: {media_type or 'unknown'}")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "image"
