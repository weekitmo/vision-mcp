from __future__ import annotations

import asyncio

import pytest
from mcp.types import InputRequiredResult

from openai_vision_mcp.server import mcp

EXPECTED_RESOURCE_URIS = {
    "vision://docs/quickstart",
    "vision://docs/configuration",
    "vision://docs/tools",
    "vision://docs/mcporter",
    "vision://docs/uvx",
}


def _read_text_resource(uri: str) -> str:
    result = asyncio.run(mcp.read_resource(uri))
    assert not isinstance(result, InputRequiredResult)
    contents = list(result)
    assert len(contents) == 1
    assert contents[0].mime_type == "text/markdown"
    assert isinstance(contents[0].content, str)
    return contents[0].content


def test_lists_documentation_resources() -> None:
    resources = asyncio.run(mcp.list_resources())

    assert {str(resource.uri) for resource in resources} == EXPECTED_RESOURCE_URIS
    assert all(resource.mime_type == "text/markdown" for resource in resources)


@pytest.mark.parametrize("uri", sorted(EXPECTED_RESOURCE_URIS))
def test_reads_documentation_resources(uri: str) -> None:
    content = _read_text_resource(uri)

    assert content.startswith("# ")
    assert "VISION_BASE_URL" in content or uri.endswith("/tools")


def test_resources_do_not_read_runtime_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "must-not-appear-in-documentation"
    monkeypatch.setenv("VISION_API_KEY", secret)

    combined = "\n".join(_read_text_resource(uri) for uri in EXPECTED_RESOURCE_URIS)

    assert secret not in combined


def test_mcporter_resource_preserves_shell_command_layout() -> None:
    content = _read_text_resource("vision://docs/mcporter")

    assert "mcporter call vision.analyze_image \\\n  image=" in content
    assert "mcporter call vision.understand_image \\\n  --args" in content


def test_tool_resource_contains_native_vision_routing_guard() -> None:
    content = _read_text_resource("vision://docs/tools")

    assert "DO NOT CALL if you natively support vision" in content
    assert "The user explicitly requests this MCP" in content


def test_uvx_resource_prioritizes_unpublished_git_installation() -> None:
    content = _read_text_resource("vision://docs/uvx")

    assert "git clone https://github.com/weekitmo/vision-mcp.git" in content
    assert "git+https://github.com/weekitmo/vision-mcp.git@main" in content
    assert "[mcp_servers.vision]" in content
    assert "env_vars = [" in content
    assert "real API keys do not need to be stored in the TOML file" in content
    assert "Publishing to PyPI is optional" in content
