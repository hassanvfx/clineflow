#!/usr/bin/env bash
# Unit-style prerequisite tests with a PATH containing only fake commands.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PREREQS="$ROOT/template/.clineflow/bin/prereqs"
TEST_DIR=$(mktemp -d /tmp/clineflow-prereqs-XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

make_bin() {
  local bin=$1 manager=${2:-}
  mkdir -p "$bin"
  cat > "$bin/uname" <<'EOF'
#!/bin/sh
[ "${1:-}" = "-m" ] && echo test-arch || echo "$CLINEFLOW_TEST_OS"
EOF
  chmod +x "$bin/uname"
  [ -n "$manager" ] || return 0
  cat > "$bin/$manager" <<'EOF'
#!/bin/sh
printf '%s\n' "$0 $*" >> "$CLINEFLOW_TEST_LOG"
EOF
  chmod +x "$bin/$manager"
}

for manager in apt-get dnf pacman zypper apk; do
  bin="$TEST_DIR/$manager"; log="$TEST_DIR/$manager.log"; make_bin "$bin" "$manager"
  output=$(PATH="$bin" CLINEFLOW_TEST_OS=Linux CLINEFLOW_TEST_LOG="$log" /bin/bash -c '. "$1"; clineflow_prereq_run true false' _ "$PREREQS" 2>&1)
  grep -q "Package manager: $manager" <<<"$output" || fail "$manager was not detected"
  grep -q 'Action: install git curl' <<<"$output" || fail "$manager did not plan Git and curl"
done
pass "Linux package-manager plans cover apt-get, dnf, pacman, zypper, and apk"

bin="$TEST_DIR/brew"; make_bin "$bin" brew
output=$(PATH="$bin" CLINEFLOW_TEST_OS=Darwin /bin/bash -c '. "$1"; clineflow_prereq_run true false' _ "$PREREQS" 2>&1)
grep -q 'Package manager: brew' <<<"$output" && grep -q 'Command: brew install git curl' <<<"$output" || fail "macOS Homebrew plan is incorrect"
pass "macOS plan uses Homebrew"

bin="$TEST_DIR/declined"; make_bin "$bin" apt-get
output=$(PATH="$bin" CLINEFLOW_TEST_OS=Linux /bin/bash -c '. "$1"; clineflow_prereq_run false false' _ "$PREREQS" 2>&1)
grep -Eq 'explicit approval is required|approval declined' <<<"$output" || fail "approval was not required"
pass "missing prerequisites require explicit approval"

bin="$TEST_DIR/git-only"; make_bin "$bin" apt-get
cat > "$bin/git" <<'EOF'
#!/bin/sh
echo 'git version test'
EOF
chmod +x "$bin/git"
output=$(PATH="$bin" CLINEFLOW_TEST_OS=Linux /bin/bash -c '. "$1"; clineflow_prereq_run true false' _ "$PREREQS" 2>&1)
grep -q 'Git: available (git version test)' <<<"$output" && grep -q 'Action: install curl' <<<"$output" || fail "Git-present downloader remediation is incorrect"
pass "Git-present environments only plan the missing downloader"

bin="$TEST_DIR/failure"; log="$TEST_DIR/failure.log"; make_bin "$bin" apt-get
cat > "$bin/sudo" <<'EOF'
#!/bin/sh
exec "$@"
EOF
chmod +x "$bin/sudo"
output=$(PATH="$bin" CLINEFLOW_TEST_OS=Linux CLINEFLOW_TEST_LOG="$log" /bin/bash -c '. "$1"; clineflow_prereq_run false true' _ "$PREREQS" 2>&1)
grep -q 'apt-get install -y git curl' "$log" || fail "approved package installation was not invoked"
grep -q 'Git is still unavailable' <<<"$output" || fail "post-install Git verification failure was not reported"
pass "approved installation verifies results and degrades safely"

bin="$TEST_DIR/package-failure"; log="$TEST_DIR/package-failure.log"; make_bin "$bin" apt-get
cat > "$bin/sudo" <<'EOF'
#!/bin/sh
exec "$@"
EOF
cat > "$bin/apt-get" <<'EOF'
#!/bin/sh
exit 1
EOF
chmod +x "$bin/sudo" "$bin/apt-get"
output=$(PATH="$bin" CLINEFLOW_TEST_OS=Linux CLINEFLOW_TEST_LOG="$log" /bin/bash -c '. "$1"; clineflow_prereq_run false true' _ "$PREREQS" 2>&1)
grep -q 'Prerequisite installation failed' <<<"$output" || fail "package-manager failure was not reported"
pass "package-manager failure degrades safely"

bin="$TEST_DIR/no-manager"; make_bin "$bin"
output=$(PATH="$bin" CLINEFLOW_TEST_OS=Linux /bin/bash -c '. "$1"; clineflow_prereq_run false true' _ "$PREREQS" 2>&1)
grep -q 'no automatic installation available' <<<"$output" || fail "missing manager was not reported"
pass "missing package manager degrades safely"

grep -q 'winget install --id Git.Git' "$ROOT/template/.clineflow/bin/bootstrap.ps1" || fail "Windows winget bootstrap is missing"
grep -q 'Git Bash and curl' "$ROOT/template/.clineflow/bin/bootstrap.ps1" || fail "Windows bootstrap does not verify Git Bash and curl"
pass "Windows PowerShell bootstrap declares Git for Windows intent"
