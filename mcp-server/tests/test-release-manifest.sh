#!/usr/bin/env bash
# Ensure the separately versioned wheel declaration is buildable and immutable.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MANIFEST="$ROOT/release-manifest"
VERSION=$(sed -n 's/^release_version=//p' "$MANIFEST")
URL=$(sed -n 's/^artifact_url=//p' "$MANIFEST")
EXPECTED_SHA=$(sed -n 's/^artifact_sha256=//p' "$MANIFEST")
ASSET=$(basename "$URL")
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/clineflow-mcp-release-test-XXXXXX")
trap 'rm -rf "$TEST_ROOT"' EXIT

[ -n "$VERSION" ] && [ -n "$URL" ] && [ -n "$EXPECTED_SHA" ]
[ "$ASSET" = "clineflow_mcp-${VERSION}-py3-none-any.whl" ]
printf '%s' "$EXPECTED_SHA" | grep -Eq '^[0-9a-f]{64}$'
grep -q "version = \"$VERSION\"" "$ROOT/pyproject.toml"
grep -q "__version__ = \"$VERSION\"" "$ROOT/src/clineflow_mcp/__init__.py"
grep -qF "$URL" "$ROOT/install.sh"
grep -qF "$EXPECTED_SHA" "$ROOT/install.sh"
UV_CACHE_DIR=${UV_CACHE_DIR:-/private/tmp/clineflow-mcp-uv-cache} uv build --directory "$ROOT" --out-dir "$TEST_ROOT" >/dev/null
ACTUAL_SHA=$(shasum -a 256 "$TEST_ROOT/$ASSET" | awk '{print $1}')
[ "$ACTUAL_SHA" = "$EXPECTED_SHA" ] || { echo "MCP release wheel checksum does not match release-manifest." >&2; exit 1; }
echo "ClineFlow MCP release-manifest test passed"
