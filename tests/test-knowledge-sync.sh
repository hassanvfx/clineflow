#!/usr/bin/env bash

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT
PROJECT="$TEST_DIR/project"
mkdir -p "$PROJECT/.clineflow/bin" "$PROJECT/knowledge/journals" "$PROJECT/docs"
cp "$ROOT/template/.clineflow/bin/validate-knowledge-sync" "$PROJECT/.clineflow/bin/"
chmod +x "$PROJECT/.clineflow/bin/validate-knowledge-sync"
cd "$PROJECT"
git init -q

write_sync_set() {
    local at=$1 summary=$2
    printf '%s\n' \
        'version: 1' "updated_at: $at" 'confirmed:' '  - Durable context is synchronized.' \
        'assumptions: []' 'constraints: []' 'non_goals: []' 'open_questions: []' \
        'journal_refs:' '  - journals/task.md' > knowledge/clineflow_specification.yml
    printf '%s\n' \
        'version: 1' "updated_at: $at" 'acceptance_criteria:' '  - Synchronization validation passes.' \
        'regression_checks: []' 'evidence_refs:' '  - journals/task.md' 'open_verification: []' \
        'journal_refs:' '  - journals/task.md' > knowledge/clineflow_verification.yml
    printf '%s\n' \
        'version: 1' "updated_at: $at" 'active_goals:' '  - Keep knowledge synchronized.' \
        'priorities: []' 'success_measures: []' 'blocked_goals: []' 'completed_goals: []' \
        'journal_refs:' '  - journals/task.md' > knowledge/clineflow_goals.yml
    printf '%s\n' \
        'version: 1' "updated_at: $at" "latest_change: $summary" \
        'specification_summary: []' 'verification_summary: []' 'goals_summary: []' \
        'next_recommended_step: Continue from the synchronized journal.' \
        'next_step_refs:' '  - journals/task.md' 'journal_refs:' '  - journals/task.md' > knowledge/clineflow_last_session.yml
    printf '%s\n' \
        'version: 1' "updated_at: $at" 'events:' "  - at: $at" '    actor: test' \
        '    type: documentation' "    summary: $summary" '    refs:' '      - journals/task.md' \
        '    git_revision: null' '    usage_capture: unavailable' > knowledge/clineflow_timeline.yml
    printf '%s\n' \
        '---' 'type: Engineering Journal' 'title: "Test task"' 'status: draft' 'generated:' \
        '  by: test' "  at: $at" '---' '' '# Task' '' "$summary" > knowledge/journals/task.md
    printf '%s\n' '# Knowledge Update Log' '' "## ${at%%T*}" '' "* **Update**: $summary" > knowledge/log.md
}

write_sync_set 2026-09-01T00:00:00Z 'Initial synchronized state.'
printf '%s\n' '# Guide' > docs/guide.md
git add .
git -c user.name=Test -c user.email=test@example.com commit -qm baseline

printf '%s\n' 'implementation' > app.txt
./.clineflow/bin/validate-knowledge-sync
rm app.txt

printf '%s\n' '# Guide' '' 'Unsynchronized documentation.' > docs/guide.md
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected documentation without ledger updates to fail' >&2
    exit 1
fi

write_sync_set 2026-09-03T08:30:00Z 'Reconciled documentation and durable knowledge.'
./.clineflow/bin/validate-knowledge-sync
git add .
./.clineflow/bin/validate-knowledge-sync --staged
BASE=$(git rev-parse HEAD)
git -c user.name=Test -c user.email=test@example.com commit -qm synchronized
./.clineflow/bin/validate-knowledge-sync --against "$BASE"

printf '%s\n' '# Guide' '' 'Mismatched synchronization.' > docs/guide.md
write_sync_set 2026-09-03T09:00:00Z 'Prepared a mismatched timestamp case.'
sed 's/2026-09-03T09:00:00Z/2026-09-03T09:01:00Z/' knowledge/clineflow_goals.yml > knowledge/clineflow_goals.tmp
mv knowledge/clineflow_goals.tmp knowledge/clineflow_goals.yml
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected mismatched ledger timestamps to fail' >&2
    exit 1
fi

printf '%s\n' '# Guide' '' 'Missing ledger change.' > docs/guide.md
write_sync_set 2026-09-03T09:10:00Z 'Prepared a missing ledger case.'
git show HEAD:knowledge/clineflow_goals.yml > knowledge/clineflow_goals.yml
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected an unchanged ledger to fail' >&2
    exit 1
fi

printf '%s\n' '# Guide' '' 'Missing knowledge log.' > docs/guide.md
write_sync_set 2026-09-03T09:20:00Z 'Prepared a missing knowledge log case.'
git show HEAD:knowledge/log.md > knowledge/log.md
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected an unchanged knowledge log to fail' >&2
    exit 1
fi

printf '%s\n' '# Guide' '' 'Missing active journal.' > docs/guide.md
write_sync_set 2026-09-03T09:30:00Z 'Prepared a missing active journal case.'
git show HEAD:knowledge/journals/task.md > knowledge/journals/task.md
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected an unchanged active journal to fail' >&2
    exit 1
fi

printf '%s\n' '# Guide' '' 'Missing journal reference.' > docs/guide.md
write_sync_set 2026-09-03T09:40:00Z 'Prepared a missing journal reference case.'
sed '/journals\/task.md/d' knowledge/clineflow_specification.yml > knowledge/clineflow_specification.tmp
mv knowledge/clineflow_specification.tmp knowledge/clineflow_specification.yml
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected a missing active-journal reference to fail' >&2
    exit 1
fi

printf '%s\n' '# Guide' '' 'Mismatched timeline event.' > docs/guide.md
write_sync_set 2026-09-03T09:50:00Z 'Prepared a mismatched timeline event case.'
sed 's/  - at: 2026-09-03T09:50:00Z/  - at: 2026-09-03T09:51:00Z/' knowledge/clineflow_timeline.yml > knowledge/clineflow_timeline.tmp
mv knowledge/clineflow_timeline.tmp knowledge/clineflow_timeline.yml
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected a mismatched latest timeline event to fail' >&2
    exit 1
fi

printf '%s\n' '# Guide' '' 'Restored synchronized state.' > docs/guide.md
write_sync_set 2026-09-03T10:00:00Z 'Restored a valid synchronized state.'
git add .
git -c user.name=Test -c user.email=test@example.com commit -qm validation-fixtures
mkdir -p docs/journals
printf '%s\n' 'legacy edits are forbidden' >> docs/journals/legacy.md
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
    echo 'expected legacy journal edits to fail' >&2
    exit 1
fi

if ./.clineflow/bin/validate-knowledge-sync --staged --against HEAD >/dev/null 2>&1; then
    echo 'expected mutually exclusive modes to fail' >&2
    exit 1
fi

echo 'Knowledge synchronization validator tests passed'
