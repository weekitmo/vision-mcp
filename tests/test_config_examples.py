from __future__ import annotations

from pathlib import Path

import pytest
import tomllib

REPOSITORY_SOURCE = "git+https://github.com/weekitmo/vision-mcp.git@main"


@pytest.mark.parametrize("name", ["codex", "grok"])
def test_toml_mcp_examples_use_main_branch(name: str) -> None:
    path = Path("config") / f"{name}.toml.example"
    config = tomllib.loads(path.read_text())
    server = config["mcp_servers"]["vision"]

    assert server["command"] == "uvx"
    assert server["args"] == ["--from", REPOSITORY_SOURCE, "vision-mcp"]
    assert server["startup_timeout_sec"] == 60
    assert server["tool_timeout_sec"] == 180


def test_codex_example_forwards_provider_environment() -> None:
    config = tomllib.loads(Path("config/codex.toml.example").read_text())
    server = config["mcp_servers"]["vision"]

    assert server["env_vars"] == [
        "VISION_BASE_URL",
        "VISION_API_KEY",
        "VISION_MODEL",
        "VISION_TIMEOUT",
    ]


def test_grok_example_configures_provider_environment() -> None:
    config = tomllib.loads(Path("config/grok.toml.example").read_text())
    server = config["mcp_servers"]["vision"]

    assert server["env"] == {
        "VISION_BASE_URL": "https://api.openai.com/v1",
        "VISION_API_KEY": "your-api-key",
        "VISION_MODEL": "your-vision-model",
        "VISION_TIMEOUT": "120",
    }
