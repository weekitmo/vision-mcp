from openai_vision_mcp.prompts import build_prompts


def test_build_prompts_uses_mode_ascii_and_custom_instructions() -> None:
    system, prompt = build_prompts(
        prompt="Read the selected row",
        mode="ui",
        ascii_mode="always",
        system_prompt="Answer in Chinese.",
    )

    assert "user interface" in system
    assert "ASCII-only" in system
    assert "Answer in Chinese." in system
    assert prompt == "Read the selected row"


def test_build_prompts_supplies_default_request() -> None:
    _, prompt = build_prompts(
        prompt=" ",
        mode="auto",
        ascii_mode="never",
        system_prompt=None,
    )

    assert prompt == "Analyze the supplied image(s)."
