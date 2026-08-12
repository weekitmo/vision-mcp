#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG_DIR="${PROJECT_ROOT}/.inspector"
CATALOG_FILE="${CATALOG_DIR}/mcp.json"
CATALOG_EXAMPLE="${CATALOG_DIR}/mcp.json.example"
INSPECTOR_VERSION="2.1.0"

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

command -v uv >/dev/null 2>&1 || die "uv is required: https://docs.astral.sh/uv/"
command -v node >/dev/null 2>&1 || die "Node.js is required by MCP Inspector."
command -v npx >/dev/null 2>&1 || die "npx is required by MCP Inspector."

cd "${PROJECT_ROOT}"

if [[ ! -f "${CATALOG_EXAMPLE}" ]]; then
  die "Inspector catalog template is missing: ${CATALOG_EXAMPLE}"
fi

if [[ ! -f "${CATALOG_FILE}" ]]; then
  mkdir -p "${CATALOG_DIR}"
  cp "${CATALOG_EXAMPLE}" "${CATALOG_FILE}"
  chmod 600 "${CATALOG_FILE}"
  printf 'Created writable Inspector catalog: %s\n' "${CATALOG_FILE}"
fi

printf 'Checking Python dependencies...\n'
uv sync --group dev

printf '\nStarting MCP Inspector %s. Press Ctrl+C to stop it.\n' "${INSPECTOR_VERSION}"
printf 'The browser should open automatically; otherwise use the URL printed below.\n\n'
printf 'In the UI, edit "vision-local" and fill its Environment Variables:\n'
printf '  VISION_BASE_URL, VISION_API_KEY, VISION_MODEL, VISION_TIMEOUT\n\n'

export npm_config_yes=true
exec npx --yes "@modelcontextprotocol/inspector@${INSPECTOR_VERSION}" \
  --web \
  --catalog "${CATALOG_FILE}"
