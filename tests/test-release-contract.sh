#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
TEST_ROOT=$(mktemp -d /tmp/clineflow-release-XXXXXX)
trap 'rm -rf "$TEST_ROOT"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

copy_release() {
  local destination=$1
  mkdir -p "$destination"
  cp "$ROOT/README.md" "$destination/README.md"
  cp -R "$ROOT/template" "$destination/template"
  mkdir -p "$destination/docs"
  cp "$ROOT/docs/installation-and-lifecycle.md" "$destination/docs/installation-and-lifecycle.md"
  mkdir -p "$destination/.github"
  cp -R "$ROOT/.github/workflows" "$destination/.github/workflows"
  cp -R "$ROOT/tests" "$destination/tests"
}

refresh_checksum() {
  local checkout=$1 source=$2 digest temporary
  digest=$(shasum -a 256 "$checkout/template/$source" | awk '{print $1}')
  temporary="$checkout/template/.clineflow/release-manifest.tmp"
  awk -F'|' -v OFS='|' -v wanted="$source" -v digest="$digest" '$1=="payload" && $4==wanted {$6=digest} {print}' "$checkout/template/.clineflow/release-manifest" > "$temporary"
  mv "$temporary" "$checkout/template/.clineflow/release-manifest"
}

"$ROOT/template/.clineflow/bin/validate-release" >/dev/null
pass "current release contract is valid"

for pattern in '*.md text eol=lf' '*.yml text eol=lf' '*.ps1 text eol=lf' 'template/.clineflow/dashboard-component-manifest text eol=lf'; do
  grep -qF "$pattern" "$ROOT/.gitattributes" || fail "release payload line endings are not pinned: $pattern"
done

portable="$TEST_ROOT/portable"; copy_release "$portable"
"$portable/template/.clineflow/bin/validate-release" >/dev/null || fail "copied release fixture is incomplete"

grep -qF '`template/.clineflow/WORKING_WITH_CODEX.md`' "$ROOT/AGENTS.md" || fail "source AGENTS.md points to a missing Codex guide"
for source_rules in "$ROOT/AGENTS.md" "$ROOT/.clinerules"; do
  grep -qF './template/.clineflow/bin/validate-okf' "$source_rules" || fail "source agent rules point to a missing OKF validator: $source_rules"
  grep -qF './template/.clineflow/bin/validate-knowledge-sync --staged' "$source_rules" || fail "source agent rules point to a missing staged synchronization validator: $source_rules"
  grep -qF 'https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh' "$source_rules" || fail "source agent rules omit the authoritative remote updater: $source_rules"
  grep -qF 'Do not run any existing local updater first' "$source_rules" || fail "source agent rules permit a stale local updater: $source_rules"
done
cmp -s "$ROOT/template/.clinerules" "$ROOT/template/configs/rules.template.md" || fail "legacy Cline template drifted from canonical shared rules"
pass "source and compatibility agent instructions resolve to current workflow files"

unmanaged="$TEST_ROOT/unmanaged"; copy_release "$unmanaged"; printf 'extra\n' > "$unmanaged/template/.clineflow/extra"
if "$unmanaged/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "unmanaged runtime file was accepted"; fi

stale="$TEST_ROOT/stale"; copy_release "$stale"; printf '\nchanged\n' >> "$stale/template/.clineflow/PROCEDURES.md"
if "$stale/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "stale checksum was accepted"; fi

optional="$TEST_ROOT/optional"; copy_release "$optional"; printf '\nchanged\n' >> "$optional/template/optional/dashboard/visor.css"
if "$optional/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "stale optional dashboard checksum was accepted"; fi

optional_unmanaged="$TEST_ROOT/optional-unmanaged"; copy_release "$optional_unmanaged"; printf 'extra\n' > "$optional_unmanaged/template/optional/dashboard/extra.js"
if "$optional_unmanaged/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "unmanaged optional dashboard source was accepted"; fi

prompt="$TEST_ROOT/prompt"; copy_release "$prompt"; sed 's/Please update ClineFlow\./Update ClineFlow now./g' "$prompt/README.md" > "$prompt/README.tmp"; mv "$prompt/README.tmp" "$prompt/README.md"
if "$prompt/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing canonical prompt was accepted"; fi

local_first="$TEST_ROOT/local-first"; copy_release "$local_first"; sed 's/Do not run any existing local updater first/Local updater use is permitted/' "$local_first/README.md" > "$local_first/README.tmp"; mv "$local_first/README.tmp" "$local_first/README.md"
if "$local_first/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing stale-local-updater warning was accepted"; fi

rescue="$TEST_ROOT/rescue"; copy_release "$rescue"; sed 's/Old install or prompt not recognized?/Update details/' "$rescue/README.md" > "$rescue/README.tmp"; mv "$rescue/README.tmp" "$rescue/README.md"
if "$rescue/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing old-install rescue path was accepted"; fi

rescue_command="$TEST_ROOT/rescue-command"; copy_release "$rescue_command"; sed 's/bash -s -- --yes/bash/' "$rescue_command/README.md" > "$rescue_command/README.tmp"; mv "$rescue_command/README.tmp" "$rescue_command/README.md"
if "$rescue_command/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "incomplete rescue command was accepted"; fi

removal="$TEST_ROOT/removal"; copy_release "$removal"; sed 's/Please remove ClineFlow\./Remove the tool./g' "$removal/README.md" > "$removal/README.tmp"; mv "$removal/README.tmp" "$removal/README.md"
if "$removal/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing canonical removal prompt was accepted"; fi

removal_preview="$TEST_ROOT/removal-preview"; copy_release "$removal_preview"; sed 's#\./\.clineflow/bin/uninstall --dry-run#./.clineflow/bin/uninstall --yes#g' "$removal_preview/README.md" > "$removal_preview/README.tmp"; mv "$removal_preview/README.tmp" "$removal_preview/README.md"
if "$removal_preview/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "removal guidance without a dry-run preview was accepted"; fi

commit_prompt="$TEST_ROOT/commit-prompt"; copy_release "$commit_prompt"; sed 's/Please commit\./Commit now./g' "$commit_prompt/README.md" > "$commit_prompt/README.tmp"; mv "$commit_prompt/README.tmp" "$commit_prompt/README.md"
if "$commit_prompt/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing canonical commit prompt was accepted"; fi

dashboard_prompt="$TEST_ROOT/dashboard-prompt"; copy_release "$dashboard_prompt"; sed 's/Please show me the ClineFlow dashboard\./Open the dashboard./g' "$dashboard_prompt/README.md" > "$dashboard_prompt/README.tmp"; mv "$dashboard_prompt/README.tmp" "$dashboard_prompt/README.md"
if "$dashboard_prompt/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing canonical dashboard prompt was accepted"; fi
pass "release validation rejects missing lifecycle prompts, rescue guidance, unsafe removal guidance, and local-first updates"

chain="$TEST_ROOT/chain"; copy_release "$chain"; sed 's/migrate_0_to_1()/removed_0_to_1()/' "$chain/template/.clineflow/bin/update" > "$chain/update.tmp"; mv "$chain/update.tmp" "$chain/template/.clineflow/bin/update"; chmod +x "$chain/template/.clineflow/bin/update"; refresh_checksum "$chain" .clineflow/bin/update
if "$chain/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "missing migration chain was accepted"; fi

version="$TEST_ROOT/version"; copy_release "$version"; (cd "$version" && git init -q && git config user.name Test && git config user.email test@example.com && git add . && git commit -qm baseline)
printf '\nmanaged change\n' >> "$version/template/.clineflow/PROCEDURES.md"; refresh_checksum "$version" .clineflow/PROCEDURES.md
if (cd "$version" && ./template/.clineflow/bin/validate-release --against HEAD >/dev/null 2>&1); then fail "managed change without a version bump was accepted"; fi
pass "release validation rejects incomplete migrations and missing version bumps"

certification="$TEST_ROOT/certification"; copy_release "$certification"
sed '/test-uninstall-safety.sh/d' "$certification/tests/certify-release.sh" > "$certification/certify.tmp"
mv "$certification/certify.tmp" "$certification/tests/certify-release.sh"; chmod +x "$certification/tests/certify-release.sh"
if "$certification/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "certification without uninstall safety was accepted"; fi

dashboard_certification="$TEST_ROOT/dashboard-certification"; copy_release "$dashboard_certification"
sed '/test-dashboard.sh/d' "$dashboard_certification/tests/certify-release.sh" > "$dashboard_certification/certify.tmp"
mv "$dashboard_certification/certify.tmp" "$dashboard_certification/tests/certify-release.sh"; chmod +x "$dashboard_certification/tests/certify-release.sh"
if "$dashboard_certification/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "certification without dashboard boundaries was accepted"; fi

ci="$TEST_ROOT/ci"; copy_release "$ci"
sed 's#./tests/certify-release.sh#./tests/test-okf-validator.sh#' "$ci/.github/workflows/test.yml" > "$ci/ci.tmp"
mv "$ci/ci.tmp" "$ci/.github/workflows/test.yml"
if "$ci/template/.clineflow/bin/validate-release" >/dev/null 2>&1; then fail "CI without lifecycle certification was accepted"; fi
pass "release validation requires complete lifecycle certification in CI"

echo "ClineFlow release-contract tests passed"
