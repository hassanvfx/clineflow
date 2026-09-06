#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
PROJECT="$WORK/project"
mkdir -p "$PROJECT"
cp -R "$ROOT/template/knowledge" "$PROJECT/knowledge"
cp -R "$ROOT/template/.clineflow" "$PROJECT/.clineflow"
cd "$PROJECT"
git init -q
git config user.email sync@example.com

./.clineflow/bin/knowledge sync >/dev/null
journal=$(./.clineflow/bin/knowledge journal new --topic synchronization --title 'Synchronization test')
stream=$(sed -n 's/^  stream: //p' "$journal")
record=$(./.clineflow/bin/knowledge record --topic synchronization --stream "$stream" --journal "$journal" --summary 'Validated source records.' --review specification=changed)
./.clineflow/bin/knowledge sync >/dev/null
./.clineflow/bin/validate-knowledge-sync

git add knowledge .clineflow
./.clineflow/bin/validate-knowledge-sync --staged
git -c user.name=Test -c user.email=test@example.com commit -qm baseline

printf '\n' >> "$record"
if ./.clineflow/bin/validate-knowledge-sync >/dev/null 2>&1; then
  echo 'expected edited immutable record to fail' >&2
  exit 1
fi
git checkout -- "$record"

git add "$record"
printf '{ staged and working tree differ\n' > "$record"
./.clineflow/bin/validate-knowledge-sync --staged
git checkout -- "$record"
git reset -q HEAD -- "$record"

mkdir -p docs/journals
printf 'legacy changes remain outside source records\n' > docs/journals/legacy.md
./.clineflow/bin/validate-knowledge-sync

echo 'Knowledge synchronization validator tests passed'
