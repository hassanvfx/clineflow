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
for tool in install dashboard update uninstall validate-knowledge-sync validate-okf validate-release doctor prereqs; do [ -x ".clineflow/bin/$tool" ] || fail "missing executable .clineflow/bin/$tool"; done
for tool in update.ps1 bootstrap.ps1; do [ -f ".clineflow/bin/$tool" ] || fail "missing PowerShell command .clineflow/bin/$tool"; done
[ -f .clineflow/dashboard-component-manifest ] || fail "missing inert dashboard component manifest"
[ ! -e .clineflow/optional ] && [ ! -e knowledge/dashboard ] || fail "installation activated the optional dashboard"
! grep -q 'CLINEFLOW DASHBOARD GENERATED REPORTS' .git/info/exclude || fail "installation changed dashboard exclusions"
[ -f docs/durable-development-methodology.md ] || fail "missing durable development methodology fixture"
for index in clineflow_specification.yml clineflow_verification.yml clineflow_goals.yml clineflow_last_session.yml clineflow_timeline.yml; do [ -f "knowledge/$index" ] || fail "missing knowledge/$index"; done
grep -q 'durable-development-methodology.md' AGENTS.md || fail "agent rules do not require the durable loop"
grep -q 'Autonomy operates within explicit boundaries' .clineflow/PROCEDURES.md || fail "managed procedures omit autonomy boundaries"
grep -q 'Routine reversible choice' .clineflow/PROCEDURES.md || fail "managed procedures omit boundary examples"
grep -q 'Choose reversible details inside the authorized contract' AGENTS.md || fail "agent rules omit the approved reversible-choice boundary"
grep -q 'Please update ClineFlow\.' AGENTS.md || fail "agent rules do not include the canonical update prompt"
for file in AGENTS.md CLAUDE.md .clinerules .github/copilot-instructions.md .windsurf/rules/clineflow.md; do
  grep -q 'immutable.*update record' "$file" && grep -q 'validate-knowledge-sync --staged' "$file" || fail "agent rules do not enforce tenant knowledge synchronization in $file"
  grep -q 'Please commit\.' "$file" || fail "agent rules omit the canonical commit prompt in $file"
  grep -q 'Please update ClineFlow\.' "$file" || fail "agent rules omit the canonical update prompt in $file"
  grep -q 'Please remove ClineFlow\.' "$file" && grep -qF './.clineflow/bin/uninstall --dry-run' "$file" || fail "agent rules omit preview-before-removal in $file"
  grep -q 'Please show me the ClineFlow dashboard\.' "$file" || fail "agent rules omit the canonical dashboard prompt in $file"
done
[ -f .clineflow/VERSION ] && [ ! -e validate-okf ] && [ ! -e clineflow-doctor ] || fail "root tooling layout is incorrect"
for file in AGENTS.md CLAUDE.md .clinerules .github/copilot-instructions.md .windsurf/rules/clineflow.md; do grep -qFx "$(cat "$file.user")" "$file" && grep -q 'BEGIN CLINEFLOW' "$file" || fail "install did not safely merge $file"; done
shasum -a 256 knowledge/log.md > after.hashes; cmp before.hashes after.hashes || fail "install replaced user knowledge"
printf '%s\n' '# user index preservation' >> knowledge/clineflow_goals.yml
printf '%s\n' '<!-- user manual preservation -->' >> docs/durable-development-methodology.md
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" --force
for file in AGENTS.md CLAUDE.md .clinerules .github/copilot-instructions.md .windsurf/rules/clineflow.md; do [ "$(grep -c 'BEGIN CLINEFLOW' "$file")" -eq 1 ] || fail "force duplicated block in $file"; done
shasum -a 256 knowledge/log.md > force.hashes; cmp before.hashes force.hashes || fail "force replaced user knowledge"
grep -q 'user index preservation' knowledge/clineflow_goals.yml || fail "force replaced user index"
grep -q 'user manual preservation' docs/durable-development-methodology.md || fail "force replaced user methodology manual"
pass "fresh install and force merge agent configuration without changing user content"
./.clineflow/bin/validate-okf; ./.clineflow/bin/doctor
CLINEFLOW_BASE_URL="file://$ROOT/template" ./.clineflow/bin/update --dry-run >/dev/null
rm knowledge/clineflow_timeline.yml docs/durable-development-methodology.md
CLINEFLOW_BASE_URL="file://$ROOT/template" ./.clineflow/bin/update --yes >/dev/null
[ -f knowledge/clineflow_timeline.yml ] && [ -f docs/durable-development-methodology.md ] || fail "update did not seed missing durable fixtures"
pass "validator, doctor, and updater use encapsulated tooling"

mkdir "$TEST_DIR/auto-init"; cd "$TEST_DIR/auto-init"
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL"
[ -d .git ] || fail "installer did not initialize Git in a fresh directory"
git rev-parse --is-inside-work-tree >/dev/null || fail "initialized Git repository is not usable"
git rev-parse --verify HEAD >/dev/null 2>&1 && fail "installer unexpectedly created a Git commit"
[ -z "$(git remote)" ] || fail "installer unexpectedly configured a Git remote"
git config --local --get user.name >/dev/null 2>&1 && fail "installer unexpectedly configured Git identity"
./.clineflow/bin/doctor
pass "fresh installation initializes Git without a commit, remote, or identity"

mkdir "$TEST_DIR/dry-run"; cd "$TEST_DIR/dry-run"
output=$(CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" --dry-run)
grep -q 'Would initialize a Git repository' <<<"$output" || fail "dry-run did not report Git initialization"
[ ! -e .git ] || fail "dry-run initialized Git"
pass "dry-run reports but does not initialize Git"

mkdir "$TEST_DIR/init-failure" "$TEST_DIR/init-failure-bin"; cd "$TEST_DIR/init-failure"
cat > "$TEST_DIR/init-failure-bin/git" <<'EOF'
#!/usr/bin/env bash
case "${1:-}" in
  --version) echo 'git version test' ;;
  rev-parse|init) exit 1 ;;
  *) exit 0 ;;
esac
EOF
chmod +x "$TEST_DIR/init-failure-bin/git"
output=$(PATH="$TEST_DIR/init-failure-bin:$PATH" CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" 2>&1)
grep -q 'repository initialization failed' <<<"$output" || fail "Git initialization failure was not reported"
[ -d .clineflow ] || fail "installation did not continue after Git initialization failure"
pass "Git initialization failure degrades safely"

mkdir "$TEST_DIR/owned"; cd "$TEST_DIR/owned"; git init -q
[ ! -d clineflow ] || fail "fresh owned project unexpectedly has legacy runtime"
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL"
[ -s .clineflow/.owned-agent-files ] || fail "missing ownership manifest"
./.clineflow/bin/uninstall --yes
[ ! -d clineflow ] && [ ! -e AGENTS.md ] && [ ! -e CLAUDE.md ] && [ ! -e .clinerules ] || fail "uninstall did not remove owned files"
pass "uninstall removes only manifest-owned agent files"

mkdir "$TEST_DIR/claude-only"; cd "$TEST_DIR/claude-only"; git init -q
printf 'user claude only\n' > CLAUDE.md
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL"
rm AGENTS.md
./.clineflow/bin/doctor
./.clineflow/bin/uninstall --yes
grep -qFx 'user claude only' CLAUDE.md && ! grep -q 'BEGIN CLINEFLOW' CLAUDE.md || fail "uninstall did not preserve user-owned CLAUDE.md"
pass "doctor accepts CLAUDE.md and uninstall preserves merged Claude instructions"

bash "$ROOT/tests/test-prerequisites.sh"
