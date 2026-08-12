from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mcp.server.mcpserver import MCPServer


@dataclass(frozen=True, slots=True)
class DocumentationResource:
    uri: str
    name: str
    title: str
    description: str
    reader: Callable[[], str]


def quickstart() -> str:
    return """\
# OpenAI Vision MCP quickstart

This server exposes image understanding through OpenAI-compatible Responses or Chat
Completions APIs.

## Mandatory routing rule

**DO NOT CALL if you natively support vision and can access the supplied image
directly.** Call this MCP only when native vision is unavailable, the image source is
inaccessible to the client's native vision capability, or the user explicitly requests
this MCP or its configured provider.

## Required provider settings

Set these variables in the MCP client's server environment:

```bash
VISION_BASE_URL=https://api.openai.com/v1
VISION_API_KEY=your-api-key
VISION_MODEL=your-vision-model
VISION_TIMEOUT=120
```

`VISION_TIMEOUT` is optional and defaults to 120 seconds. The server also accepts the
equivalent `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_TIMEOUT`
aliases. `VISION_*` takes precedence.

## Run from source

```bash
uv sync
uv run vision-mcp
```

The command starts a stdio MCP server and is normally launched by an MCP client rather
than used interactively.

## Test with MCP Inspector

```bash
./scripts/test-ui.sh
```

Edit the `vision-local` server in Inspector and set the four `VISION_*` variables in its
Environment Variables section.

## Choose a tool

- `analyze_image`: one image; recommended for mcporter and shell calls.
- `understand_image`: multiple images and compatibility input aliases.

Read `vision://docs/tools` for image inputs and prompt modes.
"""


def configuration() -> str:
    return """\
# Provider configuration

The server reads provider settings only when an image tool is called. Documentation
resources can be listed and read without a configured vision provider.

| Variable | Required | Meaning |
| --- | --- | --- |
| `VISION_BASE_URL` | yes | Service root, full `/responses` URL, or full `/chat/completions` URL |
| `VISION_API_KEY` | yes | Provider API key |
| `VISION_MODEL` | yes | Model identifier that accepts image input |
| `VISION_TIMEOUT` | no | Upstream request timeout in seconds; default `120` |

OpenAI-compatible aliases are accepted: `OPENAI_BASE_URL`, `OPENAI_API_KEY`,
`OPENAI_MODEL`, and `OPENAI_TIMEOUT`. `VISION_*` values take precedence.

## Endpoint selection

- A URL ending in `/responses` uses only the Responses API.
- A URL ending in `/chat/completions` uses only Chat Completions.
- A service root such as `https://api.openai.com/v1` tries Responses first and falls
  back to Chat Completions only when the Responses endpoint is unavailable.

Full endpoint URLs may include provider-required query parameters.

## Environment handling

MCP clients do not necessarily load a project `.env` file. Put the variables in the
client's MCP server configuration, export them in the parent shell, or explicitly run:

```bash
uv run --env-file .env vision-mcp
```

Use `.env.example` as a template. Never place a real API key in a committed config file.
This resource contains placeholders only and never reads the process environment.
"""


def tools() -> str:
    return """\
# Image tools and built-in prompts

## Mandatory routing rule

**DO NOT CALL if you natively support vision and can access the supplied image
directly.** This MCP is a fallback or explicitly requested provider bridge, not a second
vision pass for an already vision-capable model.

Call a tool only when at least one condition is true:

- The calling model or client has no native vision capability.
- Native vision cannot access the image source, such as a local path available only to
  this MCP process.
- The user explicitly requests this MCP or the provider configured through `VISION_*`.

## `analyze_image`

Use for one local image path, HTTP(S) image URL, or image data URL. The required
`image` string gives it a simple schema for CLI clients such as mcporter.

## `understand_image`

Use for multiple images, comparisons, or clients that prefer singular/plural path and
URL fields. The preferred input is `images`; `image_path`, `image_url`, `image_paths`,
and `image_urls` are also accepted.

## Built-in prompt modes

Every tool call combines a factual base system prompt with one selected mode:

| Mode | Intended use |
| --- | --- |
| `auto` | Select useful coverage from the caller's request |
| `describe` | Subjects, setting, composition, visible text, and uncertainty |
| `ocr` | Careful transcription with line and table structure |
| `document` | Headings, fields, values, tables, dates, totals, and annotations |
| `ui` | Screenshots, controls, states, notifications, and exact UI text |
| `chart` | Axes, units, legends, visible values, trends, and caveats |
| `compare` | Shared content and differences across ordered images |
| `spatial` | Relative positions, containment, and hierarchy |
| `code` | Code, terminal, log, and error screenshots |

The caller's `prompt` remains the actual question. `system_prompt` appends extra caller
instructions without replacing the built-in factuality rules.

## ASCII rendering

- `ascii_mode=auto`: add a compact ASCII-only layout only when prose is insufficient.
- `ascii_mode=always`: always include an approximate labeled ASCII representation.
- `ascii_mode=never`: never include ASCII art or a layout diagram.

Supported image formats are PNG, JPEG, WEBP, and GIF. A local image or data URL is
limited to 20 MiB, and one call accepts at most 10 images.
"""


def mcporter() -> str:
    return """\
# mcporter usage

From the project root, initialize the project-local mcporter config:

```bash
./scripts/setup-mcporter.sh
```

Export provider settings in the shell that launches mcporter:

```bash
export VISION_BASE_URL="https://api.openai.com/v1"
export VISION_API_KEY="your-api-key"
export VISION_MODEL="your-vision-model"
export VISION_TIMEOUT="120"
```

Discover tools and documentation:

```bash
mcporter list vision --schema --all-parameters
mcporter resource vision
mcporter resource vision vision://docs/tools
```

Analyze one local image:

```bash
mcporter call vision.analyze_image \\
  image=/absolute/path/to/screenshot.png \\
  prompt="Extract all visible text" \\
  mode=ocr \\
  detail=high \\
  --timeout 120000
```

Compare multiple images:

```bash
mcporter call vision.understand_image \\
  --args '{
    "images": ["/absolute/path/before.png", "/absolute/path/after.png"],
    "prompt": "Compare these screenshots",
    "mode": "compare"
  }' \\
  --timeout 120000 \\
  --output json
```

mcporter 0.12.0 defaults tool calls to 60 seconds. Vision calls should pass
`--timeout 120000` or set `MCPORTER_CALL_TIMEOUT=120000`. MCP resource reads do not
call the vision provider.
"""


def uvx() -> str:
    return """\
# Git and source installation

Publishing to PyPI is optional. This server can be distributed from a Git repository.

## Clone and run the source

```bash
git clone https://github.com/weekitmo/vision-mcp.git
cd vision-mcp
uv sync --frozen
uv run vision-mcp
```

Use this approach for development, debugging, or local modifications. Example MCP server
definition:

```json
{
  "command": "uv",
  "args": [
    "--directory",
    "/absolute/path/to/vision-mcp",
    "run",
    "--frozen",
    "vision-mcp"
  ],
  "env": {
    "VISION_BASE_URL": "https://api.openai.com/v1",
    "VISION_API_KEY": "your-api-key",
    "VISION_MODEL": "your-vision-model",
    "VISION_TIMEOUT": "120"
  }
}
```

## Run directly from Git with uvx

This does not require a PyPI release or a manual clone:

```bash
uvx --from git+https://github.com/weekitmo/vision-mcp.git@main vision-mcp
```

This installs and runs the repository's `main` branch. Example JSON MCP server definition:

```json
{
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/weekitmo/vision-mcp.git@main",
    "vision-mcp"
  ],
  "env": {
    "VISION_BASE_URL": "https://api.openai.com/v1",
    "VISION_API_KEY": "your-api-key",
    "VISION_MODEL": "your-vision-model",
    "VISION_TIMEOUT": "120"
  }
}
```

## Codex config.toml

Add this to `~/.codex/config.toml` or a trusted project's `.codex/config.toml`:

```toml
[mcp_servers.vision]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/weekitmo/vision-mcp.git@main",
  "vision-mcp",
]
env_vars = [
  "VISION_BASE_URL",
  "VISION_API_KEY",
  "VISION_MODEL",
  "VISION_TIMEOUT",
]
startup_timeout_sec = 60
tool_timeout_sec = 180
```

Export the `VISION_*` variables before starting Codex. Verify with `codex mcp list`.

## Grok Build config.toml

Add this to `~/.grok/config.toml` or `.grok/config.toml`:

```toml
[mcp_servers.vision]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/weekitmo/vision-mcp.git@main",
  "vision-mcp",
]
enabled = true
startup_timeout_sec = 60
tool_timeout_sec = 180
```

Export the `VISION_*` variables before starting Grok. The stdio server inherits Grok's
process environment, so real API keys do not need to be stored in the TOML file. Verify
with `grok inspect` and `grok mcp doctor vision`.

To distribute without PyPI, push the source to the repository's `main` branch and give
users one of the configurations above.

## Optional PyPI release

Publishing is needed only for the shorter bare-package form:

```bash
uvx openai-vision-mcp
```

The optional publishing flow is `uv build --no-sources` followed by `uv publish`.
"""


DOCUMENTATION_RESOURCES = (
    DocumentationResource(
        uri="vision://docs/quickstart",
        name="quickstart",
        title="Vision MCP Quickstart",
        description="Required configuration, source startup, Inspector, and tool selection.",
        reader=quickstart,
    ),
    DocumentationResource(
        uri="vision://docs/configuration",
        name="configuration",
        title="Provider Configuration",
        description="Environment variables, endpoint selection, and secret handling.",
        reader=configuration,
    ),
    DocumentationResource(
        uri="vision://docs/tools",
        name="tools",
        title="Tools and Built-in Prompts",
        description="Tool selection, image inputs, prompt modes, and ASCII behavior.",
        reader=tools,
    ),
    DocumentationResource(
        uri="vision://docs/mcporter",
        name="mcporter",
        title="mcporter Usage",
        description="Configure, discover, and call this MCP with mcporter.",
        reader=mcporter,
    ),
    DocumentationResource(
        uri="vision://docs/uvx",
        name="uvx",
        title="Source and uvx Execution",
        description="Run from source, PyPI, or an unpublished Git repository.",
        reader=uvx,
    ),
)


def register_resources(server: MCPServer[Any]) -> None:
    for document in DOCUMENTATION_RESOURCES:
        server.resource(
            document.uri,
            name=document.name,
            title=document.title,
            description=document.description,
            mime_type="text/markdown",
        )(document.reader)
