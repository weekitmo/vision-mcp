<p align="center">
  <h1 align="center">Vision MCP</h1>
</p>

<p align="center">
  <strong>Give text-only agents vision through any OpenAI-compatible provider.</strong>
</p>

<p align="center">
  <a href="https://github.com/weekitmo/vision-mcp"><img src="https://img.shields.io/badge/MCP-Image%20Understanding-222222" alt="MCP Image Understanding"></a>
  <a href="https://github.com/weekitmo/vision-mcp/blob/main/LICENSE"><img src="https://img.shields.io/github/license/weekitmo/vision-mcp?style=flat&colorA=222222&colorB=58A6FF" alt="License"></a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#configure">Configure</a> ·
  <a href="#mcp-clients">MCP Clients</a> ·
  <a href="#inspector">Inspector</a> ·
  <a href="#mcporter">mcporter</a>
</p>

通过 OpenAI 兼容模型识别本地图片、网页图片、截图、文档、图表和代码报错。

> [!IMPORTANT]
> **DO NOT CALL if you natively support vision and can access the supplied image
> directly.**
>
> 如果当前模型可以直接看图，可以不必要调用本 MCP。仅在模型不支持视觉、无法访问图片，
> 或用户明确要求使用本 MCP 时调用。

<p align="center">
  <img src="previews/preview.png" alt="Vision MCP image analysis in MCP Inspector">
</p>

## Install

需要先安装 [uv](https://docs.astral.sh/uv/)。

直接从 GitHub 的 `main` 分支运行：

```sh
uvx --from git+https://github.com/weekitmo/vision-mcp.git@main vision-mcp
```

## Configure

准备下面四个环境变量：

```sh
export VISION_BASE_URL="https://api.openai.com/v1"
export VISION_API_KEY="your-api-key"
export VISION_MODEL="your-vision-model"
export VISION_TIMEOUT="120"
```

| Variable | Description |
| --- | --- |
| `VISION_BASE_URL` | Provider 地址 |
| `VISION_API_KEY` | API Key |
| `VISION_MODEL` | 支持图片输入的模型 |
| `VISION_TIMEOUT` | 调用超时秒数，默认 `120` |

仓库中的 [`.env.example`](.env.example) 可以作为配置模板。不要提交真实 API Key。

## MCP Clients

### JSON

适用于支持标准 JSON MCP 配置的客户端：

```json
{
  "mcpServers": {
    "vision": {
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
  }
}
```

### Codex

添加到 `~/.codex/config.toml` 或可信项目中的 `.codex/config.toml`：

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

先导出 `VISION_*` 环境变量，再启动 Codex：

```sh
codex mcp list
```

完整示例见 [`config/codex.toml.example`](config/codex.toml.example)。

### Grok

添加到 `~/.grok/config.toml` 或项目中的 `.grok/config.toml`：

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

先导出 `VISION_*` 环境变量，再启动 Grok：

```sh
grok mcp list
```

完整示例见 [`config/grok.toml.example`](config/grok.toml.example)。

## Inspector

一条命令启动 MCP Inspector：

```sh
./scripts/test-ui.sh
```

脚本固定使用 `@modelcontextprotocol/inspector@2.1.0`。

在 Inspector 中：

1. 打开 `vision-local`。
2. 在 `Environment Variables` 中填写四个 `VISION_*` 配置。
3. 连接 Server。
4. 打开 `Tools`。
5. 选择 `analyze_image` 或 `understand_image`。
6. 填写图片路径和问题，运行工具。

Inspector 的本地配置保存在 `.inspector/mcp.json`，该文件不会被 Git 提交。

## mcporter

初始化项目配置：

```sh
./scripts/setup-mcporter.sh
```

查看工具：

```sh
mcporter list vision --schema --all-parameters
```

识别一张图片：

```sh
mcporter call vision.analyze_image \
  image=/absolute/path/to/screenshot.png \
  prompt="提取图片中的所有文字" \
  mode=ocr \
  detail=high \
  --timeout 120000
```

比较多张图片：

```sh
mcporter call vision.understand_image \
  --args '{
    "images": [
      "/absolute/path/before.png",
      "/absolute/path/after.png"
    ],
    "prompt": "比较两张图片的差异",
    "mode": "compare"
  }' \
  --timeout 120000 \
  --output json
```

查看内置使用说明：

```sh
mcporter resource vision
mcporter resource vision vision://docs/quickstart
mcporter resource vision vision://docs/tools
```

## Tools

### `analyze_image`

用于识别单张图片，适合 Inspector、mcporter 和命令行调用。

```text
image       本地路径、HTTP(S) URL 或 data URL
prompt      希望模型回答的问题
mode        识别模式
ascii_mode  是否使用 ASCII 表达布局
detail      图片解析精度
max_tokens  最大输出长度
```

### `understand_image`

用于多图识别、图片比较，以及需要兼容不同图片参数格式的客户端。

```text
images      图片列表
prompt      希望模型回答的问题
mode        识别模式
ascii_mode  是否使用 ASCII 表达布局
detail      图片解析精度
max_tokens  最大输出长度
```

可用模式：

`auto` · `describe` · `ocr` · `document` · `ui` · `chart` · `compare` ·
`spatial` · `code`

支持 PNG、JPEG、WEBP 和 GIF。单次最多识别 10 张图片。

## From Source

需要修改或调试时：

```sh
git clone https://github.com/weekitmo/vision-mcp.git
cd vision-mcp
uv sync --frozen
uv run vision-mcp
```

在 MCP 客户端中从源码启动：

```json
{
  "mcpServers": {
    "vision": {
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
  }
}
```

## License

MIT
