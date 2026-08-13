from __future__ import annotations

import asyncio
import json
import platform
import secrets
from typing import Any

import httpx
import pytest

from openai_vision_mcp.client import (
    USER_AGENT,
    APIStyle,
    VisionAPIError,
    VisionClient,
    build_chat_completions_payload,
    build_responses_payload,
    build_user_agent,
    parse_chat_completions_text,
    parse_responses_text,
    resolve_endpoints,
)
from openai_vision_mcp.config import Settings


def test_resolve_endpoints() -> None:
    assert [endpoint.style for endpoint in resolve_endpoints("https://example.com/v1")] == [
        APIStyle.RESPONSES,
        APIStyle.CHAT_COMPLETIONS,
    ]
    assert resolve_endpoints("https://example.com/v1/responses")[0].url.endswith("/responses")
    assert (
        resolve_endpoints("https://example.com/v1/chat/completions")[0].style
        is APIStyle.CHAT_COMPLETIONS
    )
    assert (
        resolve_endpoints("https://example.com/v1?api-version=2026-01-01")[0].url
        == "https://example.com/v1/responses?api-version=2026-01-01"
    )
    assert (
        resolve_endpoints("https://example.com/v1/chat/completions?api-version=2026-01-01")[0].style
        is APIStyle.CHAT_COMPLETIONS
    )


def test_build_payloads_use_each_api_schema() -> None:
    responses = build_responses_payload(
        model="model",
        images=["https://example.com/a.png"],
        prompt="inspect",
        system_prompt="system",
        detail="high",
        max_tokens=100,
    )
    chat = build_chat_completions_payload(
        model="model",
        images=["https://example.com/a.png"],
        prompt="inspect",
        system_prompt="system",
        detail="high",
        max_tokens=100,
    )

    response_image = responses["input"][0]["content"][1]
    chat_image = chat["messages"][1]["content"][1]
    assert response_image == {
        "type": "input_image",
        "image_url": "https://example.com/a.png",
        "detail": "high",
    }
    assert chat_image == {
        "type": "image_url",
        "image_url": {"url": "https://example.com/a.png", "detail": "high"},
    }
    assert responses["max_output_tokens"] == 100
    assert chat["max_tokens"] == 100


def test_payloads_accept_original_image_detail() -> None:
    payload = build_responses_payload(
        model="model",
        images=["https://example.com/a.png"],
        prompt="inspect",
        system_prompt="system",
        detail="original",
        max_tokens=100,
    )

    assert payload["input"][0]["content"][1]["detail"] == "original"


def test_parse_response_formats() -> None:
    assert parse_responses_text({"output_text": "direct"}) == "direct"
    assert (
        parse_responses_text({"output": [{"content": [{"type": "output_text", "text": "nested"}]}]})
        == "nested"
    )
    assert parse_chat_completions_text({"choices": [{"message": {"content": "chat"}}]}) == "chat"


def test_client_falls_back_from_responses_to_chat() -> None:
    requests: list[tuple[str, dict[str, Any]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append((request.url.path, body))
        if request.url.path.endswith("/responses"):
            return httpx.Response(404, json={"error": "not found"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "seen"}}]})

    client = VisionClient(
        Settings("https://example.com/v1", "key", "model", 10),
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(
        client.analyze(
            images=["https://example.com/image.png"],
            prompt="inspect",
            system_prompt="system",
            detail="auto",
            max_tokens=100,
        )
    )

    assert result == "seen"
    assert [path for path, _ in requests] == ["/v1/responses", "/v1/chat/completions"]
    assert requests[0][1]["input"][0]["content"][1]["type"] == "input_image"
    assert requests[1][1]["messages"][1]["content"][1]["type"] == "image_url"


def test_client_uses_codex_user_agent() -> None:
    seen_user_agents: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_user_agents.append(request.headers["user-agent"])
        return httpx.Response(200, json={"output_text": "seen"})

    client = VisionClient(
        Settings("https://example.com/v1/responses", "key", "model", 10),
        transport=httpx.MockTransport(handler),
    )
    asyncio.run(
        client.analyze(
            images=["https://example.com/image.png"],
            prompt="inspect",
            system_prompt="system",
            detail="auto",
            max_tokens=100,
        )
    )

    assert seen_user_agents == [USER_AGENT]
    assert not USER_AGENT.startswith("python-httpx/")


def test_user_agent_uses_current_macos_version_and_architecture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def choose_kitty(choices: tuple[str, ...]) -> str:
        assert choices == ("kitty", "ghostty")
        return "kitty"

    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "mac_ver", lambda: ("26.4", ("", "", ""), ""))
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(secrets, "choice", choose_kitty)

    assert build_user_agent() == (
        "codex-tui/0.147.0 (Mac OS 26.4.0; x86_64) "
        "kitty (codex-tui; 0.147.0)"
    )


def test_user_agent_randomizes_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_choices: list[tuple[str, ...]] = []

    def choose_terminal(choices: tuple[str, ...]) -> str:
        seen_choices.append(choices)
        return "ghostty"

    monkeypatch.setattr(secrets, "choice", choose_terminal)

    assert build_user_agent().endswith("ghostty (codex-tui; 0.147.0)")
    assert seen_choices == [("kitty", "ghostty")]


def test_client_does_not_hide_model_errors_with_fallback() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "model not found"}})

    client = VisionClient(
        Settings("https://example.com/v1", "key", "missing-model", 10),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(VisionAPIError, match="HTTP 400"):
        asyncio.run(
            client.analyze(
                images=["https://example.com/image.png"],
                prompt="inspect",
                system_prompt="system",
                detail="auto",
                max_tokens=100,
            )
        )


def test_chat_retries_with_max_completion_tokens() -> None:
    payloads: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        payloads.append(payload)
        if "max_tokens" in payload:
            return httpx.Response(
                400,
                json={"error": {"message": "max_tokens is unsupported; use max_completion_tokens"}},
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = VisionClient(
        Settings("https://example.com/v1/chat/completions", "key", "model", 10),
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(
        client.analyze(
            images=["https://example.com/image.png"],
            prompt="inspect",
            system_prompt="system",
            detail="auto",
            max_tokens=100,
        )
    )

    assert result == "ok"
    assert "max_tokens" in payloads[0]
    assert payloads[1]["max_completion_tokens"] == 100
