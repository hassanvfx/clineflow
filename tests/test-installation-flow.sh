#!/usr/bin/env bash
# End-to-end installation, ownership, update, and uninstall safety checks.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
INSTALL="$ROOT/template/.clineflow/bin/install"
TEST_DIR=$(mktemp -d /tmp/clineflow-test-XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

mkdir -p "$TEST_DIR/project/.github" "$TEST_DIR/project/.windsurf/rules" "$TEST_DIR/project/knowledge/journals"
cd "$TEST_DIR/project"; git init -q
printf 'user agents\n' > AGENTS.md; printf 'user claude\n' > CLAUDE.md; printf 'user cline\n' > .clinerules
printf 'user copilot\n' > .github/copilot-instructions.md; printf 'user windsurf\n' > .windsurf/rules/clineflow.md
printf 'user knowledge\n' > knowledge/log.md
for file in AGENTS.md CLAUDE.md .clinerules .github/copilot-instructions.md .windsurf/rules/clineflow.md; do cp "$file" "$file.user"; done
shasum -a 256 knowledge/log.md > before.hashes
[ ! -d clineflow ] || fail "fresh test project unexpectedly has legacy runtime"
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL"
for tool in install update uninstall validate-okf doctor prereqs bootstrap.ps1; do [ -x ".clineflow/bin/$tool" ] || fail "missing .clineflow/bin/$tool"; done
[ -f .clineflow/VERSION ] && [ ! -e validate-okf ] && [ ! -e clineflow-doctor ] || fail "root tooling layout is incorrect"
for file in AGENTS.md CLAUDE.md .clinerules .github/copilot-instructions.md .windsurf/rules/clineflow.md; do grep -qFx "$(cat "$file.user")" "$file" && grep -q 'BEGIN CLINEFLOW' "$file" || fail "install did not safely merge $file"; done
shasum -a 256 knowledge/log.md > after.hashes; cmp before.hashes after.hashes || fail "install replaced user knowledge"
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" --force
for file in AGENTS.md CLAUDE.md .clinerules .github/copilot-instructions.md .windsurf/rules/clineflow.md; do [ "$(grep -c 'BEGIN CLINEFLOW' "$file")" -eq 1 ] || fail "force duplicated block in $file"; done
shasum -a 256 knowledge/log.md > force.hashes; cmp before.hashes force.hashes || fail "force replaced user knowledge"
pass "fresh install and force merge agent configuration without changing user content"
./.clineflow/bin/validate-okf; ./.clineflow/bin/doctor
CLINEFLOW_BASE_URL="file://$ROOT/template" ./.clineflow/bin/update --dry-run >/dev/null
pass "validator, doctor, and updater use encapsulated tooling"

mkdir "$TEST_DIR/owned"; cd "$TEST_DIR/owned"; git init -q
[ ! -d clineflow ] || fail "fresh owned project unexpectedly has legacy runtime"
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL"
[ -s .clineflow/.owned-agent-files ] || fail "missing ownership manifest"
./.clineflow/bin/uninstall
[ ! -d clineflow ] && [ ! -e AGENTS.md ] && [ ! -e CLAUDE.md ] && [ ! -e .clinerules ] || fail "uninstall did not remove owned files"
pass "uninstall removes only manifest-owned agent files"

mkdir "$TEST_DIR/claude-only"; cd "$TEST_DIR/claude-only"; git init -q
printf 'user claude only\n' > CLAUDE.md
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL"
rm AGENTS.md
./.clineflow/bin/doctor
./.clineflow/bin/uninstall
grep -qFx 'user claude only' CLAUDE.md && ! grep -q 'BEGIN CLINEFLOW' CLAUDE.md || fail "uninstall did not preserve user-owned CLAUDE.md"
pass "doctor accepts CLAUDE.md and uninstall preserves merged Claude instructions"

bash "$ROOT/tests/test-prerequisites.sh"
