from __future__ import annotations

import base64
from pathlib import Path

import pytest

from openai_vision_mcp.images import build_image_inputs, local_image_to_data_url


def test_local_image_to_data_url(tmp_path: Path) -> None:
    path = tmp_path / "sample.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = local_image_to_data_url(str(path))

    assert result == "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def test_build_image_inputs_accepts_mixed_sources(tmp_path: Path) -> None:
    path = tmp_path / "sample.jpg"
    path.write_bytes(b"jpeg")

    result = build_image_inputs(
        images=[str(path), "https://example.com/image.webp"],
        image_url="data:image/gif;base64,R0lGODlh",
    )

    assert len(result) == 3
    assert result[0].startswith("data:image/jpeg;base64,")
    assert result[1] == "https://example.com/image.webp"


def test_build_image_inputs_requires_an_image() -> None:
    with pytest.raises(ValueError, match="At least one image"):
        build_image_inputs()


def test_build_image_inputs_rejects_invalid_data_url() -> None:
    with pytest.raises(ValueError, match="invalid base64"):
        build_image_inputs(images=["data:image/png;base64,%%%"])
