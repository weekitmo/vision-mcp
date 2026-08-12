from __future__ import annotations

from typing import Literal

PromptMode = Literal[
    "auto",
    "describe",
    "ocr",
    "document",
    "ui",
    "chart",
    "compare",
    "spatial",
    "code",
]
AsciiMode = Literal["auto", "always", "never"]

BASE_SYSTEM_PROMPT = """\
You are a meticulous image-understanding specialist. Analyze only what is visible in the
provided images. Separate direct observations from inference, never invent unreadable text
or hidden details, and state uncertainty precisely. Preserve exact spelling, capitalization,
numbers, punctuation, and line breaks when transcribing text. Refer to multiple images as
Image 1, Image 2, and so on, in the order supplied."""

MODE_PROMPTS: dict[PromptMode, str] = {
    "auto": (
        "Determine the most useful analysis for the user's request. Cover relevant visible "
        "content, text, layout, relationships, and anomalies without padding the answer."
    ),
    "describe": (
        "Describe the image systematically: main subjects, setting, actions, visible text, "
        "composition, notable details, and any uncertainty."
    ),
    "ocr": (
        "Perform careful OCR. Transcribe all readable text in natural reading order. Preserve "
        "line breaks and table structure where practical. Mark uncertain characters with [?] "
        "and describe illegible regions instead of guessing."
    ),
    "document": (
        "Analyze this document image. Extract headings, paragraphs, fields, values, tables, "
        "dates, identifiers, totals, and annotations while preserving their relationships."
    ),
    "ui": (
        "Inspect this user interface or screenshot. Identify the app/page, layout regions, "
        "controls, labels, current states, selected items, errors, notifications, data shown, "
        "and likely interaction implications. Quote important UI text exactly."
    ),
    "chart": (
        "Analyze the chart or data visualization. Identify title, axes, units, scales, legend, "
        "series, values that can be read, trends, extrema, comparisons, and visual caveats. "
        "Do not fabricate values between visible marks."
    ),
    "compare": (
        "Compare the supplied images in order. First summarize what is shared, then enumerate "
        "specific visual, textual, layout, state, and content differences with image labels."
    ),
    "spatial": (
        "Explain the spatial layout and relative positions of important objects or regions. "
        "Use clear directional and containment language and preserve the overall hierarchy."
    ),
    "code": (
        "Inspect the code, terminal, log, or error screenshot. Transcribe relevant content in "
        "monospace blocks, preserve indentation when visible, identify the failure, and explain "
        "only conclusions supported by the screenshot."
    ),
}

ASCII_PROMPTS: dict[AsciiMode, str] = {
    "auto": (
        "When prose cannot clearly preserve a meaningful visual or spatial arrangement, add a "
        "compact ASCII-only diagram in a fenced text block. Use plain ASCII characters, label "
        "important regions, and note that positions are approximate. Omit it when it adds no value."
    ),
    "always": (
        "Include a compact ASCII-only representation of the important visual layout in a fenced "
        "text block. Use only plain ASCII characters, label important regions, and state that "
        "positions and scale are approximate."
    ),
    "never": "Do not include ASCII art or an ASCII layout diagram.",
}


def build_prompts(
    *,
    prompt: str | None,
    mode: PromptMode,
    ascii_mode: AsciiMode,
    system_prompt: str | None,
) -> tuple[str, str]:
    user_request = prompt.strip() if prompt and prompt.strip() else "Analyze the supplied image(s)."
    system_parts = [
        BASE_SYSTEM_PROMPT,
        MODE_PROMPTS[mode],
        ASCII_PROMPTS[ascii_mode],
    ]
    if system_prompt and system_prompt.strip():
        system_parts.append(f"Additional caller instructions:\n{system_prompt.strip()}")
    return "\n\n".join(system_parts), user_request
