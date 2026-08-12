from __future__ import annotations

import pytest

from openai_vision_mcp.config import ConfigurationError, load_settings


def test_load_settings_prefers_vision_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VISION_BASE_URL", "https://vision.example/v1/")
    monkeypatch.setenv("VISION_API_KEY", "vision-key")
    monkeypatch.setenv("VISION_MODEL", "vision-model")
    monkeypatch.setenv("VISION_TIMEOUT", "42.5")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://ignored.example/v1")

    settings = load_settings()

    assert settings.base_url == "https://vision.example/v1"
    assert settings.api_key == "vision-key"
    assert settings.model == "vision-model"
    assert settings.timeout == 42.5


def test_load_settings_accepts_openai_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("VISION_BASE_URL", "VISION_API_KEY", "VISION_MODEL", "VISION_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_MODEL", "local-model")

    settings = load_settings()

    assert settings.timeout == 120
    assert settings.model == "local-model"


def test_load_settings_accepts_endpoint_query_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "VISION_BASE_URL",
        "https://vision.example/v1/responses?api-version=2026-01-01",
    )
    monkeypatch.setenv("VISION_API_KEY", "key")
    monkeypatch.setenv("VISION_MODEL", "model")

    settings = load_settings()

    assert settings.base_url.endswith("/responses?api-version=2026-01-01")


def test_load_settings_reports_missing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "VISION_BASE_URL",
        "VISION_API_KEY",
        "VISION_MODEL",
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ConfigurationError, match="VISION_BASE_URL"):
        load_settings()


@pytest.mark.parametrize("timeout", ["zero", "0", "-1"])
def test_load_settings_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch, timeout: str
) -> None:
    monkeypatch.setenv("VISION_BASE_URL", "https://vision.example/v1")
    monkeypatch.setenv("VISION_API_KEY", "key")
    monkeypatch.setenv("VISION_MODEL", "model")
    monkeypatch.setenv("VISION_TIMEOUT", timeout)

    with pytest.raises(ConfigurationError, match="VISION_TIMEOUT"):
        load_settings()
