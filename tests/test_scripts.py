from pathlib import Path


def test_inspector_script_uses_an_exact_pinned_version() -> None:
    script = Path("scripts/test-ui.sh").read_text()

    assert 'INSPECTOR_VERSION="2.1.0"' in script
    assert '"@modelcontextprotocol/inspector@${INSPECTOR_VERSION}"' in script
    assert "@modelcontextprotocol/inspector@latest" not in script
