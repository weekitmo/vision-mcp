from __future__ import annotations

import base64
import binascii
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

MAX_IMAGES = 10
MAX_IMAGE_BYTES = 20 * 1024 * 1024
SUPPORTED_MIME_TYPES = {
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def guess_image_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"
    if mime_type not in SUPPORTED_MIME_TYPES:
        supported = ", ".join(sorted(SUPPORTED_MIME_TYPES))
        raise ValueError(
            f"Unsupported image type for {path.name!r}. Supported MIME types: {supported}."
        )
    return mime_type


def local_image_to_data_url(image_path: str) -> str:
    path = Path(image_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Image does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Image path is not a file: {path}")

    size = path.stat().st_size
    if size > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is too large: {size / 1024 / 1024:.2f} MiB. "
            f"The per-image limit is {MAX_IMAGE_BYTES / 1024 / 1024:.0f} MiB."
        )

    mime_type = guess_image_mime_type(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def validate_image_url(image_url: str) -> str:
    value = image_url.strip()
    if value.startswith("data:"):
        return _validate_data_url(value)

    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Image URL must be an absolute http(s) URL or a base64 image data URL.")
    return value


def _validate_data_url(value: str) -> str:
    try:
        header, encoded = value.split(",", 1)
    except ValueError as exc:
        raise ValueError("Image data URL is missing its base64 payload.") from exc

    if not header.endswith(";base64"):
        raise ValueError("Image data URL must use base64 encoding.")
    mime_type = header.removeprefix("data:").removesuffix(";base64").lower()
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(f"Unsupported image data URL MIME type: {mime_type or '(empty)'}.")

    estimated_size = len(encoded) * 3 // 4
    if estimated_size > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image data URL is too large. The per-image limit is "
            f"{MAX_IMAGE_BYTES / 1024 / 1024:.0f} MiB."
        )
    try:
        base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Image data URL contains invalid base64 data.") from exc
    return value


def build_image_inputs(
    *,
    images: list[str] | None = None,
    image_path: str | None = None,
    image_url: str | None = None,
    image_paths: list[str] | None = None,
    image_urls: list[str] | None = None,
) -> list[str]:
    """Normalize local paths, remote URLs, and compatibility aliases."""

    values: list[str] = []
    for image in images or []:
        if image.strip().startswith(("http://", "https://", "data:")):
            values.append(validate_image_url(image))
        else:
            values.append(local_image_to_data_url(image))

    if image_path:
        values.append(local_image_to_data_url(image_path))
    if image_url:
        values.append(validate_image_url(image_url))
    for path in image_paths or []:
        values.append(local_image_to_data_url(path))
    for url in image_urls or []:
        values.append(validate_image_url(url))

    if not values:
        raise ValueError(
            "At least one image is required. Pass images, image_path, image_url, "
            "image_paths, or image_urls."
        )
    if len(values) > MAX_IMAGES:
        raise ValueError(f"At most {MAX_IMAGES} images can be analyzed in one call.")
    return values
