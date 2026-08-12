from __future__ import annotations

import asyncio
from typing import Any

import pytest

from openai_vision_mcp.config import Settings
from openai_vision_mcp.server import (
    NATIVE_VISION_ROUTING_GUARD,
    analyze_image,
    mcp,
)


def test_analyze_image_has_cli_friendly_schema() -> None:
    tools = asyncio.run(mcp.list_tools())
    tool = next(tool for tool in tools if tool.name == "analyze_image")
    schema = tool.input_schema
    properties = schema["properties"]

    assert schema["required"] == ["image"]
    assert properties["image"]["type"] == "string"
    assert properties["prompt"]["type"] == "string"
    assert properties["system_prompt"]["type"] == "string"
    assert properties["mode"]["enum"][0] == "auto"


def test_all_image_tools_warn_native_vision_callers_not_to_call() -> None:
    tools = asyncio.run(mcp.list_tools())
    image_tools = {
        tool.name: tool for tool in tools if tool.name in {"analyze_image", "understand_image"}
    }

    assert set(image_tools) == {"analyze_image", "understand_image"}
    for tool in image_tools.values():
        assert tool.description is not None
        assert tool.description.startswith("DO NOT CALL if you natively support vision")
        assert NATIVE_VISION_ROUTING_GUARD in tool.description


def test_server_instructions_warn_native_vision_callers_not_to_call() -> None:
    assert mcp.instructions is not None
    assert mcp.instructions.startswith("DO NOT CALL if you natively support vision")
    assert NATIVE_VISION_ROUTING_GUARD in mcp.instructions


def test_analyze_image_calls_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        def __init__(self, settings: Settings) -> None:
            captured["settings"] = settings

        async def analyze(self, **kwargs: Any) -> str:
            captured["request"] = kwargs
            return "result"

    monkeypatch.setattr(
        "openai_vision_mcp.server.load_settings",
        lambda: Settings("https://example.com/v1", "key", "model", 10),
    )
    monkeypatch.setattr("openai_vision_mcp.server.VisionClient", FakeClient)

    result = asyncio.run(
        analyze_image(
            image="https://example.com/image.png",
            prompt="Read this",
            mode="ocr",
            ascii_mode="always",
            detail="high",
            max_tokens=256,
        )
    )

    assert result == "result"
    request = captured["request"]
    assert request["images"] == ["https://example.com/image.png"]
    assert request["prompt"] == "Read this"
    assert request["detail"] == "high"
    assert "careful OCR" in request["system_prompt"]
    assert "ASCII-only" in request["system_prompt"]
