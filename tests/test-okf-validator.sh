#!/usr/bin/env bash

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT
BUNDLE="$TEST_DIR/knowledge"
mkdir -p "$BUNDLE/journals"

create_valid_bundle() {
    mkdir -p "$BUNDLE/journals"
    printf '%s\n' '---' 'okf_version: "0.2"' '---' '' '# Knowledge' > "$BUNDLE/index.md"
    printf '%s\n' '# Log' '' '## 2026-08-15' '' '* **Creation**: Initialized.' > "$BUNDLE/log.md"
    printf '%s\n' '# Journals' > "$BUNDLE/journals/index.md"
}

create_valid_bundle
printf '%s\n' '---' 'type: Engineering Journal' '---' '' '# Task' > "$BUNDLE/journals/task.md"
bash "$ROOT/template/.clineflow/bin/validate-okf" "$BUNDLE"

if bash "$ROOT/template/.clineflow/bin/validate-okf" --strict "$BUNDLE" >/dev/null 2>&1; then
    echo "strict validation ran with available PyYAML"
else
    strict_status=$?
    if [ "$strict_status" -ne 2 ]; then
        echo "strict validation failed unexpectedly" >&2
        exit 1
    fi
fi

printf '%s\n' '---' 'title: Missing type' '---' > "$BUNDLE/journals/task.md"
if bash "$ROOT/template/.clineflow/bin/validate-okf" "$BUNDLE" >/dev/null 2>&1; then
    echo "expected missing type to fail" >&2
    exit 1
fi

printf '%s\n' '---' 'type: Custom Concept' 'producer_field: supported' '---' '' '[Future](/future.md)' > "$BUNDLE/journals/task.md"
bash "$ROOT/template/.clineflow/bin/validate-okf" "$BUNDLE"

printf '%s\n' '---' 'title: Invalid nested index' '---' > "$BUNDLE/journals/index.md"
printf '%s\n' '## 2026-01-01' '' '## 2026-08-15' > "$BUNDLE/log.md"
if bash "$ROOT/template/.clineflow/bin/validate-okf" "$BUNDLE" >/dev/null 2>&1; then
    echo "expected reserved-file violations to fail" >&2
    exit 1
fi

echo "OKF validator tests passed"
