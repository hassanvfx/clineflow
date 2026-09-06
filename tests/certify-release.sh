#!/usr/bin/env bash
# One-command release gate for installation, updates, removal, and durable knowledge.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

AGAINST=''
if [ "${1:-}" = --against ]; then
  AGAINST=${2:-}
  [ -n "$AGAINST" ] || { echo "Usage: $0 [--against GIT_REF]" >&2; exit 2; }
elif [ "${1:-}" = --help ] || [ "${1:-}" = -h ]; then
  echo "Usage: $0 [--against GIT_REF]"
  exit 0
elif [ "$#" -gt 0 ]; then
  echo "Usage: $0 [--against GIT_REF]" >&2
  exit 2
fi

echo "==> Shell syntax"
bash -n update.sh template/.clineflow/bin/doctor template/.clineflow/bin/install template/.clineflow/bin/prereqs template/.clineflow/bin/uninstall template/.clineflow/bin/update template/.clineflow/bin/validate-knowledge-sync template/.clineflow/bin/validate-okf template/.clineflow/bin/validate-release tests/*.sh

echo "==> Release contract"
if [ -n "$AGAINST" ]; then ./template/.clineflow/bin/validate-release --against "$AGAINST"
else ./template/.clineflow/bin/validate-release; fi

echo "==> Installation lifecycle"
./tests/test-installation-flow.sh

echo "==> Optional dashboard dormant and activated boundaries"
./tests/test-dashboard.sh

echo "==> Historical update and rollback matrix"
./tests/test-update-migrations.sh

echo "==> Uninstall safety and rollback matrix"
./tests/test-uninstall-safety.sh

echo "==> Release-contract rejection matrix"
./tests/test-release-contract.sh

echo "==> OKF validator matrix"
./tests/test-okf-validator.sh
./template/.clineflow/bin/validate-okf

echo "==> Knowledge synchronization matrix"
./tests/test-knowledge-sync.sh
if [ -n "$AGAINST" ]; then ./template/.clineflow/bin/validate-knowledge-sync --against "$AGAINST"
else ./template/.clineflow/bin/validate-knowledge-sync; fi

echo "==> Tenant knowledge matrix"
./tests/test-tenant-knowledge.sh

echo "==> Whitespace integrity"
git diff --check

echo "ClineFlow lifecycle certification passed."
