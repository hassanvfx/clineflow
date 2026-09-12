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
[ -f .claude/commands/update-clineflow.md ] || fail "fresh install omitted deterministic Claude update command"
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
grep -q -- '--paper:' "$fixture/source/visor.css" && grep -q -- '--accent:' "$fixture/source/visor.css" && grep -q -- 'html.dark' "$fixture/source/visor.css" || fail "dashboard lost the scientific light/dark reader system"
printf 'var echarts={init:function(){return {setOption:function(){},resize:function(){}}}};\n' > "$fixture/assets/echarts.min.js"
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
import re
class MarkdownIt:
    def __init__(self, *args, **kwargs): pass
    def enable(self, *args, **kwargs): return self
    def inline(self, value):
        value = html.escape(value)
        value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
        value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
        value = re.sub(r'\*(.+?)\*', r'<em>\1</em>', value)
        return value
    def render(self, value):
        lines = value.splitlines(); output = []; index = 0
        while index < len(lines):
            line = lines[index]
            if not line.strip(): index += 1; continue
            heading = re.match(r'^(#{1,4})\s+(.+)$', line)
            if heading:
                level = len(heading.group(1)); output.append(f'<h{level}>' + self.inline(heading.group(2)) + f'</h{level}>'); index += 1; continue
            bullet = re.match(r'^[-*+]\s+(.+)$', line)
            ordered = re.match(r'^\d+\.\s+(.+)$', line)
            if bullet or ordered:
                tag = 'ul' if bullet else 'ol'; items = []
                while index < len(lines):
                    match = (re.match(r'^[-*+]\s+(.+)$', lines[index]) if tag == 'ul' else re.match(r'^\d+\.\s+(.+)$', lines[index]))
                    if not match: break
                    items.append('<li>' + self.inline(match.group(1)) + '</li>'); index += 1
                output.append(f'<{tag}>' + ''.join(items) + f'</{tag}>'); continue
            paragraph = [line.strip()]; index += 1
            while index < len(lines) and lines[index].strip() and not re.match(r'^(#{1,4}\s+|[-*+]\s+|\d+\.\s+)', lines[index]):
                paragraph.append(lines[index].strip()); index += 1
            output.append('<p>' + self.inline(' '.join(paragraph)) + '</p>')
        return ''.join(output)
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
for (const marker of ["Workspace", "Learning", "Sparks", "Activity", "Evidence", "reader-modal", "theme-toggle", "Report provenance", "Report chronology", "journal-library", "activity-day", "day-more", "Find records"]) {
  if (!source.includes(marker)) throw new Error(`Dashboard omitted ${marker}`);
}
NODE
PYTHONPATH="$fixture/modules" python3 - "$fixture/source/dashboard.py" <<'PY'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
spec = importlib.util.spec_from_file_location("dashboard", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
evidence = {"summary": "Dashboard evidence is structured", "command": "./tests/certify-release.sh"}
assert module.observation_text(evidence) == "Dashboard evidence is structured"
event = module.normalize_event({"timestamp": "2026-09-03T12:00:00Z", "category": "verification", "event": "Built and verified a reusable validation harness (analytics/tools/validation)", "references": "journals/example.md"})
assert event["at"] == "2026-09-03T12:00:00Z"
assert event["type"] == "verification"
assert event["summary"] == "Built and verified a reusable validation harness (analytics/tools/validation)"
assert event["title"] == "Built and verified a reusable validation harness"
assert event["refs"] == ["journals/example.md"]
journal = {
    "kind": "journal",
    "raw": "---\ntype: Engineering Journal\n---\n# Goal\n\n- [x] Keep **source fidelity**.\n- Use `safe_markdown`.\n\n# Decisions\n\n1. Render *Markdown* before raw source.\n",
    "description": "Reader formatting fixture",
}
guided = module.guided_document(journal)
assert guided["sections"][0]["type"] == "markdown"
assert "<strong>source fidelity</strong>" in guided["sections"][0]["html"]
assert "<code>safe_markdown</code>" in guided["sections"][0]["html"]
assert "<ol>" in guided["sections"][1]["html"]
ledger = {
    "kind": "ledger",
    "title": "Specification",
    "description": "Frozen specification ledger.",
    "structured": {
        "version": 3,
        "updated_at": "2026-09-12T00:00:00Z",
        "records": ["opaque-storage-id"],
        "items": [{"id": "design-confirmed", "alternatives": [{"record": "opaque-storage-id", "statement": "The project uses named records instead of exposed storage identifiers."}], "unresolved": False}],
    },
}
ledger_guided = module.guided_document(ledger)
assert ledger_guided["ledger_records"][0]["title"] == "Design Confirmed"
assert "opaque-storage-id" not in ledger_guided["ledger_records"][0]["title"]
assert all(section["label"] != "Records" for section in ledger_guided["sections"])
identity = module.report_identity({
    "run_at": "2026-09-03T12:00:00Z", "git": {"head": "a" * 40, "dirty": False},
    "commits": [{"revision": "a" * 40, "short_revision": "aaaaaaaa", "summary": "Captured change", "committed_at": "2026-09-03T10:00:00Z"}],
    "events": [{"at": "2026-09-01T09:00:00Z"}], "documents": [{"generated_at": "2026-09-02T09:00:00Z"}],
})
assert identity["revision"]["label"] == "Captured Git HEAD"
assert identity["latest_commit"]["summary"] == "Captured change"
assert identity["condition"]["state"] == "clean"
unknown_identity = module.report_identity({"run_at": "2026-09-03T12:00:00Z", "git": {}, "commits": [], "events": [], "documents": []})
assert unknown_identity["condition"]["state"] == "unknown"
mock_snapshot = {
    "schema": "clineflow-dashboard/v1", "run_at": "2026-09-03T12:00:00Z", "source_hash": "mock",
    "documents": [
        {"id": "goals", "path": "knowledge/clineflow_goals.yml"},
        {"id": "session", "path": "knowledge/clineflow_last_session.yml"},
        {"id": "verification", "path": "knowledge/clineflow_verification.yml"},
        {"id": "specification", "path": "knowledge/clineflow_specification.yml"},
        {"id": "timeline", "path": "knowledge/clineflow_timeline.yml"},
    ],
    "ledgers": {
        "clineflow_goals": {"active_goals": ["Ship a durable decision dashboard"]},
        "clineflow_last_session": {"latest_change": "Replaced a noisy graph with a project story", "next_recommended_step": "Review the source-bound story with the team"},
        "clineflow_verification": {"open_verification": ["Check keyboard navigation on the story cards"]},
        "clineflow_specification": {"open_questions": ["Which audience needs a weekly export?"]},
    },
    "events": [
        {"at": "2026-09-01T09:00:00Z", "title": "Defined the narrative brief", "summary": "Discovery began."},
        {"at": "2026-09-03T11:00:00Z", "title": "Reframed the dashboard around project story", "summary": "The design now leads with decisions."},
    ],
    "drift": {"added": ["knowledge/journals/story.md"], "changed": ["knowledge/clineflow_goals.yml"], "removed": []},
}
story = module.derive_observations(mock_snapshot)["project_story"]
assert story["evolution"]["text"].startswith("From Defined the narrative brief")
assert story["important_now"]["text"] == "Ship a durable decision dashboard"
assert "Which audience needs a weekly export?" in story["urgency"]["text"]
assert story["next_action"]["text"] == "Review the source-bound story with the team"
assert len(story["milestones"]) == 2
observations = module.derive_observations(mock_snapshot)
contract = module.observation_contract(mock_snapshot)
assert contract["schema"] == module.AGENT_CONTRACT_SCHEMA
assert contract["agent_input"]["allowed_fields"] == ["executive_summary", "delivery_estimate"]
assert contract["deterministic_observer"]["output_schema"] == module.OBSERVATION_SCHEMA
try:
    module.validate_insights_data({"project_phases": []}, {"goals"})
except ValueError as error:
    assert "allowed fields" in str(error)
else:
    raise AssertionError("unused agent insight fields were accepted")
try:
    module.validate_insights_data({"executive_summary": {"text": "Unsourced claim", "source_ids": []}}, {"goals"})
except ValueError as error:
    assert "known source_id" in str(error)
else:
    raise AssertionError("uncited agent summary was accepted")
assert set(observations["narratives"]) == {"origin", "overall", "recent", "digest"}
assert observations["coverage"]["journal_ids"] == []
assert observations["relationship_analysis"]["relationships"] == []
assert observations["relationship_analysis"]["unknowns"] == []
assert observations["sparks"] and observations["sparks"][0]["lifecycle"] == "new"
reconciled = module.derive_observations({**mock_snapshot, "previous_sparks": observations["sparks"], "previous_spark_run": "prior-run"})
assert reconciled["sparks"][0]["lifecycle"] == "unchanged"
assert reconciled["sparks"][0]["state"] == "emerging"
assert reconciled["sparks"][0]["supporting"] == []
baseline_history = module.report_history(mock_snapshot, observations)
assert baseline_history["mode"] == "baseline" and baseline_history["cards"][0]["value"] == "Baseline"
comparison_snapshot = {**mock_snapshot, "previous_report": {
    "run_id": "chronologically-later-name", "generated_at": "2026-09-02T12:00:00Z",
    "document_paths": ["knowledge/clineflow_goals.yml"], "journal_paths": [],
    "event_keys": [], "unresolved_count": 2, "sparks": observations["sparks"],
}}
comparison_observations = module.derive_observations({**comparison_snapshot, "previous_sparks": observations["sparks"], "previous_spark_run": "chronologically-later-name"})
comparison_history = module.report_history(comparison_snapshot, comparison_observations)
assert comparison_history["mode"] == "comparison"
assert comparison_history["previous_run"] == "chronologically-later-name"
assert any(card["label"] == "ACTIVITY DELTA" for card in comparison_history["cards"])
with tempfile.TemporaryDirectory() as root_dir:
    root = Path(root_dir)
    runs = root / "knowledge" / "dashboard" / "runs"
    for run_id, generated_at, project_title in (("zeta", "2026-09-03T12:00:00Z", "Other project"), ("alpha", "2026-09-02T12:00:00Z", "Correct project")):
        run = runs / run_id; run.mkdir(parents=True)
        (run / "manifest.json").write_text(json.dumps({"schema": module.SCHEMA, "run_id": run_id, "generated_at": generated_at}))
        (run / "snapshot.json").write_text(json.dumps({"schema": module.SCHEMA, "source_hash": run_id, "documents": [], "events": [], "ledgers": {}, "report_identity": {"project": {"title": project_title, "source_kind": "fixture"}}}))
        (run / "observations.json").write_text(json.dumps({"schema": module.OBSERVATION_SCHEMA, "sparks": []}))
    predecessor = module.collect_previous_report(root, {"title": "Correct project", "source_kind": "fixture"})
    assert predecessor and predecessor["run_id"] == "alpha", "predecessor must use matching project identity and generated chronology"
_, retired = module.reconcile_sparks([], observations["sparks"])
assert retired["retired"] == 1 and retired["retired_items"][0]["id"] == observations["sparks"][0]["id"]
decision = module.journal_spark_seed({"id": "journal", "path": "journal.md", "title": "Example", "raw": "# Goal\n\nBuild it.\n\n# Decisions\n\nUse stable cache keys because stale renders obscure a changed input.\n"}, "2026-09-03T12:00:00Z")
assert decision["origins"][0]["locator"] == "# Decisions"
assert decision["excerpt"] == "Use stable cache keys because stale renders obscure a changed input."
valid_spark = {
    "id": "cache-input-contract", "title": "Cache keys include output-changing inputs",
    "learning": "Include every output-changing input in the cache identity.",
    "scope": "Generated asset pipelines", "state": "supported", "limits": "Applies where the source records the dependency.",
    "origins": [{"source_id": "goals", "locator": "# Goal"}], "supporting": [{"source_id": "verification", "locator": "# Verification"}],
    "challenging": [], "synthesized_at": "2026-09-03T12:00:00Z",
}
observations["sparks"] = [valid_spark]
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
    json.dump(observations, handle); handle.flush()
    assert module.validate_observations(__import__("pathlib").Path(handle.name), mock_snapshot)["sparks"][0]["id"] == valid_spark["id"]
observations["sparks"] = [{**valid_spark, "supporting": valid_spark["origins"]}]
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
    json.dump(observations, handle); handle.flush()
    try:
        module.validate_observations(__import__("pathlib").Path(handle.name), mock_snapshot)
    except ValueError as error:
        assert "additional evidence" in str(error)
    else:
        raise AssertionError("a repeated origin was accepted as supporting evidence")
observations["sparks"] = []
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
    json.dump(observations, handle); handle.flush()
    try:
        module.validate_observations(__import__("pathlib").Path(handle.name), mock_snapshot)
    except ValueError as error:
        assert "source-bound Spark" in str(error)
    else:
        raise AssertionError("empty Sparks were accepted despite available source records")
observations["sparks"] = [{**valid_spark, "origins": [{"source_id": "missing", "locator": "# Goal"}]}]
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
    json.dump(observations, handle); handle.flush()
    try:
        module.validate_observations(__import__("pathlib").Path(handle.name), mock_snapshot)
    except ValueError as error:
        assert "unresolved source locator" in str(error)
    else:
        raise AssertionError("unresolved Spark citation was accepted")
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
  for asset in echarts.min.js gsap.min.js; do
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
[ -f "$report" ] && [ -f "${report%/index.html}/manifest.json" ] && [ -f "${report%/index.html}/snapshot.json" ] && [ -f "${report%/index.html}/observations.json" ] && [ -f "${report%/index.html}/presentation.json" ] || fail "activation omitted report artifacts"
find knowledge/dashboard/blog -path '*/index.json' -type f -print -quit | grep -q . || fail "activation omitted the project blog archive"
blog_index=$(find knowledge/dashboard/blog -path '*/index.html' -type f -print -quit)
grep -q 'ENGINEERING INDEX' "$blog_index" && grep -q 'SOURCE-BOUND RELEASE HISTORY' "$blog_index" && grep -q 'CHRONOLOGICAL ARCHIVE' "$blog_index" || fail "blog archive omitted the engineering history index"
grep -q "default-src 'none'" "$report" || fail "generated report omitted Content Security Policy"
grep -q "connect-src 'none'" "$report" || fail "generated report permits browser network access"
! grep -Eq "<(script|link|img)[^>]+(src|href)=['\\\"]https?://" "$report" || fail "self-contained report references a remote browser asset"
grep -q 'data:font/woff2;base64,' "$report" || fail "self-contained report omitted embedded fonts"
grep -q 'data-tab="workspace"' "$report" && grep -q '>Workspace</span>' "$report" && grep -q '>Sparks</span>' "$report" && grep -q '>Activity</span>' "$report" && grep -q '>Evidence</span>' "$report" && grep -q '>Learning</span>' "$report" && grep -q '>Blog</span>' "$report" || fail "dashboard omitted the report blog tab"
grep -q 'id="report-selector"' "$report" && grep -q 'Choose a frozen report' "$report" || fail "dashboard omitted the frozen-report selector"
grep -q 'Dark reader' "$report" && grep -q 'reader-modal' "$report" || fail "dashboard omitted theme and modal reader controls"
grep -q 'PROJECT MEMORY' "$report" && grep -q 'activity-list' "$report" && grep -q 'journal-library' "$report" && grep -q 'Report provenance' "$report" || fail "dashboard omitted progressive disclosure, activity, or provenance surfaces"
grep -q 'id="onboarding-panel"' "$report" && grep -q 'PROJECT ONBOARDING' "$report" && grep -q 'Copy question' "$report" || fail "dashboard omitted dedicated project onboarding"
grep -q 'DECISION LENSES' "$report" && grep -q 'Product manager' "$report" && grep -q 'Technical lead' "$report" && grep -q 'non-financial return proxy' "$report" || fail "dashboard omitted role-based source-bound decision lenses"
! grep -q 'Download PDF\|white-paper.pdf\|Evidence appendix\|primary-pdf' "$report" || fail "dashboard retained a removed white-paper action"
grep -q 'clineflow-dashboard/v1' "${report%/index.html}/snapshot.json" || fail "snapshot omitted dashboard schema"
python3 - "$report" "${report%/index.html}/snapshot.json" "${report%/index.html}/observations.json" "${report%/index.html}/presentation.json" <<'PY'
import json, re, sys
page = open(sys.argv[1], encoding="utf-8").read()
snapshot = json.load(open(sys.argv[2], encoding="utf-8"))
match = re.search(r'<script id="clineflow-data" type="application/json">(.*?)</script>', page, re.S)
if not match or json.loads(match.group(1)) != snapshot:
    raise SystemExit("embedded report data differs from adjacent snapshot.json")
observation_match = re.search(r'<script id="clineflow-observations" type="application/json">(.*?)</script>', page, re.S)
observations = json.load(open(sys.argv[3], encoding="utf-8"))
if not observation_match or json.loads(observation_match.group(1)) != observations:
    raise SystemExit("embedded narrative differs from adjacent observations.json")
presentation_match = re.search(r'<script id="clineflow-presentation" type="application/json">(.*?)</script>', page, re.S)
presentation = json.load(open(sys.argv[4], encoding="utf-8"))
if not presentation_match or json.loads(presentation_match.group(1)) != presentation:
    raise SystemExit("embedded presentation differs from adjacent presentation.json")
if presentation.get("schema") != "clineflow-dashboard-presentation/v1":
    raise SystemExit("presentation omitted its formal schema")
if presentation.get("source", {}).get("source_hash") != snapshot.get("source_hash"):
    raise SystemExit("presentation is not bound to its source facts")
blog = presentation.get("blog", {})
if blog.get("publication", {}).get("status") != "published" or not blog.get("current", {}).get("url") or not blog.get("index_json") or not blog.get("articles"):
    raise SystemExit("presentation omitted the release engineering blog")
if not blog.get("current", {}).get("json_url") or not all(item.get("json_url") for item in blog.get("articles", [])):
    raise SystemExit("presentation omitted agent-readable release article JSON links")
onboarding = presentation.get("onboarding", {})
if len(onboarding.get("steps", [])) != 3 or not all(step.get("prompt") and step.get("question") for step in onboarding.get("steps", [])):
    raise SystemExit("presentation omitted project-derived onboarding prompts")
commentary = presentation.get("workspace", {}).get("commentary", [])
if len(commentary) != 4 or not all("source_ids" in item for item in commentary):
    raise SystemExit("presentation omitted source-bound workspace commentary")
report_history = presentation.get("workspace", {}).get("report_history", {})
if report_history.get("mode") != "baseline" or len(report_history.get("cards", [])) != 3:
    raise SystemExit("first dashboard report omitted its chronological baseline commentary")
ledger_docs = [item for item in presentation.get("documents", []) if item.get("kind") == "ledger"]
if not ledger_docs or not all(record.get("highlights") for doc in ledger_docs for record in doc.get("guided", {}).get("ledger_records", [])):
    raise SystemExit("ledger records omitted compact key points for the reader")
lenses = presentation.get("workspace", {}).get("decision_lenses", [])
expected_lenses = {"product_manager", "executive", "technical_lead"}
if {item.get("id") for item in lenses} != expected_lenses:
    raise SystemExit("presentation omitted the three role-based decision lenses")
for lens in lenses:
    insights = lens.get("insights", [])
    if len(insights) != 3 or {item.get("category") for item in insights} != {"team", "time", "return"}:
        raise SystemExit("decision lens omitted the team, time, and return signals")
    if not all(item.get("source_ids") for item in insights):
        raise SystemExit("decision lens is not source-bound")
if not all("financial ROI" in item.get("text", "") or "financial" in item.get("text", "") for lens in lenses for item in lens.get("insights", []) if item.get("category") == "return"):
    raise SystemExit("decision lenses did not label return as non-financial")
if "insights" in snapshot:
    raise SystemExit("normalized facts contain the separate narrative model")
if observations.get("schema") != "clineflow-dashboard-observations/v1":
    raise SystemExit("observations omitted their formal schema")
if observations.get("source", {}).get("source_hash") != snapshot.get("source_hash"):
    raise SystemExit("observations are not bound to their source facts")
if set(observations.get("audiences", {})) != {"executive", "manager", "engineer"}:
    raise SystemExit("observations omitted an audience narrative")
if set(observations.get("narratives", {})) != {"origin", "overall", "recent", "digest"}:
    raise SystemExit("observations omitted the four source-bound narratives")
if set(observations.get("coverage", {})) != {"journal_ids", "covered_journal_ids", "uncovered_journal_ids"}:
    raise SystemExit("observations omitted explicit journal coverage")
if set(observations.get("relationship_analysis", {})) != {"relationships", "unknowns"}:
    raise SystemExit("observations omitted relationship uncertainty")
story = observations.get("project_story", {})
if set(("evolution", "important_now", "urgency", "next_action")) - set(story):
    raise SystemExit("observations omitted the narrative project story")
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
python3 - "knowledge/dashboard/runs" <<'PY'
import json, pathlib, sys
runs = pathlib.Path(sys.argv[1])
reports = []
for run in runs.iterdir():
    manifest = run / "manifest.json"
    if manifest.is_file():
        data = json.load(open(manifest, encoding="utf-8"))
        reports.append((data["generated_at"], data["run_id"], run))
_, _, latest = max(reports)
model = json.load(open(latest / "presentation.json", encoding="utf-8"))
history = model.get("workspace", {}).get("report_history", {})
if history.get("mode") != "comparison" or not history.get("previous_run"):
    raise SystemExit("repeat dashboard did not compare its predecessor JSON")
selector = model.get("report", {}).get("selector", [])
if len(selector) < 2 or sum(1 for item in selector if item.get("current")) != 1:
    raise SystemExit("repeat dashboard did not offer current and prior reports in the selector")
if not all(item.get("href") and item.get("run_id") and item.get("generated_at") for item in selector):
    raise SystemExit("report selector omitted a stable local route or report metadata")
if not any(item.get("label") == "ACTIVITY DELTA" for item in history.get("cards", [])):
    raise SystemExit("repeat dashboard omitted chronological activity commentary")
archives = list((runs.parent / "blog").glob("*/index.json"))
if len(archives) != 1:
    raise SystemExit("repeat dashboard created an unexpected number of project blog archives")
archive = json.load(open(archives[0], encoding="utf-8"))
if len(archive.get("articles", [])) != 1:
    raise SystemExit("unchanged facts created duplicate blog articles")
blog = model.get("blog", {})
if blog.get("publication", {}).get("status") != "nothing_new" or blog.get("current") is not None:
    raise SystemExit("unchanged facts did not report a no-new-publication blog state")
if not blog.get("latest_published", {}).get("url"):
    raise SystemExit("unchanged facts did not retain a link to the last blog post")
if "Nothing new to publish." not in (latest / "index.html").read_text(encoding="utf-8"):
    raise SystemExit("unchanged facts did not render the no-new-publication message")
PY
pass "activated dashboard reuses verified assets without network access"

facts="$TEST_ROOT/facts.json"
observations="$TEST_ROOT/observations.json"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard collect --output "$facts"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard contract --facts "$facts" > "$TEST_ROOT/agent-contract.json"
python3 - "$TEST_ROOT/agent-contract.json" <<'PY'
import json, sys
contract = json.load(open(sys.argv[1], encoding="utf-8"))
if contract.get("schema") != "clineflow-dashboard-agent-observation-contract/v1":
    raise SystemExit("agent contract omitted its schema")
if contract.get("agent_input", {}).get("allowed_fields") != ["executive_summary", "delivery_estimate"]:
    raise SystemExit("agent contract exposes an unbounded input surface")
if not contract.get("facts", {}).get("source_register"):
    raise SystemExit("agent contract omitted the source register")
PY
python3 - "$TEST_ROOT/invalid-agent-insights.json" <<'PY'
import json, sys
json.dump({"executive_summary": {"text": "Unsupported statement", "source_ids": ["not-a-source"]}}, open(sys.argv[1], "w", encoding="utf-8"))
PY
if PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$facts" --insights "$TEST_ROOT/invalid-agent-insights.json" --output "$TEST_ROOT/invalid-observations.json" --json-errors > /dev/null 2> "$TEST_ROOT/agent-diagnostic.json"; then fail "invalid agent input was accepted"; fi
python3 - "$TEST_ROOT/agent-diagnostic.json" <<'PY'
import json, sys
diagnostic = json.load(open(sys.argv[1], encoding="utf-8"))
errors = diagnostic.get("errors", [])
if diagnostic.get("schema") != "clineflow-dashboard-diagnostic/v1" or len(errors) != 1:
    raise SystemExit("agent failure did not emit one structured diagnostic")
if errors[0].get("code") != "INVALID_AGENT_INPUT" or not errors[0].get("retryable"):
    raise SystemExit("agent diagnostic did not identify a retryable input error")
PY
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$facts" --output "$observations"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$facts" --observations "$observations" --no-open >/dev/null
python3 - "$facts" "$observations" <<'PY'
import json, sys
facts, observations = (json.load(open(path, encoding="utf-8")) for path in sys.argv[1:])
if observations["source"]["source_hash"] != facts["source_hash"]:
    raise SystemExit("formal observation stage lost its facts binding")
PY
pass "facts, observations, and rendering remain independent JSON stages with a bounded agent retry contract"

python3 - "$ROOT/tests/fixtures/dashboard/adcrush-frozen/facts.json" "$ROOT/tests/fixtures/dashboard/adcrush-frozen/manifest.json" <<'PY'
import json, sys
facts, manifest = (json.load(open(path, encoding="utf-8")) for path in sys.argv[1:])
if manifest.get("schema") != "clineflow-dashboard-fixture/v1" or manifest.get("project") != "sibling project ad-crush":
    raise SystemExit("frozen Ad Crush fixture lost source provenance")
if facts.get("source_hash") != manifest.get("facts_source_hash") or facts.get("frozen_source", {}).get("commit") != manifest.get("commit"):
    raise SystemExit("frozen Ad Crush fixture lost content binding")
if len(facts.get("documents", [])) != len(manifest.get("sources", [])):
    raise SystemExit("frozen Ad Crush fixture source count differs from its manifest")
identity = facts.get("report_identity", {})
if identity.get("project", {}).get("title") != "Ad Crush":
    raise SystemExit("frozen Ad Crush fixture omitted its project identity")
if identity.get("revision", {}).get("value") != manifest.get("commit") or identity.get("revision", {}).get("kind") != "baseline":
    raise SystemExit("frozen Ad Crush fixture omitted its named baseline")
if identity.get("latest_commit", {}).get("kind") != "unavailable" or identity.get("condition", {}).get("state") != "frozen-snapshot":
    raise SystemExit("frozen Ad Crush fixture misrepresented captured Git state")
PY
pass "frozen Ad Crush dashboard sample retains source provenance"

for fixture_name in comprehensive minimal empty adcrush-frozen; do
  fixture_facts="$ROOT/tests/fixtures/dashboard/$fixture_name/facts.json"
  fixture_observations="$TEST_ROOT/$fixture_name-observations.json"
  if [ -f "$ROOT/tests/fixtures/dashboard/$fixture_name/insights.json" ]; then
    PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$fixture_facts" --output "$fixture_observations" --insights "$ROOT/tests/fixtures/dashboard/$fixture_name/insights.json"
  else
    PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$fixture_facts" --output "$fixture_observations"
  fi
  fixture_report=$(PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$fixture_facts" --observations "$fixture_observations" --retain unlimited --no-open)
  [ -f "$fixture_report" ] && [ -f "${fixture_report%/index.html}/presentation.json" ] || fail "$fixture_name fixture did not render a presentation"
  python3 - "$fixture_report" "${fixture_report%/index.html}/presentation.json" "$fixture_name" <<'PY'
import json, re, sys
page = open(sys.argv[1], encoding="utf-8").read()
model = json.load(open(sys.argv[2], encoding="utf-8"))
embedded = re.search(r'<script id="clineflow-presentation" type="application/json">(.*?)</script>', page, re.S)
if not embedded or json.loads(embedded.group(1)) != model:
    raise SystemExit("fixture presentation is not embedded exactly")
if "[object Object]" in page:
    raise SystemExit("fixture rendered object coercion")
if sys.argv[3] == "empty" and "No journals in this snapshot" not in page:
    raise SystemExit("empty fixture omitted journal onboarding")
if sys.argv[3] == "comprehensive" and "Verified local-only reports" not in page:
    raise SystemExit("comprehensive fixture omitted verification narrative")
if not all(marker in page for marker in ("Workspace", "Learning", "Activity", "Evidence", "PROJECT ONBOARDING", "Copy question")):
    raise SystemExit("fixture omitted the V1 report surfaces")
estimate = model.get("delivery_estimate")
if sys.argv[3] == "comprehensive":
    if not estimate or estimate.get("agent", {}).get("model") != "gpt-5.6-sol":
        raise SystemExit("comprehensive fixture omitted agent-supplied delivery estimate")
    current, without_flow, no_ai = estimate["scenarios"]
    if (current["estimated_cost"], without_flow["estimated_cost"], no_ai["estimated_cost"]) != (1818.0, 2718.0, 4500.0):
        raise SystemExit("delivery scenario costs were not calculated from constants")
elif estimate is not None:
    raise SystemExit("sparse fixture fabricated a delivery estimate")
if sys.argv[3] == "adcrush-frozen":
    identity = model.get("identity", {})
    if identity.get("project", {}).get("title") != "Ad Crush":
        raise SystemExit("frozen Ad Crush presentation lost project identity")
    if identity.get("condition", {}).get("state") != "frozen-snapshot":
        raise SystemExit("frozen Ad Crush presentation leaked host condition")
    if len(model.get("workspace", {}).get("workstreams", [])) != 5:
        raise SystemExit("frozen Ad Crush fixture omitted its active workstreams")
    if len(model.get("workspace", {}).get("commentary", [])) != 4:
        raise SystemExit("frozen Ad Crush fixture omitted workspace commentary")
    if len(model.get("onboarding", {}).get("steps", [])) != 3:
        raise SystemExit("frozen Ad Crush fixture omitted project onboarding")
    assert all(step.get("answer") and step.get("source_ids") for step in model["onboarding"]["steps"])
    assert len(model["evidence_register"]["verification"]) == 33
    assert all(item.get("recorded_at") == "2026-09-11T22:33:08Z" and item.get("date_label") == "Ledger snapshot" for item in model["evidence_register"]["verification"])
    assert len(model["now"]["follow_ups"]) == 27
    assert all(item.get("recorded_at") == "2026-09-11T22:33:08Z" and item.get("date_label") == "Ledger snapshot" for item in model["now"]["follow_ups"])
    assert "Two per-clip aggregates" in model["now"]["latest_change"]
    assert model["now"]["intent"] == "", "Do not invent a designated goal from alphabetical ledger order"
    assert all(spark["state"] == "emerging" for spark in model["sparks"])
    if len(model.get("activity", {}).get("events", [])) < 10:
        raise SystemExit("frozen Ad Crush fixture omitted its timeline")
PY
done
pass "comprehensive, minimal, and empty fixture facts render through observe and render"

# Delivery estimates accept explicit agent assumptions only and reject malformed or unsafe inputs.
invalid_estimate="$TEST_ROOT/invalid-delivery-estimate.json"
python3 - "$ROOT/tests/fixtures/dashboard/comprehensive/insights.json" "$invalid_estimate" <<'PY'
import copy, json, sys
base = json.load(open(sys.argv[1], encoding="utf-8"))
cases = {
    "currency": lambda item: item["constants"].update(currency="usd"),
    "rate": lambda item: item["constants"].update(loaded_hourly_rate=0),
    "hours": lambda item: item["constants"].update(baseline_hours=-1),
    "direct_cost": lambda item: item["constants"]["no_ai"].update(direct_cost=-1),
    "multiplier": lambda item: item["constants"]["ai_without_clineflow"].update(effort_multiplier=0),
    "source": lambda item: item.update(source_ids=["unknown-document"]),
    "total": lambda item: item.update(estimated_cost=1),
}
json.dump({name: (lambda candidate, mutate=mutate: (mutate(candidate), candidate)[1])(copy.deepcopy(base["delivery_estimate"])) for name, mutate in cases.items()}, open(sys.argv[2], "w", encoding="utf-8"))
PY
for invalid_case in currency rate hours direct_cost multiplier source total; do
  python3 - "$invalid_estimate" "$TEST_ROOT/$invalid_case-insights.json" "$invalid_case" <<'PY'
import json, sys
all_cases = json.load(open(sys.argv[1], encoding="utf-8"))
json.dump({"delivery_estimate": all_cases[sys.argv[3]]}, open(sys.argv[2], "w", encoding="utf-8"))
PY
  if PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$ROOT/tests/fixtures/dashboard/comprehensive/facts.json" --insights "$TEST_ROOT/$invalid_case-insights.json" --output "$TEST_ROOT/$invalid_case-observations.json" >/dev/null 2>&1; then fail "invalid delivery estimate $invalid_case was accepted"; fi
done
pass "delivery estimates validate inputs and reject agent-provided totals"

estimate_observations="$TEST_ROOT/estimate-observations.json"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard observe --facts "$ROOT/tests/fixtures/dashboard/comprehensive/facts.json" --insights "$ROOT/tests/fixtures/dashboard/comprehensive/insights.json" --output "$estimate_observations"
estimate_report=$(PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$ROOT/tests/fixtures/dashboard/comprehensive/facts.json" --observations "$estimate_observations" --retain unlimited --no-open)
estimate_run=$(basename "$(dirname "$estimate_report")")
estimate_export="$TEST_ROOT/sanitized-estimate"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard --yes export --run "$estimate_run" --output "$estimate_export" >/dev/null
python3 - "$estimate_export/observations.json" "$estimate_export/presentation.json" "$estimate_export/index.html" <<'PY'
import json, sys
observations = json.load(open(sys.argv[1], encoding="utf-8"))
presentation = json.load(open(sys.argv[2], encoding="utf-8"))
page = open(sys.argv[3], encoding="utf-8").read()
if "delivery_estimate" in observations or "delivery_estimate" in presentation:
    raise SystemExit("sanitized export retained delivery-estimate data")
if any(value in page for value in ("gpt-5.6-sol", "2718", "150.0")):
    raise SystemExit("sanitized export leaked delivery-estimate values")
PY
grep -q 'data-tab="workspace"' "$estimate_export/index.html" && grep -q '>Workspace</span>' "$estimate_export/index.html" || fail "sanitized export removed the report shell"
pass "sanitized exports exclude delivery scenarios and retain the report shell"

for _ in 1 2 3 4; do
  PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$ROOT/tests/fixtures/dashboard/minimal/facts.json" --retain 3 --no-open >/dev/null
done
[ "$(find knowledge/dashboard/runs -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" -eq 3 ] || fail "default retention did not keep three completed reports"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard settings --retain 5 >/dev/null
grep -q '"retention": 5' knowledge/dashboard/settings.json || fail "retention settings were not written under the dashboard boundary"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard settings --show | grep -q '"retention": 5' || fail "retention settings could not be inspected"
for _ in 1 2; do
  PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$ROOT/tests/fixtures/dashboard/minimal/facts.json" --no-open >/dev/null
done
[ "$(find knowledge/dashboard/runs -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" -eq 5 ] || fail "configured retention did not keep five reports"
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard settings --retain unlimited >/dev/null
PYTHONPATH="$fixture/modules" ./.clineflow/bin/dashboard render --facts "$ROOT/tests/fixtures/dashboard/empty/facts.json" --no-open >/dev/null
[ "$(find knowledge/dashboard/runs -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" -eq 6 ] || fail "unlimited retention did not preserve completed reports"
pass "dashboard retention settings support default, configured, and unlimited history"

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
