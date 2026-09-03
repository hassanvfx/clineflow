#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
UPDATER="$ROOT/update.sh"
CURRENT_VERSION=$(sed -n 's/^release_version=//p' "$ROOT/template/.clineflow/release-manifest")
TEST_ROOT=$(mktemp -d /tmp/clineflow-migrations-XXXXXX)
trap 'rm -rf "$TEST_ROOT"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

seed_okf() {
  local project=$1
  mkdir -p "$project"
  cp -R "$ROOT/template/knowledge" "$project/knowledge"
  mkdir -p "$project/docs/journals"
  printf 'legacy journal\n' > "$project/docs/journals/legacy.md"
  (cd "$project" && git init -q)
}

assert_current() {
  local project=$1
  [ "$(cat "$project/.clineflow/VERSION")" = "$CURRENT_VERSION" ] || fail "wrong migrated version"
  grep -qx 'migration_schema=1' "$project/.clineflow/state" || fail "missing migration state"
  [ -x "$project/.clineflow/bin/validate-knowledge-sync" ] || fail "missing knowledge synchronization validator"
  [ -x "$project/.clineflow/bin/dashboard" ] && [ -f "$project/.clineflow/dashboard-component-manifest" ] || fail "missing inert dashboard launcher"
  [ ! -e "$project/.clineflow/optional" ] && [ ! -e "$project/knowledge/dashboard" ] || fail "update activated the optional dashboard"
  (cd "$project" && ./.clineflow/bin/doctor >/dev/null) || fail "migrated installation is unhealthy"
}

# Initial root OKF layout, stock agent rules, and retired reference artifacts.
root_project="$TEST_ROOT/root-okf"
seed_okf "$root_project"
mkdir -p "$root_project/clineflow"
printf '2026.08.15.0\n' > "$root_project/VERSION"
printf 'custom legacy runtime\n' > "$root_project/clineflow/WORKING_WITH_CLINE.md"
cp "$ROOT/tests/fixtures/okf-2026.08.15-agent-rules.md" "$root_project/AGENTS.md"
printf 'user knowledge\n' >> "$root_project/knowledge/log.md"
printf 'retired but user controlled\n' > "$root_project/setup-refs.sh"
knowledge_hash=$(shasum -a 256 "$root_project/knowledge/log.md" | awk '{print $1}')
legacy_hash=$(shasum -a 256 "$root_project/docs/journals/legacy.md" | awk '{print $1}')
refs_hash=$(shasum -a 256 "$root_project/setup-refs.sh" | awk '{print $1}')
(cd "$root_project" && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" --yes >/dev/null)
assert_current "$root_project"
[ "$knowledge_hash" = "$(shasum -a 256 "$root_project/knowledge/log.md" | awk '{print $1}')" ] || fail "user knowledge changed"
[ "$legacy_hash" = "$(shasum -a 256 "$root_project/docs/journals/legacy.md" | awk '{print $1}')" ] || fail "legacy journal changed"
[ "$refs_hash" = "$(shasum -a 256 "$root_project/setup-refs.sh" | awk '{print $1}')" ] || fail "retired reference artifact changed"
grep -qx 'file:AGENTS.md' "$root_project/.clineflow/.owned-agent-files" || fail "stock agent rules were not adopted"
grep -q 'validate-knowledge-sync --staged' "$root_project/AGENTS.md" || fail "updated agent rules omit staged knowledge synchronization"
grep -qFx 'custom legacy runtime' "$root_project/clineflow/WORKING_WITH_CLINE.md" || fail "custom legacy runtime was removed"
before_second=$(find "$root_project/.clineflow/backups" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
(cd "$root_project" && CLINEFLOW_BASE_URL="file://$ROOT/template" ./.clineflow/bin/update --yes >/dev/null)
after_second=$(find "$root_project/.clineflow/backups" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
[ "$before_second" = "$after_second" ] || fail "idempotent update created another transaction"
pass "root OKF migration preserves authored and retired content and is idempotent"

# Visible and partial hidden layouts converge through the same entrypoint.
for layout in visible hidden; do
  project="$TEST_ROOT/$layout"
  seed_okf "$project"
  if [ "$layout" = visible ]; then mkdir -p "$project/clineflow/bin"; printf '2026.08.25.0\n' > "$project/clineflow/VERSION"; printf 'old\n' > "$project/clineflow/bin/update"
  else mkdir -p "$project/.clineflow/bin"; printf '2026.08.25.0\n' > "$project/.clineflow/VERSION"; printf 'old\n' > "$project/.clineflow/bin/update"; fi
  printf 'custom project instructions\n' > "$project/AGENTS.md"
  (cd "$project" && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" --yes >/dev/null)
  assert_current "$project"
  grep -qFx 'custom project instructions' "$project/AGENTS.md" || fail "$layout migration replaced custom rules"
  grep -q 'BEGIN CLINEFLOW OKF RULES' "$project/AGENTS.md" || fail "$layout migration omitted current rules"
done
pass "visible and partial hidden OKF layouts converge"

# Dry-run, malformed markers, and pre-OKF detection are non-mutating.
dry_project="$TEST_ROOT/dry"
seed_okf "$dry_project"; printf '2026.08.15.0\n' > "$dry_project/VERSION"; mkdir -p "$dry_project/clineflow"; printf 'legacy\n' > "$dry_project/clineflow/WORKING_WITH_CLINE.md"
before=$(find "$dry_project" -type f -exec shasum -a 256 {} \; | sort | shasum -a 256 | awk '{print $1}')
(cd "$dry_project" && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" --dry-run >/dev/null)
after=$(find "$dry_project" -type f -exec shasum -a 256 {} \; | sort | shasum -a 256 | awk '{print $1}')
[ "$before" = "$after" ] || fail "dry-run changed project files"

malformed="$TEST_ROOT/malformed"
seed_okf "$malformed"; printf '2026.08.15.0\n' > "$malformed/VERSION"; mkdir -p "$malformed/clineflow"; printf 'legacy\n' > "$malformed/clineflow/WORKING_WITH_CLINE.md"; printf '<!-- BEGIN CLINEFLOW OKF RULES -->\n' > "$malformed/AGENTS.md"
if (cd "$malformed" && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" --yes >/dev/null 2>&1); then fail "malformed markers were accepted"; fi
[ ! -e "$malformed/.clineflow" ] || fail "malformed-marker rejection mutated the project"

pre_okf="$TEST_ROOT/pre-okf"
mkdir -p "$pre_okf/clineflow" "$pre_okf/docs/journals"; printf 'legacy\n' > "$pre_okf/docs/journals/task.md"
if (cd "$pre_okf" && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" --yes >/dev/null 2>&1); then fail "pre-OKF layout was accepted"; fi
[ ! -e "$pre_okf/.clineflow" ] || fail "pre-OKF rejection mutated the project"
pass "dry-run and unsupported-layout failures are non-mutating"

# A post-apply failure restores all original files and retains recovery evidence.
rollback_project="$TEST_ROOT/rollback"
seed_okf "$rollback_project"; printf '2026.08.15.0\n' > "$rollback_project/VERSION"; mkdir -p "$rollback_project/clineflow"; printf 'custom runtime\n' > "$rollback_project/clineflow/WORKING_WITH_CLINE.md"; printf 'custom agent\n' > "$rollback_project/AGENTS.md"
version_hash=$(shasum -a 256 "$rollback_project/VERSION" | awk '{print $1}')
agent_hash=$(shasum -a 256 "$rollback_project/AGENTS.md" | awk '{print $1}')
if (cd "$rollback_project" && CLINEFLOW_TEST_FAIL_AFTER_APPLY=true CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" --yes >/dev/null 2>&1); then fail "injected failure unexpectedly succeeded"; fi
[ "$version_hash" = "$(shasum -a 256 "$rollback_project/VERSION" | awk '{print $1}')" ] || fail "rollback did not restore VERSION"
[ "$agent_hash" = "$(shasum -a 256 "$rollback_project/AGENTS.md" | awk '{print $1}')" ] || fail "rollback did not restore agent rules"
[ ! -e "$rollback_project/.clineflow/state" ] || fail "rollback retained new release state"
find "$rollback_project/.clineflow/backups" -name update.log -exec grep -q 'rollback completed' {} \; || fail "rollback evidence was not retained"
grep -R -q 'rollback completed' "$rollback_project/.clineflow/backups" || fail "rollback evidence was not retained"
pass "failed migration automatically restores the prior installation"

# Confirmation and checksum failures happen before project mutation.
confirmation_project="$TEST_ROOT/confirmation"
seed_okf "$confirmation_project"; printf '2026.08.15.0\n' > "$confirmation_project/VERSION"; mkdir -p "$confirmation_project/clineflow"; printf 'legacy\n' > "$confirmation_project/clineflow/WORKING_WITH_CLINE.md"
if (cd "$confirmation_project" && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$UPDATER" </dev/null >/dev/null 2>&1); then fail "non-interactive update proceeded without --yes"; fi
[ ! -e "$confirmation_project/.clineflow" ] || fail "confirmation failure mutated the project"

bad_release="$TEST_ROOT/bad-release"
cp -R "$ROOT/template" "$bad_release"
printf '\ncorrupt\n' >> "$bad_release/.clineflow/PROCEDURES.md"
checksum_project="$TEST_ROOT/checksum"
seed_okf "$checksum_project"; printf '2026.08.15.0\n' > "$checksum_project/VERSION"; mkdir -p "$checksum_project/clineflow"; printf 'legacy\n' > "$checksum_project/clineflow/WORKING_WITH_CLINE.md"
if (cd "$checksum_project" && CLINEFLOW_BASE_URL="file://$bad_release" bash "$UPDATER" --yes >/dev/null 2>&1); then fail "checksum mismatch was accepted"; fi
[ ! -e "$checksum_project/.clineflow" ] || fail "checksum failure mutated the project"
pass "confirmation and release-integrity failures precede mutation"

echo "ClineFlow migration tests passed"
