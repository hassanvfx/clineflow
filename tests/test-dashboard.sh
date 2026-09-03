#!/usr/bin/env bash
# Prove the optional Knowledge Visor remains dormant and activates within its declared boundary.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
INSTALL="$ROOT/template/.clineflow/bin/install"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/clineflow-dashboard-test-XXXXXX")
trap 'rm -rf "$TEST_ROOT"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }
sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  else shasum -a 256 "$1" | awk '{print $1}'; fi
}
snapshot_knowledge() {
  find knowledge -type f ! -path 'knowledge/dashboard/*' -exec shasum -a 256 {} \; | LC_ALL=C sort | shasum -a 256 | awk '{print $1}'
}

project="$TEST_ROOT/project"
mkdir -p "$project"
cd "$project"
git init -q
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" >/dev/null
[ -x .clineflow/bin/dashboard ] || fail "fresh install omitted inert dashboard bootstrap"
[ -f .clineflow/dashboard-component-manifest ] || fail "fresh install omitted dashboard component manifest"
[ ! -e .clineflow/optional ] && [ ! -e knowledge/dashboard ] || fail "fresh install activated optional dashboard state"
! grep -q 'CLINEFLOW DASHBOARD GENERATED REPORTS' .git/info/exclude || fail "fresh install changed Git exclusions"
./.clineflow/bin/doctor >/dev/null
pass "fresh installation keeps the dashboard dormant"

git config user.name test
git config user.email test@example.invalid
git add .
git commit -qm baseline
before_decline=$(snapshot_knowledge)
if ./.clineflow/bin/dashboard </dev/null >/dev/null 2>&1; then fail "non-interactive first use bypassed approval"; fi
[ ! -e .clineflow/optional ] && [ ! -e knowledge/dashboard ] || fail "declined activation created dashboard state"
[ "$before_decline" = "$(snapshot_knowledge)" ] || fail "declined activation changed canonical knowledge"
! grep -q 'CLINEFLOW DASHBOARD GENERATED REPORTS' .git/info/exclude || fail "declined activation changed Git exclusions"
pass "declined activation is non-mutating"

fixture="$TEST_ROOT/fixture"
mkdir -p "$fixture/source" "$fixture/assets" "$fixture/uv/uv-test" "$fixture/modules"
cp "$ROOT"/template/optional/dashboard/* "$fixture/source/"
printf 'var echarts={init:function(){return {setOption:function(){},resize:function(){}}}};\n' > "$fixture/assets/echarts.min.js"
printf 'function cytoscape(){return {on:function(){}}}\n' > "$fixture/assets/cytoscape.min.js"
printf 'var gsap={from:function(){}};\n' > "$fixture/assets/gsap.min.js"
printf 'wOF2space' > "$fixture/assets/space-grotesk.woff2"
printf 'wOF2ibm400' > "$fixture/assets/ibm-plex-mono-400.woff2"
printf 'wOF2ibm500' > "$fixture/assets/ibm-plex-mono-500.woff2"
cat > "$fixture/uv/uv-test/uv" <<'EOF'
#!/usr/bin/env bash
while [ "$#" -gt 0 ]; do
  case "$1" in *.py) script=$1; shift; exec python3 "$script" "$@" ;; *) shift ;; esac
done
exit 2
EOF
chmod +x "$fixture/uv/uv-test/uv"
tar -czf "$fixture/assets/uv.tar.gz" -C "$fixture/uv" uv-test
cat > "$fixture/modules/bleach.py" <<'PY'
def clean(value, **kwargs):
    return value
PY
cat > "$fixture/modules/markdown_it.py" <<'PY'
import html
class MarkdownIt:
    def __init__(self, *args, **kwargs): pass
    def render(self, value): return '<pre>' + html.escape(value) + '</pre>'
PY
cat > "$fixture/modules/yaml.py" <<'PY'
import json
YAMLError = Exception
def scalar(value):
    value=value.strip()
    if value in ('null','~'): return None
    if value == '[]': return []
    if value == '{}': return {}
    if value in ('true','false'): return value == 'true'
    if value.startswith('[') and value.endswith(']'):
        return [part.strip().strip('"\'') for part in value[1:-1].split(',') if part.strip()]
    if value.startswith(('"', "'")) and value.endswith(('"', "'")): return value[1:-1]
    try: return int(value)
    except ValueError: return value
def safe_load(text):
    root={}; stack=[(-1,root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith('#') or ':' not in raw: continue
        indent=len(raw)-len(raw.lstrip()); key,value=raw.strip().split(':',1)
        while stack[-1][0] >= indent: stack.pop()
        parent=stack[-1][1]
        if value.strip(): parent[key]=scalar(value)
        else: parent[key]={}; stack.append((indent,parent[key]))
    return root
def safe_dump(value, **kwargs):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'
PY

node - "$fixture/source/visor.js" <<'NODE'
const fs = require("fs");
const source = fs.readFileSync(process.argv[2], "utf8");
const start = source.indexOf("  const humanize =");
const end = source.indexOf("  const journalDocs =");
if (start < 0 || end < 0) throw new Error("Atlas statement formatter is missing");
const helpers = new Function(`${source.slice(start, end)}; return {statementText, statementDetail, shortLabel};`)();
const evidence = {summary: "Dashboard evidence is structured", command: "./tests/certify-release.sh", status: "passed"};
if (helpers.statementText(evidence) !== "Dashboard evidence is structured") throw new Error("Atlas did not select a structured evidence summary");
if (!helpers.statementDetail(evidence).includes("Command: ./tests/certify-release.sh")) throw new Error("Atlas did not preserve structured evidence metadata");
if (helpers.shortLabel(evidence).includes("[object Object]")) throw new Error("Atlas still coerces evidence objects");
NODE
PYTHONPATH="$fixture/modules" python3 - "$fixture/source/dashboard.py" <<'PY'
import importlib.util
import sys
spec = importlib.util.spec_from_file_location("dashboard", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
evidence = {"summary": "Dashboard evidence is structured", "command": "./tests/certify-release.sh"}
assert module.observation_text(evidence) == "Dashboard evidence is structured"
event = module.normalize_event({"timestamp": "2026-09-03T12:00:00Z", "category": "verification", "description": "Structured timeline event", "references": "journals/example.md"})
assert event["at"] == "2026-09-03T12:00:00Z"
assert event["type"] == "verification"
assert event["summary"] == "Structured timeline event"
assert event["refs"] == ["journals/example.md"]
PY

component="$project/.clineflow/dashboard-component-manifest"
{
  echo 'component_version=test-1'
  echo 'python_version=3.12'
  for source in dashboard.py dashboard.py.lock visor.css visor.js THIRD_PARTY_LICENSES.md; do
    echo "file|$source|$source|$(sha256_file "$fixture/source/$source")"
  done
  echo "runtime|darwin-arm64|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  echo "runtime|darwin-x86_64|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  echo "runtime|linux-arm64-gnu|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  echo "runtime|linux-arm64-musl|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  echo "runtime|linux-x86_64-gnu|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  echo "runtime|linux-x86_64-musl|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  echo "runtime|windows-x86_64|tar.gz|file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")"
  for asset in echarts.min.js cytoscape.min.js gsap.min.js; do
    echo "asset|javascript|$asset|test|file://$fixture/assets/$asset|-|$(sha256_file "$fixture/assets/$asset")|MIT"
  done
  for asset in space-grotesk.woff2 ibm-plex-mono-400.woff2 ibm-plex-mono-500.woff2; do
    echo "asset|font|$asset|test|file://$fixture/assets/$asset|-|$(sha256_file "$fixture/assets/$asset")|OFL-1.1"
  done
} > "$component"
git add .clineflow/dashboard-component-manifest
git commit -qm 'test component manifest'
before_activation=$(snapshot_knowledge)
index_before=$(git write-tree)
BROWSER=true PYTHONPATH="$fixture/modules" CLINEFLOW_DASHBOARD_TEST_ALLOW_FILE=true CLINEFLOW_DASHBOARD_BASE_URL="file://$fixture/source" ./.clineflow/bin/dashboard --yes > "$TEST_ROOT/generated-path"
[ -f .clineflow/optional/dashboard/.active ] || fail "activation omitted active runtime marker"
[ -x .clineflow/optional/bin/uv ] || fail "activation omitted isolated uv runtime"
report=$(tail -n 1 "$TEST_ROOT/generated-path")
[ -f "$report" ] && [ -f "${report%/index.html}/manifest.json" ] && [ -f "${report%/index.html}/snapshot.json" ] && [ -f "${report%/index.html}/observations.json" ] || fail "activation omitted report artifacts"
grep -q "default-src 'none'" "$report" || fail "generated report omitted Content Security Policy"
grep -q "connect-src 'none'" "$report" || fail "generated report permits browser network access"
! grep -Eq "<(script|link|img)[^>]+(src|href)=['\\\"]https?://" "$report" || fail "self-contained report references a remote browser asset"
grep -q 'data:font/woff2;base64,' "$report" || fail "self-contained report omitted embedded fonts"
! grep -q 'About this report' "$report" || fail "dashboard retained the removed asset panel"
grep -q 'Manager view' "$report" && grep -q 'Engineering view' "$report" && grep -q 'Source of truth' "$report" || fail "dashboard omitted its multi-audience story chapters"
grep -q 'data-atlas="overview"' "$report" && grep -q 'data-atlas="journals"' "$report" || fail "Decision Atlas omitted progressive disclosure controls"
grep -q 'slice(0,10)' "$report" || fail "Decision Atlas omitted its visible-node cap"
! grep -q 'layout:{name:"cose"' "$report" || fail "Decision Atlas retained the overlapping force layout"
grep -q 'Guided view' "$report" && grep -q 'Copy normalized YAML' "$report" || fail "Knowledge Explorer omitted YAML interpretation and repair controls"
grep -q 'data-filter="ledger"' "$report" && grep -q 'data-filter="journal"' "$report" || fail "Knowledge Explorer omitted progressive document filters"
grep -q 'clineflow-dashboard/v1' "${report%/index.html}/snapshot.json" || fail "snapshot omitted dashboard schema"
python3 - "$report" "${report%/index.html}/snapshot.json" "${report%/index.html}/observations.json" <<'PY'
import json, re, sys
page = open(sys.argv[1], encoding="utf-8").read()
match = re.search(r'<script id="clineflow-data" type="application/json">(.*?)</script>', page, re.S)
if not match or json.loads(match.group(1)) != json.load(open(sys.argv[2], encoding="utf-8")):
    raise SystemExit("embedded report data differs from adjacent snapshot.json")
observation_match = re.search(r'<script id="clineflow-observations" type="application/json">(.*?)</script>', page, re.S)
observations = json.load(open(sys.argv[3], encoding="utf-8"))
if not observation_match or json.loads(observation_match.group(1)) != observations:
    raise SystemExit("embedded narrative differs from adjacent observations.json")
snapshot = json.load(open(sys.argv[2], encoding="utf-8"))
if "insights" in snapshot:
    raise SystemExit("normalized facts contain the separate narrative model")
if observations.get("schema") != "clineflow-dashboard-observations/v1":
    raise SystemExit("observations omitted their formal schema")
if observations.get("source", {}).get("source_hash") != snapshot.get("source_hash"):
    raise SystemExit("observations are not bound to their source facts")
if set(observations.get("audiences", {})) != {"executive", "manager", "engineer"}:
    raise SystemExit("observations omitted an audience narrative")
ledger = next((doc for doc in snapshot["documents"] if doc.get("kind") == "ledger"), None)
if not ledger or not ledger.get("yaml", {}).get("valid") or not isinstance(ledger.get("structured"), dict):
    raise SystemExit("dashboard did not retain a parsed, structured YAML ledger")
if not ledger["yaml"].get("normalized"):
    raise SystemExit("dashboard did not retain normalized YAML repair output")
PY
python3 - "${report%/index.html}/manifest.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
required = {"name", "version", "sha256", "license", "primary"}
if not manifest.get("assets") or any(not required.issubset(asset) for asset in manifest["assets"]):
    raise SystemExit("report manifest lost asset provenance after removing the visible panel")
PY
grep -qFx '/.clineflow/optional/' .git/info/exclude && grep -qFx '/knowledge/dashboard/' .git/info/exclude || fail "activation omitted exact Git exclusions"
[ "$before_activation" = "$(snapshot_knowledge)" ] || fail "activation changed canonical knowledge"
[ "$index_before" = "$(git write-tree)" ] || fail "activation changed the Git index"
[ -z "$(git status --porcelain)" ] || fail "activated boundaries leaked into Git status"
pass "first activation defaults to the generate subcommand"
./.clineflow/bin/dashboard doctor >/dev/null
./.clineflow/bin/validate-knowledge-sync >/dev/null
pass "activation changes only isolated, ignored dashboard boundaries"

mkdir "$TEST_ROOT/no-network"
cat > "$TEST_ROOT/no-network/curl" <<'EOF'
#!/usr/bin/env bash
echo 'unexpected network access' >&2
exit 97
EOF
chmod +x "$TEST_ROOT/no-network/curl"
PATH="$TEST_ROOT/no-network:$PATH" PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard generate --no-open >/dev/null
[ "$(find knowledge/dashboard/runs -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" -eq 2 ] || fail "offline repeat did not create a second run"
pass "activated dashboard reuses verified assets without network access"

facts="$TEST_ROOT/facts.json"
observations="$TEST_ROOT/observations.json"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard collect --output "$facts"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$facts" --output "$observations"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$facts" --observations "$observations" --no-open >/dev/null
python3 - "$facts" "$observations" <<'PY'
import json, sys
facts, observations = (json.load(open(path, encoding="utf-8")) for path in sys.argv[1:])
if observations["source"]["source_hash"] != facts["source_hash"]:
    raise SystemExit("formal observation stage lost its facts binding")
PY
pass "facts, observations, and rendering remain independent JSON stages"

rollback_project="$TEST_ROOT/rollback-project"
mkdir -p "$rollback_project"
cd "$rollback_project"
git init -q
CLINEFLOW_BASE_URL="file://$ROOT/template" bash "$INSTALL" >/dev/null
git config user.name test
git config user.email test@example.invalid
git add .
git commit -qm baseline
cp "$component" .clineflow/dashboard-component-manifest
git add .clineflow/dashboard-component-manifest
git commit -qm 'test component manifest'
cat > "$fixture/uv/uv-test/uv" <<'EOF'
#!/usr/bin/env bash
exit 88
EOF
chmod +x "$fixture/uv/uv-test/uv"
tar -czf "$fixture/assets/uv-fail.tar.gz" -C "$fixture/uv" uv-test
sed -i.bak "s#file://$fixture/assets/uv.tar.gz|$(sha256_file "$fixture/assets/uv.tar.gz")#file://$fixture/assets/uv-fail.tar.gz|$(sha256_file "$fixture/assets/uv-fail.tar.gz")#g" .clineflow/dashboard-component-manifest
rm -f .clineflow/dashboard-component-manifest.bak
before_failure=$(snapshot_knowledge)
if PYTHONPATH="$fixture/modules" CLINEFLOW_DASHBOARD_TEST_ALLOW_FILE=true CLINEFLOW_DASHBOARD_BASE_URL="file://$fixture/source" ./.clineflow/bin/dashboard --yes generate --no-open >/dev/null 2>&1; then fail "post-verification engine failure succeeded"; fi
[ ! -e .clineflow/optional ] && [ ! -e knowledge/dashboard ] || fail "failed first generation retained activated state"
[ "$before_failure" = "$(snapshot_knowledge)" ] || fail "failed first generation changed canonical knowledge"
! grep -q 'CLINEFLOW DASHBOARD GENERATED REPORTS' .git/info/exclude || fail "failed first generation retained Git exclusion"
pass "post-verification generation failure rolls activation back completely"

cd "$project"

export_dir="$TEST_ROOT/sanitized"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard --yes export --run latest --output "$export_dir" >/dev/null
[ -f "$export_dir/index.html" ] && [ -f "$export_dir/data.json" ] && [ -f "$export_dir/observations.json" ] || fail "sanitized export is incomplete"
! grep -q '"raw": "#' "$export_dir/data.json" || fail "sanitized export leaked full journal bodies"
pass "sanitized export embeds the viewer without full knowledge bodies"

./.clineflow/bin/uninstall --yes >/dev/null
[ ! -e .clineflow ] || fail "uninstall retained optional runtime"
[ -d knowledge/dashboard/runs ] || fail "uninstall removed generated dashboard reports"
! grep -q 'CLINEFLOW DASHBOARD GENERATED REPORTS' .git/info/exclude || fail "uninstall retained dashboard exclusion marker"
pass "uninstall removes optional tooling and preserves reports"

echo "ClineFlow dashboard boundary tests passed."
