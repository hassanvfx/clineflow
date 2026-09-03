#!/usr/bin/env bash
# Permanent compatibility entrypoint for every supported ClineFlow updater.
set -euo pipefail
BASE_URL="${CLINEFLOW_BASE_URL:-https://raw.githubusercontent.com/hassanvfx/clineflow/main/template}"
temporary=$(mktemp "${TMPDIR:-/tmp}/clineflow-update-bootstrap-XXXXXX")
cleanup() { rm -f "$temporary"; }
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
if command -v curl >/dev/null 2>&1; then curl -fsSL "$BASE_URL/.clineflow/bin/update" -o "$temporary"
elif command -v wget >/dev/null 2>&1; then wget -q "$BASE_URL/.clineflow/bin/update" -O "$temporary"
else echo "ERROR: curl or wget is required." >&2; exit 1; fi
chmod +x "$temporary"
bash "$temporary" "$@"
