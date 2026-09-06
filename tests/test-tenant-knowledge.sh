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
git config user.email 'Developer@Users.Noreply.GitHub.com'
git config user.name 'Developer Name'

./.clineflow/bin/knowledge sync >/dev/null
identity=$(./.clineflow/bin/knowledge identity show)
printf '%s\n' "$identity" | grep -q '"source": "email"'
printf '%s\n' "$identity" | grep -Eq '"id": "t-[0-9a-f]{32}"'
! printf '%s\n' "$identity" | grep -qi 'users.noreply' || { echo 'identity output leaked raw email' >&2; exit 1; }

journal_one=$(./.clineflow/bin/knowledge journal new --topic tenant-knowledge --title 'First stream')
journal_two=$(./.clineflow/bin/knowledge journal new --topic tenant-knowledge --title 'Second stream')
[ "$journal_one" != "$journal_two" ] || { echo 'independent streams collided' >&2; exit 1; }
for heading in 'Task Contract' 'Execution Boundaries' 'Existing Approaches' 'Planned Proof' 'Verification Results'; do
  grep -q "# $heading" "$journal_one" || { echo "generated journal omitted $heading" >&2; exit 1; }
done
stream_one=$(sed -n 's/^  stream: //p' "$journal_one")
stream_two=$(sed -n 's/^  stream: //p' "$journal_two")
tenant=$(sed -n 's/^  id: //p' "$journal_one")
[ "$tenant" = "$(sed -n 's/^  id: //p' "$journal_two")" ] || { echo 'tenant was not stable across streams' >&2; exit 1; }

record_one=$(./.clineflow/bin/knowledge record --topic tenant-knowledge --stream "$stream_one" --journal "$journal_one" --summary 'First independent update.' --item goals:tenant-journals='Use additive updates.')
record_two=$(./.clineflow/bin/knowledge record --topic tenant-knowledge --stream "$stream_two" --journal "$journal_two" --summary 'Second independent update.' --item goals:tenant-journals='Resolve the tenant journal policy explicitly.')
./.clineflow/bin/knowledge sync >/dev/null
./.clineflow/bin/knowledge validate
grep -q '"unresolved": true' knowledge/clineflow_goals.yml
grep -q "$tenant" "${record_one}"
! grep -Eq 'Developer@|Users\.Noreply|hostname|mac' "${record_one}" || { echo 'record leaked raw identity data' >&2; exit 1; }

git add knowledge .clineflow
git -c user.name=Test -c user.email=test@example.com commit -qm tenant-baseline
snapshot=$(sed -n 's/.*"snapshot": "\([^"]*\)".*/\1/p' "$record_one")
printf '\ncorrupted snapshot\n' >> "$snapshot"
if ./.clineflow/bin/knowledge validate >/dev/null 2>&1; then
  echo 'expected journal snapshot digest mismatch to fail' >&2
  exit 1
fi
git checkout -- "$snapshot"
printf '\n' >> "$record_one"
if ./.clineflow/bin/knowledge validate >/dev/null 2>&1; then
  echo 'expected published-record mutation to fail' >&2
  exit 1
fi
git checkout -- "$record_one"

git add "$record_one"
printf '{ invalid working tree data\n' > "$record_one"
./.clineflow/bin/knowledge validate --mode staged

git config user.email changed@example.com
drift=$(./.clineflow/bin/knowledge identity show)
printf '%s\n' "$drift" | grep -q 'detected_change'
if ./.clineflow/bin/knowledge journal new --topic identity-drift --title 'Must not create' >/dev/null 2>&1; then
  echo 'identity drift unexpectedly created a journal' >&2
  exit 1
fi
./.clineflow/bin/knowledge identity set email changed@example.com --name 'Developer Name' >/dev/null
./.clineflow/bin/knowledge journal new --topic identity-drift --title 'Explicit identity change works' >/dev/null

echo 'Tenant knowledge tests passed'
