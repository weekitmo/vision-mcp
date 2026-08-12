from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


class ConfigurationError(RuntimeError):
    """Raised when required runtime settings are missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    base_url: str
    api_key: str
    model: str
    timeout: float


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return None


def _validate_base_url(value: str) -> str:
    normalized = value.rstrip("/")
    parsed = urlsplit(normalized)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError(
            "VISION_BASE_URL must be an absolute http(s) URL, for example "
            "https://api.openai.com/v1."
        )
    if parsed.fragment:
        raise ConfigurationError("VISION_BASE_URL must not contain a URL fragment.")

    return normalized


def load_settings() -> Settings:
    """Load the four supported provider settings from environment variables."""

    base_url = _first_env("VISION_BASE_URL", "OPENAI_BASE_URL")
    api_key = _first_env("VISION_API_KEY", "OPENAI_API_KEY")
    model = _first_env("VISION_MODEL", "OPENAI_MODEL")
    timeout_value = _first_env("VISION_TIMEOUT", "OPENAI_TIMEOUT") or "120"

    missing = [
        name
        for name, value in (
            ("VISION_BASE_URL", base_url),
            ("VISION_API_KEY", api_key),
            ("VISION_MODEL", model),
        )
        if not value
    ]
    if missing:
        raise ConfigurationError(
            "Missing required vision provider settings: "
            + ", ".join(missing)
            + ". Set them in the MCP server's env configuration."
        )

    try:
        timeout = float(timeout_value)
    except ValueError as exc:
        raise ConfigurationError("VISION_TIMEOUT must be a number of seconds.") from exc
    if timeout <= 0:
        raise ConfigurationError("VISION_TIMEOUT must be greater than zero.")

    assert base_url is not None
    assert api_key is not None
    assert model is not None
    return Settings(
        base_url=_validate_base_url(base_url),
        api_key=api_key,
        model=model,
        timeout=timeout,
    )
