from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from openai_vision_mcp import __version__
from openai_vision_mcp.client import ImageDetail, VisionClient
from openai_vision_mcp.config import load_settings
from openai_vision_mcp.images import build_image_inputs
from openai_vision_mcp.prompts import AsciiMode, PromptMode, build_prompts
from openai_vision_mcp.resources import register_resources

NATIVE_VISION_ROUTING_GUARD = (
    "DO NOT CALL if you natively support vision and can access the supplied image "
    "directly. Call this MCP only when native vision is unavailable, the image source "
    "is inaccessible to your native vision capability, or the user explicitly requests "
    "this MCP or its configured provider."
)

ANALYZE_IMAGE_DESCRIPTION = (
    f"{NATIVE_VISION_ROUTING_GUARD}\n\n"
    "Analyze one local image path, HTTP(S) image URL, or image data URL. This "
    "CLI-friendly single-image tool is the simplest entry point for mcporter and shell "
    "automation. Use understand_image for multiple images."
)

UNDERSTAND_IMAGE_DESCRIPTION = (
    f"{NATIVE_VISION_ROUTING_GUARD}\n\n"
    "Understand one or more images for description, OCR, document extraction, UI "
    "inspection, chart reading, comparison, spatial reasoning, or code/error screenshot "
    "analysis. Inputs may be local paths, HTTP(S) URLs, or image data URLs. Built-in "
    "prompt modes and optional ASCII rendering are available."
)

mcp = MCPServer(
    name="openai-vision-mcp",
    version=__version__,
    instructions=(
        f"{NATIVE_VISION_ROUTING_GUARD} If this MCP is required, use analyze_image for "
        "one image and understand_image for multiple images or compatibility inputs. "
        "Read the vision://docs/quickstart, vision://docs/configuration, "
        "vision://docs/tools, vision://docs/mcporter, and vision://docs/uvx resources "
        "for setup and usage help."
    ),
)
register_resources(mcp)


def _validate_max_tokens(max_tokens: int) -> None:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero.")
    if max_tokens > 65536:
        raise ValueError("max_tokens must not exceed 65536.")


async def _analyze(
    *,
    image_inputs: list[str],
    prompt: str | None,
    mode: PromptMode,
    ascii_mode: AsciiMode,
    detail: ImageDetail,
    max_tokens: int,
    system_prompt: str | None,
) -> str:
    _validate_max_tokens(max_tokens)
    effective_system_prompt, effective_prompt = build_prompts(
        prompt=prompt,
        mode=mode,
        ascii_mode=ascii_mode,
        system_prompt=system_prompt,
    )
    client = VisionClient(load_settings())
    return await client.analyze(
        images=image_inputs,
        prompt=effective_prompt,
        system_prompt=effective_system_prompt,
        detail=detail,
        max_tokens=max_tokens,
    )


@mcp.tool(description=ANALYZE_IMAGE_DESCRIPTION, structured_output=False)
async def analyze_image(
    image: str,
    prompt: str = "Analyze the supplied image.",
    mode: PromptMode = "auto",
    ascii_mode: AsciiMode = "auto",
    detail: ImageDetail = "auto",
    max_tokens: int = 8192,
    system_prompt: str = "",
) -> str:
    """Analyze one image using a CLI-friendly schema.

    DO NOT CALL if you natively support vision and can access the image directly.
    Use this tool for a single local image path, HTTP(S) image URL, or image data URL.
    It is the simplest entry point for mcporter and shell automation. Use
    `understand_image` when comparing or analyzing multiple images in one call.
    """

    image_inputs = build_image_inputs(images=[image])
    return await _analyze(
        image_inputs=image_inputs,
        prompt=prompt,
        mode=mode,
        ascii_mode=ascii_mode,
        detail=detail,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )


@mcp.tool(description=UNDERSTAND_IMAGE_DESCRIPTION, structured_output=False)
async def understand_image(
    prompt: str | None = None,
    images: list[str] | None = None,
    image_path: str | None = None,
    image_url: str | None = None,
    image_paths: list[str] | None = None,
    image_urls: list[str] | None = None,
    mode: PromptMode = "auto",
    ascii_mode: AsciiMode = "auto",
    detail: ImageDetail = "auto",
    max_tokens: int = 8192,
    system_prompt: str | None = None,
) -> str:
    """Understand one or more images with an OpenAI-compatible vision model.

    DO NOT CALL if you natively support vision and can access the images directly.
    Use this tool for image description, OCR, document extraction, screenshot and UI
    inspection, chart reading, visual comparisons, spatial reasoning, and code/error
    screenshots. The `images` list accepts local paths, HTTP(S) URLs, or image data URLs.
    The singular/plural path and URL fields are compatibility aliases and can be mixed.

    Set `mode` to select a built-in analysis prompt. Set `ascii_mode` to `always` when a
    text-only spatial rendering is required, or leave it on `auto` so the model uses ASCII
    only when it materially clarifies the image.
    """

    image_inputs = build_image_inputs(
        images=images,
        image_path=image_path,
        image_url=image_url,
        image_paths=image_paths,
        image_urls=image_urls,
    )
    return await _analyze(
        image_inputs=image_inputs,
        prompt=prompt,
        mode=mode,
        ascii_mode=ascii_mode,
        detail=detail,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
