#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${PROJECT_ROOT}/config"
CONFIG_FILE="${CONFIG_DIR}/mcporter.json"
CONFIG_EXAMPLE="${CONFIG_DIR}/mcporter.json.example"

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

command -v mcporter >/dev/null 2>&1 || die "mcporter is required: https://mcporter.dev"
[[ -f "${CONFIG_EXAMPLE}" ]] || die "Missing config template: ${CONFIG_EXAMPLE}"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  mkdir -p "${CONFIG_DIR}"
  cp "${CONFIG_EXAMPLE}" "${CONFIG_FILE}"
  chmod 600 "${CONFIG_FILE}"
  printf 'Created %s\n' "${CONFIG_FILE}"
else
  printf 'Using existing %s\n' "${CONFIG_FILE}"
fi

printf '\nExport the provider settings before using mcporter:\n'
printf '  export VISION_BASE_URL="https://api.openai.com/v1"\n'
printf '  export VISION_API_KEY="your-api-key"\n'
printf '  export VISION_MODEL="your-vision-model"\n'
printf '  export VISION_TIMEOUT="120"\n\n'
printf 'Then inspect or call the server:\n'
printf '  mcporter list vision --schema --all-parameters\n'
printf '  mcporter resource vision\n'
printf '  mcporter resource vision vision://docs/mcporter\n'
printf '  mcporter call vision.analyze_image image=/absolute/path/image.png \\\n'
printf '    prompt="Describe this image" --timeout 120000\n'
