#!/usr/bin/env bash
# Verify the MCP-owned dashboard never writes canonical knowledge.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
UV_CACHE_DIR=${UV_CACHE_DIR:-/private/tmp/clineflow-mcp-uv-cache}
export UV_CACHE_DIR
(cd "$ROOT/mcp-server" && uv run --extra dev pytest tests)
echo "ClineFlow MCP protocol and dashboard boundary tests passed"
