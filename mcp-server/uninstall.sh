#!/usr/bin/env bash
# Preview or remove only the globally owned ClineFlow MCP runtime and entries.
set -euo pipefail

STATE_HOME=${CLINEFLOW_MCP_HOME:-${XDG_STATE_HOME:-$HOME/.local/state}/clineflow-mcp}
case "$STATE_HOME" in
  /*) ;;
  *) echo "ERROR: CLINEFLOW_MCP_HOME must be an absolute path." >&2; exit 1 ;;
esac
[ "$(basename "$STATE_HOME")" = clineflow-mcp ] || { echo "ERROR: refusing to remove a non-ClineFlow MCP directory." >&2; exit 1; }
MODE=${1:-}
case "$MODE" in
  --dry-run|'') ;;
  --yes) ;;
  --help|-h)
    echo "Usage: uninstall.sh [--dry-run|--yes]"
    exit 0
    ;;
  *) echo "Usage: uninstall.sh [--dry-run|--yes]" >&2; exit 2 ;;
esac

command -v uv >/dev/null 2>&1 || { echo "ERROR: uv is required to remove the global MCP runtime." >&2; exit 1; }
BIN=$(uv tool dir --bin)
COMMAND="$BIN/clineflow-mcp"
if [ ! -x "$COMMAND" ]; then
  echo "ClineFlow MCP runtime is not installed. No global runtime was removed."
  exit 0
fi

echo "ClineFlow MCP global-removal plan:"
CLINEFLOW_MCP_COMMAND="$BIN/clineflow-mcp-server" "$COMMAND" uninstall
echo "  - remove only the globally owned clineflow-mcp runtime"
echo "  - remove only $STATE_HOME"
echo "  - preserve every project .clineflow-mcp/ workspace and all ClineFlow knowledge"
if [ "$MODE" != --yes ]; then
  echo "Preview only. Re-run with --yes after explicit authorization."
  exit 0
fi

CLINEFLOW_MCP_COMMAND="$BIN/clineflow-mcp-server" "$COMMAND" uninstall --apply --yes
uv tool uninstall clineflow-mcp
rm -rf "$STATE_HOME"
echo "Removed the global ClineFlow MCP runtime. Project workspaces were preserved."
