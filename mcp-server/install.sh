#!/usr/bin/env bash
# Install the optional ClineFlow MCP server without changing project data.
set -euo pipefail

SCRIPT_SOURCE=${BASH_SOURCE[0]:-$0}
SOURCE_ROOT=''
if [ -f "$SCRIPT_SOURCE" ]; then
  candidate_root=$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)
  # Source-checkout installation is a development/CI convenience only. A
  # downloaded or piped script must never mistake the target project for the
  # MCP package merely because it also has a pyproject.toml.
  if [ -f "$candidate_root/pyproject.toml" ] && [ -d "$candidate_root/src/clineflow_mcp" ] && [ -f "$candidate_root/release-manifest" ]; then
    SOURCE_ROOT=$candidate_root
  fi
fi
STATE_HOME=${CLINEFLOW_MCP_HOME:-${XDG_STATE_HOME:-$HOME/.local/state}/clineflow-mcp}
STATE="$STATE_HOME/state"
DEFAULT_ARTIFACT='https://github.com/hassanvfx/clineflow/releases/download/mcp-v0.1.7/clineflow_mcp-0.1.7-py3-none-any.whl'
[ -z "$SOURCE_ROOT" ] || DEFAULT_ARTIFACT=$SOURCE_ROOT
ARTIFACT=${CLINEFLOW_MCP_ARTIFACT:-$DEFAULT_ARTIFACT}
ARTIFACT_SHA256=${CLINEFLOW_MCP_ARTIFACT_SHA256:-6942066d08bde107558e3f26d6ce86755081b5df93fe695b0320d2aeea617f1f}
RELEASE_VERSION=${CLINEFLOW_MCP_RELEASE_VERSION:-0.1.7}
MODE=${1:-}

usage() {
  cat <<'EOF'
Usage: install.sh [--status|--update|--repair]

Environment for a published install:
  CLINEFLOW_MCP_ARTIFACT        Versioned wheel URL or local wheel path
  CLINEFLOW_MCP_ARTIFACT_SHA256 SHA-256 for that wheel
  CLINEFLOW_MCP_RELEASE_VERSION Published MCP release version
EOF
}

case "$MODE" in ''|--status|--update|--repair|--dry-run) ;; --help|-h) usage; exit 0 ;; *) usage >&2; exit 2 ;; esac
command -v uv >/dev/null 2>&1 || { echo "ERROR: uv is required; install uv and retry." >&2; exit 1; }
BIN=$(uv tool dir --bin)
COMMAND="$BIN/clineflow-mcp"
SERVER="$BIN/clineflow-mcp-server"
LOCK="$STATE_HOME.bootstrap-lock"
mkdir -p "$(dirname "$STATE_HOME")"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "ERROR: another ClineFlow MCP bootstrap is active; wait for it to finish and retry." >&2
  exit 1
fi
cleanup_lock() { rmdir "$LOCK" 2>/dev/null || true; }
trap cleanup_lock EXIT HUP INT TERM

launcher_healthy() {
  [ -x "$COMMAND" ] && [ -x "$SERVER" ] || return 1
  actual_version=$("$COMMAND" --version 2>/dev/null) || return 1
  [ "$actual_version" = "$RELEASE_VERSION" ]
}

classify() {
  if [ ! -e "$STATE" ] && [ ! -e "$COMMAND" ] && [ ! -e "$SERVER" ]; then echo absent; return; fi
  if [ -f "$STATE" ] && launcher_healthy; then
    installed=$(sed -n 's/^release_version=//p' "$STATE" | head -n1)
    [ "$installed" = "$RELEASE_VERSION" ] && { echo healthy; return; }
    echo outdated; return
  fi
  echo corrupt
}

STATE_KIND=$(classify)
if [ "$MODE" = --status ]; then
  printf '{"status":"%s","launcher":"%s","server":"%s"}\n' "$STATE_KIND" "$COMMAND" "$SERVER"
  exit 0
fi
if [ "$MODE" = --dry-run ]; then
  printf '{"status":"%s","launcher":"%s","server":"%s","action":"%s"}\n' "$STATE_KIND" "$COMMAND" "$SERVER" "install-if-absent"
  echo "Dry run: no global runtime or client configuration was changed."
  exit 0
fi
case "$STATE_KIND" in
  healthy) CLINEFLOW_MCP_COMMAND="$SERVER" "$COMMAND" setup --apply --yes; echo "ClineFlow MCP is already healthy."; exit 0 ;;
  outdated) [ "$MODE" = --update ] || { echo "ERROR: MCP server is outdated; rerun with --update." >&2; exit 1; } ;;
  corrupt) [ "$MODE" = --repair ] || { echo "ERROR: MCP server state is corrupt; rerun with --repair." >&2; exit 1; } ;;
esac

install_source=$ARTIFACT
temporary=''
cleanup() { [ -z "$temporary" ] || rm -rf "$temporary"; cleanup_lock; }
trap cleanup EXIT HUP INT TERM
case "$ARTIFACT" in
  http://*|https://*)
    [ -n "$ARTIFACT_SHA256" ] || { echo "ERROR: a published artifact requires CLINEFLOW_MCP_ARTIFACT_SHA256." >&2; exit 1; }
    command -v curl >/dev/null 2>&1 || { echo "ERROR: curl is required for artifact verification." >&2; exit 1; }
    temporary=$(mktemp -d "${TMPDIR:-/tmp}/clineflow-mcp-install-XXXXXX")
    install_source="$temporary/clineflow-mcp.whl"
    curl --fail --location --silent --show-error "$ARTIFACT" -o "$install_source"
    if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$install_source" | awk '{print $1}'); else actual=$(shasum -a 256 "$install_source" | awk '{print $1}'); fi
    [ "$actual" = "$ARTIFACT_SHA256" ] || { echo "ERROR: MCP artifact checksum mismatch." >&2; exit 1; }
    ;;
  *.whl)
    [ -n "$ARTIFACT_SHA256" ] || { echo "ERROR: a wheel artifact requires CLINEFLOW_MCP_ARTIFACT_SHA256." >&2; exit 1; }
    if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$ARTIFACT" | awk '{print $1}'); else actual=$(shasum -a 256 "$ARTIFACT" | awk '{print $1}'); fi
    [ "$actual" = "$ARTIFACT_SHA256" ] || { echo "ERROR: MCP artifact checksum mismatch." >&2; exit 1; }
    ;;
  *)
    [ -n "$SOURCE_ROOT" ] && [ "$ARTIFACT" = "$SOURCE_ROOT" ] || { echo "ERROR: artifact must be a wheel or HTTPS URL." >&2; exit 1; }
    ;;
esac

uv tool install --force "$install_source"
launcher_healthy || { echo "ERROR: the global ClineFlow MCP launcher failed its version health check." >&2; exit 1; }
CLINEFLOW_MCP_COMMAND="$SERVER" "$COMMAND" setup --apply --yes
mkdir -p "$STATE_HOME"
printf 'release_version=%s\nartifact=%s\nartifact_sha256=%s\n' "$RELEASE_VERSION" "$ARTIFACT" "$ARTIFACT_SHA256" > "$STATE"
echo "Installed ClineFlow MCP. Restart configured clients, then call clineflow_consult with an explicit root."
