from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, cast
from urllib.parse import SplitResult, urlsplit, urlunsplit

import httpx

from openai_vision_mcp.config import Settings

ImageDetail = Literal["auto", "low", "high", "original"]


class APIStyle(str, Enum):
    RESPONSES = "responses"
    CHAT_COMPLETIONS = "chat_completions"


@dataclass(frozen=True, slots=True)
class Endpoint:
    style: APIStyle
    url: str


class VisionAPIError(RuntimeError):
    """Raised when the upstream vision provider cannot return usable text."""


def resolve_endpoints(base_url: str) -> list[Endpoint]:
    normalized = base_url.rstrip("/")
    parsed = urlsplit(normalized)
    path = parsed.path.rstrip("/")
    if path.endswith("/responses"):
        return [Endpoint(APIStyle.RESPONSES, normalized)]
    if path.endswith("/chat/completions"):
        return [Endpoint(APIStyle.CHAT_COMPLETIONS, normalized)]
    return [
        Endpoint(APIStyle.RESPONSES, _append_endpoint(parsed, "responses")),
        Endpoint(APIStyle.CHAT_COMPLETIONS, _append_endpoint(parsed, "chat/completions")),
    ]


def _append_endpoint(parsed: SplitResult, suffix: str) -> str:
    path = f"{parsed.path.rstrip('/')}/{suffix}"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def build_responses_payload(
    *,
    model: str,
    images: list[str],
    prompt: str,
    system_prompt: str,
    detail: ImageDetail,
    max_tokens: int,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    content.extend(
        {"type": "input_image", "image_url": image, "detail": detail} for image in images
    )
    return {
        "model": model,
        "instructions": system_prompt,
        "input": [{"role": "user", "content": content}],
        "max_output_tokens": max_tokens,
    }


def build_chat_completions_payload(
    *,
    model: str,
    images: list[str],
    prompt: str,
    system_prompt: str,
    detail: ImageDetail,
    max_tokens: int,
    use_completion_tokens: bool = False,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    content.extend(
        {
            "type": "image_url",
            "image_url": {"url": image, "detail": detail},
        }
        for image in images
    )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
    }
    payload["max_completion_tokens" if use_completion_tokens else "max_tokens"] = max_tokens
    return payload


def parse_responses_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    texts: list[str] = []
    output: object = data.get("output")
    if isinstance(output, list):
        for item in cast(list[object], output):
            if not isinstance(item, dict):
                continue
            typed_item = cast(dict[str, object], item)
            content = typed_item.get("content")
            if not isinstance(content, list):
                continue
            for part in cast(list[object], content):
                if not isinstance(part, dict):
                    continue
                typed_part = cast(dict[str, object], part)
                if typed_part.get("type") not in {"output_text", "text"}:
                    continue
                text = typed_part.get("text")
                if isinstance(text, str) and text:
                    texts.append(text)
    if texts:
        return "\n".join(texts)
    raise VisionAPIError("Responses API returned no text output.")


def parse_chat_completions_text(data: dict[str, Any]) -> str:
    choices: object = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise VisionAPIError("Chat Completions API returned no choices.")
    first_choice = cast(dict[str, object], choices[0])
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise VisionAPIError("Chat Completions API returned no message.")

    typed_message = cast(dict[str, object], message)
    content = typed_message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        texts: list[str] = []
        for part in cast(list[object], content):
            if not isinstance(part, dict):
                continue
            typed_part = cast(dict[str, object], part)
            text = typed_part.get("text")
            if typed_part.get("type") in {"text", "output_text"} and isinstance(text, str):
                texts.append(text)
        if texts:
            return "\n".join(texts)
    raise VisionAPIError("Chat Completions API returned no text content.")


def _response_summary(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:2000]
    return json.dumps(payload, ensure_ascii=False)[:2000]


def _endpoint_is_unavailable(response: httpx.Response) -> bool:
    if response.status_code in {404, 405, 501}:
        return True
    if response.status_code != 400:
        return False

    body = response.text.lower()
    endpoint_words = ("endpoint", "route", "path", "url")
    unavailable_words = ("not found", "unknown", "unsupported", "not implemented")
    return any(word in body for word in endpoint_words) and any(
        word in body for word in unavailable_words
    )


def _requires_completion_tokens(response: httpx.Response) -> bool:
    if response.status_code != 400:
        return False
    body = response.text.lower()
    return "max_tokens" in body and "max_completion_tokens" in body


class VisionClient:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    async def analyze(
        self,
        *,
        images: list[str],
        prompt: str,
        system_prompt: str,
        detail: ImageDetail,
        max_tokens: int,
    ) -> str:
        endpoints = resolve_endpoints(self.settings.base_url)
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "api-key": self.settings.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                headers=headers,
                timeout=self.settings.timeout,
                transport=self.transport,
            ) as client:
                for index, endpoint in enumerate(endpoints):
                    response = await self._post(
                        client=client,
                        endpoint=endpoint,
                        images=images,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        detail=detail,
                        max_tokens=max_tokens,
                    )
                    if response.status_code < 400:
                        return self._parse_success(endpoint.style, response)
                    if index + 1 < len(endpoints) and _endpoint_is_unavailable(response):
                        continue
                    raise self._http_error(endpoint, response)
        except httpx.TimeoutException as exc:
            raise VisionAPIError(
                f"Vision API request timed out after {self.settings.timeout:g} seconds."
            ) from exc
        except httpx.HTTPError as exc:
            raise VisionAPIError(f"Vision API request failed: {exc}") from exc

        raise VisionAPIError("No compatible vision API endpoint was available.")

    async def _post(
        self,
        *,
        client: httpx.AsyncClient,
        endpoint: Endpoint,
        images: list[str],
        prompt: str,
        system_prompt: str,
        detail: ImageDetail,
        max_tokens: int,
    ) -> httpx.Response:
        if endpoint.style is APIStyle.RESPONSES:
            payload = build_responses_payload(
                model=self.settings.model,
                images=images,
                prompt=prompt,
                system_prompt=system_prompt,
                detail=detail,
                max_tokens=max_tokens,
            )
            return await client.post(endpoint.url, json=payload)

        payload = build_chat_completions_payload(
            model=self.settings.model,
            images=images,
            prompt=prompt,
            system_prompt=system_prompt,
            detail=detail,
            max_tokens=max_tokens,
        )
        response = await client.post(endpoint.url, json=payload)
        if _requires_completion_tokens(response):
            payload = build_chat_completions_payload(
                model=self.settings.model,
                images=images,
                prompt=prompt,
                system_prompt=system_prompt,
                detail=detail,
                max_tokens=max_tokens,
                use_completion_tokens=True,
            )
            response = await client.post(endpoint.url, json=payload)
        return response

    @staticmethod
    def _parse_success(style: APIStyle, response: httpx.Response) -> str:
        try:
            raw_data: object = response.json()
        except ValueError as exc:
            raise VisionAPIError(
                f"Vision API returned invalid JSON from {response.request.url}: "
                f"{response.text[:2000]}"
            ) from exc
        if not isinstance(raw_data, dict):
            raise VisionAPIError("Vision API returned a JSON value that is not an object.")
        data = cast(dict[str, Any], raw_data)
        if style is APIStyle.RESPONSES:
            return parse_responses_text(data)
        return parse_chat_completions_text(data)

    def _http_error(self, endpoint: Endpoint, response: httpx.Response) -> VisionAPIError:
        return VisionAPIError(
            f"Vision API returned HTTP {response.status_code} for {endpoint.url} "
            f"using model {self.settings.model!r}: {_response_summary(response)}"
        )
