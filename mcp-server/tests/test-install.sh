#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/clineflow-mcp-install-test-XXXXXX")
trap 'rm -rf "$TEST_ROOT"' EXIT
UV_CACHE_DIR=${UV_CACHE_DIR:-/private/tmp/clineflow-mcp-uv-cache}
export UV_CACHE_DIR
(cd "$ROOT" && uv build --out-dir "$TEST_ROOT/dist" >/dev/null)
WHEEL=$(find "$TEST_ROOT/dist" -name '*.whl' -print -quit)
SHA=$(shasum -a 256 "$WHEEL" | awk '{print $1}')
mkdir -p "$TEST_ROOT/home/.codex"
MCP_STATE="$TEST_ROOT/state/clineflow-mcp"
HOME="$TEST_ROOT/home" UV_TOOL_DIR="$TEST_ROOT/tools" UV_TOOL_BIN_DIR="$TEST_ROOT/bin" \
  CLINEFLOW_MCP_HOME="$MCP_STATE" CLINEFLOW_MCP_ARTIFACT="$WHEEL" \
  CLINEFLOW_MCP_ARTIFACT_SHA256="$SHA" CLINEFLOW_MCP_RELEASE_VERSION=0.1.7 \
  bash "$ROOT/install.sh" >/dev/null
[ -x "$TEST_ROOT/bin/clineflow-mcp" ] || { echo "missing stable CLI launcher" >&2; exit 1; }
[ -x "$TEST_ROOT/bin/clineflow-mcp-server" ] || { echo "missing stable server launcher" >&2; exit 1; }
"$TEST_ROOT/bin/clineflow-mcp" --version | grep -q '^0.1.7$'
grep -q 'release_version=0.1.7' "$MCP_STATE/state"
grep -q 'clineflow-mcp-server' "$TEST_ROOT/home/.codex/config.toml"
HOME="$TEST_ROOT/home" UV_TOOL_DIR="$TEST_ROOT/tools" UV_TOOL_BIN_DIR="$TEST_ROOT/bin" \
  CLINEFLOW_MCP_HOME="$MCP_STATE" CLINEFLOW_MCP_RELEASE_VERSION=0.1.7 \
  bash "$ROOT/install.sh" --status | grep -q 'healthy'
preview=$(HOME="$TEST_ROOT/home" UV_TOOL_DIR="$TEST_ROOT/tools" UV_TOOL_BIN_DIR="$TEST_ROOT/bin" \
  CLINEFLOW_MCP_HOME="$MCP_STATE" bash "$ROOT/uninstall.sh" --dry-run)
grep -q 'preserve every project .clineflow-mcp/' <<<"$preview"
HOME="$TEST_ROOT/home" UV_TOOL_DIR="$TEST_ROOT/tools" UV_TOOL_BIN_DIR="$TEST_ROOT/bin" \
  CLINEFLOW_MCP_HOME="$MCP_STATE" bash "$ROOT/uninstall.sh" --yes >/dev/null
[ ! -e "$TEST_ROOT/bin/clineflow-mcp" ] || { echo "global removal retained the CLI launcher" >&2; exit 1; }
[ ! -e "$MCP_STATE" ] || { echo "global removal retained owned state" >&2; exit 1; }

# The status classifier is deliberately independent of a live repository. It
# must distinguish every supported global state without installing anything.
status_case() {
  local name=$1 version=$2 expected=$3 fixture
  fixture="$TEST_ROOT/status-$name"
  mkdir -p "$fixture/bin"
  if [ "$name" != absent ] && [ "$name" != corrupt ]; then
    printf '%s\n' '#!/bin/sh' 'printf "0.1.7\\n"' > "$fixture/bin/clineflow-mcp"
    printf '%s\n' '#!/bin/sh' 'exit 0' > "$fixture/bin/clineflow-mcp-server"
    chmod +x "$fixture/bin/clineflow-mcp" "$fixture/bin/clineflow-mcp-server"
  fi
  if [ "$name" != absent ]; then
    mkdir -p "$fixture/state/clineflow-mcp"
    printf 'release_version=%s\n' "$version" > "$fixture/state/clineflow-mcp/state"
  fi
  HOME="$fixture/home" UV_TOOL_DIR="$fixture/tools" UV_TOOL_BIN_DIR="$fixture/bin" \
    CLINEFLOW_MCP_HOME="$fixture/state/clineflow-mcp" bash "$ROOT/install.sh" --status | grep -q "\"status\":\"$expected\""
}
status_case absent '' absent
status_case healthy 0.1.7 healthy
status_case outdated 0.0.9 outdated
status_case corrupt 0.1.1 corrupt

lock_fixture="$TEST_ROOT/status-lock"
mkdir -p "$lock_fixture/state/clineflow-mcp.bootstrap-lock"
if HOME="$lock_fixture/home" UV_TOOL_DIR="$lock_fixture/tools" UV_TOOL_BIN_DIR="$lock_fixture/bin" \
  CLINEFLOW_MCP_HOME="$lock_fixture/state/clineflow-mcp" bash "$ROOT/install.sh" --dry-run >/dev/null 2>&1; then
  echo "concurrent bootstrap lock was accepted" >&2
  exit 1
fi

# A piped standalone script runs with the target project as its working
# directory.  Its package selection must remain the declared HTTPS wheel even
# when that project has an unrelated pyproject.toml.
piped_project="$TEST_ROOT/piped-project"
piped_bin="$TEST_ROOT/piped-bin"
mkdir -p "$piped_project" "$piped_bin" "$TEST_ROOT/piped-tool-bin"
touch "$piped_project/pyproject.toml"
cat > "$piped_bin/uv" <<'EOF'
#!/bin/sh
if [ "$1" = tool ] && [ "$2" = dir ] && [ "$3" = --bin ]; then printf '%s\n' "$PIPED_TOOL_BIN"; exit 0; fi
exit 99
EOF
cat > "$piped_bin/curl" <<'EOF'
#!/bin/sh
printf '%s\n' "$@" > "$PIPED_CURL_LOG"
exit 1
EOF
chmod +x "$piped_bin/uv" "$piped_bin/curl"
if (cd "$piped_project" && PATH="$piped_bin:$PATH" PIPED_TOOL_BIN="$TEST_ROOT/piped-tool-bin" \
  PIPED_CURL_LOG="$TEST_ROOT/piped-curl.log" CLINEFLOW_MCP_HOME="$TEST_ROOT/piped-state/clineflow-mcp" \
  bash < "$ROOT/install.sh") >/dev/null 2>&1; then
  echo "piped installer unexpectedly completed with a deliberately failing downloader" >&2
  exit 1
fi
grep -qF 'https://github.com/hassanvfx/clineflow/releases/download/mcp-v0.1.7/clineflow_mcp-0.1.7-py3-none-any.whl' "$TEST_ROOT/piped-curl.log"
echo "ClineFlow MCP global-install test passed"
