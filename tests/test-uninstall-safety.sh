#!/usr/bin/env bash
# Adversarial removal tests for ownership, preservation, confirmation, and rollback.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
INSTALL="$ROOT/template/.clineflow/bin/install"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/clineflow-uninstall-test-XXXXXX")
trap 'rm -rf "$TEST_ROOT"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

install_project() {
  local project=$1
  mkdir -p "$project"
  (cd "$project" && git init -q && CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" >/dev/null)
}
snapshot() {
  local project=$1 destination=$2 file
  (
    cd "$project"
    find . -type f | LC_ALL=C sort | while IFS= read -r file; do
      printf '%s  ' "$file"
      shasum -a 256 "$file" | awk '{print $1}'
    done
    find . -type l | LC_ALL=C sort | while IFS= read -r file; do printf '%s -> %s\n' "$file" "$(readlink "$file")"; done
  ) > "$destination"
}

dry="$TEST_ROOT/dry"
install_project "$dry"
snapshot "$dry" "$TEST_ROOT/dry.before"
(cd "$dry" && ./.clineflow/bin/uninstall --dry-run >/dev/null)
snapshot "$dry" "$TEST_ROOT/dry.after"
cmp "$TEST_ROOT/dry.before" "$TEST_ROOT/dry.after" || fail "uninstall dry-run changed the project"
if (cd "$dry" && ./.clineflow/bin/uninstall </dev/null >/dev/null 2>&1); then fail "non-interactive uninstall bypassed confirmation"; fi
snapshot "$dry" "$TEST_ROOT/dry.confirmation"
cmp "$TEST_ROOT/dry.before" "$TEST_ROOT/dry.confirmation" || fail "rejected confirmation changed the project"
pass "dry-run and missing confirmation are non-mutating"

preserve="$TEST_ROOT/preserve"
install_project "$preserve"
printf 'user agent addition\n' >> "$preserve/AGENTS.md"
mkdir -p "$preserve/docs/journals"
printf 'journal\n' > "$preserve/docs/journals/user.md"
printf 'documentation\n' > "$preserve/docs/user-guide.md"
printf 'unrelated\n' > "$preserve/unrelated.txt"
printf 'retired\n' > "$preserve/setup-refs.sh"
(cd "$preserve" && ./.clineflow/bin/uninstall --yes >/dev/null)
[ ! -e "$preserve/.clineflow" ] || fail "uninstall retained the managed runtime"
grep -qFx 'user agent addition' "$preserve/AGENTS.md" || fail "uninstall removed user additions from an owned agent file"
! grep -q 'BEGIN CLINEFLOW' "$preserve/AGENTS.md" || fail "uninstall retained the managed rules block"
for path in knowledge docs/journals/user.md docs/user-guide.md unrelated.txt setup-refs.sh; do [ -e "$preserve/$path" ] || fail "uninstall removed preserved path $path"; done
[ ! -e "$preserve/CLAUDE.md" ] && [ ! -e "$preserve/.clinerules" ] || fail "uninstall retained unchanged owned agent files"
pass "removal preserves authored and retired content while deleting only managed content"

external="$TEST_ROOT/external-reexec"
install_project "$external"
(cd "$external" && CLINEFLOW_TEST_FORCE_EXTERNAL_REEXEC=true ./.clineflow/bin/uninstall --yes >/dev/null)
[ ! -e "$external/.clineflow" ] || fail "external self-copy uninstall retained the managed runtime"
[ -d "$external/knowledge" ] || fail "external self-copy uninstall removed project knowledge"
pass "external self-copy permits Windows-safe runtime removal"

malformed="$TEST_ROOT/malformed"
install_project "$malformed"
sed '/END CLINEFLOW OKF RULES/d' "$malformed/AGENTS.md" > "$malformed/AGENTS.tmp"
mv "$malformed/AGENTS.tmp" "$malformed/AGENTS.md"
snapshot "$malformed" "$TEST_ROOT/malformed.before"
if (cd "$malformed" && ./.clineflow/bin/uninstall --yes >/dev/null 2>&1); then fail "malformed markers did not block uninstall"; fi
snapshot "$malformed" "$TEST_ROOT/malformed.after"
cmp "$TEST_ROOT/malformed.before" "$TEST_ROOT/malformed.after" || fail "malformed-marker rejection changed the project"
pass "malformed ownership markers abort before mutation"

unsafe="$TEST_ROOT/unsafe"
install_project "$unsafe"
printf 'file:../outside.txt\n' >> "$unsafe/.clineflow/.owned-agent-files"
printf 'outside\n' > "$TEST_ROOT/outside.txt"
snapshot "$unsafe" "$TEST_ROOT/unsafe.before"
if (cd "$unsafe" && ./.clineflow/bin/uninstall --yes >/dev/null 2>&1); then fail "unsafe ownership path did not block uninstall"; fi
snapshot "$unsafe" "$TEST_ROOT/unsafe.after"
cmp "$TEST_ROOT/unsafe.before" "$TEST_ROOT/unsafe.after" || fail "unsafe ownership rejection changed the project"
grep -qFx outside "$TEST_ROOT/outside.txt" || fail "unsafe ownership path touched an outside file"
pass "ownership manifests cannot escape the supported agent path allowlist"

for mode in failure signal; do
  project="$TEST_ROOT/rollback-$mode"
  install_project "$project"
  printf 'user text\n' >> "$project/AGENTS.md"
  snapshot "$project" "$TEST_ROOT/$mode.before"
  if [ "$mode" = failure ]; then variable=CLINEFLOW_TEST_FAIL_AFTER_APPLY
  else variable=CLINEFLOW_TEST_SIGNAL_AFTER_APPLY; fi
  if (cd "$project" && env "$variable=true" ./.clineflow/bin/uninstall --yes >/dev/null 2>&1); then fail "injected $mode unexpectedly succeeded"; fi
  snapshot "$project" "$TEST_ROOT/$mode.after"
  cmp "$TEST_ROOT/$mode.before" "$TEST_ROOT/$mode.after" || fail "injected $mode did not restore the complete installation"
  [ -x "$project/.clineflow/bin/uninstall" ] || fail "rollback did not restore the uninstaller"
done
pass "failure and termination restore the complete pre-removal state"

untrusted="$TEST_ROOT/untrusted"
install_project "$untrusted"
rm "$untrusted/.clineflow/.owned-agent-files"
(cd "$untrusted" && ./.clineflow/bin/uninstall --yes >/dev/null 2>&1)
[ ! -e "$untrusted/.clineflow" ] || fail "untrusted uninstall retained runtime"
grep -q 'BEGIN CLINEFLOW' "$untrusted/AGENTS.md" || fail "untrusted uninstall changed agent configuration"
pass "missing ownership data preserves all agent configurations"

symlinked="$TEST_ROOT/symlinked"
install_project "$symlinked"
mv "$symlinked/.clineflow" "$symlinked/real-runtime"
ln -s real-runtime "$symlinked/.clineflow"
if (cd "$symlinked" && ./real-runtime/bin/uninstall --yes >/dev/null 2>&1); then fail "symlinked runtime did not block uninstall"; fi
[ -L "$symlinked/.clineflow" ] && [ -d "$symlinked/real-runtime" ] || fail "symlink rejection changed runtime layout"
pass "symlinked runtime layouts abort safely"

echo "All uninstall safety tests passed."
