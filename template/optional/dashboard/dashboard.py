# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#   "bleach==6.2.0",
#   "markdown-it-py==4.0.0",
#   "PyYAML==6.0.2",
# ]
# ///
"""Generate the local, time-first ClineFlow Knowledge Visor."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

try:
    import bleach
    import yaml
    from markdown_it import MarkdownIt
except ImportError as exc:  # pragma: no cover - the bootstrap supplies the locked environment
    raise SystemExit(f"dashboard runtime is incomplete: {exc}") from exc

SCHEMA = "clineflow-dashboard/v1"
OBSERVATION_SCHEMA = "clineflow-dashboard-observations/v1"
LEDGERS = (
    "clineflow_specification.yml",
    "clineflow_verification.yml",
    "clineflow_goals.yml",
    "clineflow_last_session.yml",
    "clineflow_timeline.yml",
)
SOURCE_SUFFIXES = {".md", ".yml", ".yaml"}
ALLOWED_TAGS = {
    "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4",
    "hr", "li", "ol", "p", "pre", "strong", "table", "tbody", "td", "th",
    "thead", "tr", "ul",
}


def run_git(root: Path, *args: str, check: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout if result.returncode == 0 else ""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return value


def canonical_sources(root: Path) -> list[Path]:
    knowledge = root / "knowledge"
    if not knowledge.is_dir():
        raise RuntimeError("knowledge/ does not exist")
    return sorted(
        path for path in knowledge.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SOURCE_SUFFIXES
        and "dashboard" not in path.relative_to(knowledge).parts
    )


def markdown_renderer() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})


def safe_markdown(renderer: MarkdownIt, value: str) -> str:
    rendered = renderer.render(value)
    return bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes={"a": ["href", "title"]},
        protocols={"http", "https", "mailto"},
        strip=True,
    )


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    parsed = yaml.safe_load(text[4:end]) or {}
    return json_safe(parsed) if isinstance(parsed, dict) else {}, text[end + 5:]


def parse_yaml_document(raw: str) -> tuple[Any, dict[str, Any]]:
    """Parse YAML for presentation without making canonical-source mutations."""
    try:
        parsed = json_safe(yaml.safe_load(raw))
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        return None, {
            "valid": False,
            "error": str(error),
            "line": mark.line + 1 if mark else None,
            "column": mark.column + 1 if mark else None,
            "normalized": None,
        }
    normalized = yaml.safe_dump(
        parsed, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    return parsed, {
        "valid": True,
        "error": None,
        "line": None,
        "column": None,
        "normalized": normalized,
        "normalization_changed": normalized.strip() != raw.strip(),
    }


def parse_numstat(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "files": 0, "insertions": 0, "deletions": 0, "net": 0, "binaries": 0,
        "areas": {}, "paths": [],
    }
    for line in text.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if path.startswith("knowledge/dashboard/"):
            continue
        area = classify_path(path)
        bucket = result["areas"].setdefault(
            area, {"files": 0, "insertions": 0, "deletions": 0, "binaries": 0}
        )
        result["files"] += 1
        bucket["files"] += 1
        result["paths"].append(path)
        if added == "-" or deleted == "-":
            result["binaries"] += 1
            bucket["binaries"] += 1
            continue
        plus, minus = int(added), int(deleted)
        result["insertions"] += plus
        result["deletions"] += minus
        bucket["insertions"] += plus
        bucket["deletions"] += minus
    result["net"] = result["insertions"] - result["deletions"]
    return result


def classify_path(path: str) -> str:
    if path.startswith("knowledge/"):
        return "knowledge"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("template/.clineflow/") or path.startswith(".clineflow/"):
        return "clineflow_runtime"
    if path.startswith("docs/") or path.lower().endswith(".md"):
        return "documentation"
    return "source"


def tree_footprint(root: Path, revision: str | None = None) -> dict[str, int]:
    if revision:
        listing = run_git(root, "ls-tree", "-r", "-l", revision)
        tracked_files = tracked_bytes = knowledge_files = knowledge_bytes = 0
        for line in listing.splitlines():
            match = re.match(r"\d+\s+\w+\s+[0-9a-f]+\s+(\d+|-)\t(.+)$", line)
            if not match or match.group(1) == "-":
                continue
            size, path = int(match.group(1)), match.group(2)
            if path.startswith("knowledge/dashboard/"):
                continue
            tracked_files += 1
            tracked_bytes += size
            if path.startswith("knowledge/"):
                knowledge_files += 1
                knowledge_bytes += size
        return {
            "tracked_files": tracked_files, "tracked_bytes": tracked_bytes,
            "knowledge_files": knowledge_files, "knowledge_bytes": knowledge_bytes,
        }

    files = [line for line in run_git(root, "ls-files").splitlines() if line]
    tracked_files = tracked_bytes = knowledge_files = knowledge_bytes = 0
    for relative in files:
        if relative.startswith("knowledge/dashboard/"):
            continue
        path = root / relative
        if not path.is_file():
            continue
        size = path.stat().st_size
        tracked_files += 1
        tracked_bytes += size
        if relative.startswith("knowledge/"):
            knowledge_files += 1
            knowledge_bytes += size
    for path in canonical_sources(root):
        relative = path.relative_to(root).as_posix()
        if relative not in files:
            knowledge_files += 1
            knowledge_bytes += path.stat().st_size
    return {
        "tracked_files": tracked_files, "tracked_bytes": tracked_bytes,
        "knowledge_files": knowledge_files, "knowledge_bytes": knowledge_bytes,
    }


def collect_commits(root: Path, limit: int = 60) -> list[dict[str, Any]]:
    hashes = run_git(root, "log", f"-{limit}", "--format=%H").splitlines()
    commits: list[dict[str, Any]] = []
    for revision in reversed(hashes):
        fields = run_git(root, "show", "-s", "--format=%H%x1f%aI%x1f%cI%x1f%s", revision).strip().split("\x1f")
        if len(fields) != 4:
            continue
        parent = f"{revision}^" if run_git(root, "rev-parse", f"{revision}^").strip() else "--root"
        args = ["diff-tree", "--no-commit-id", "--numstat", "-r"]
        if parent == "--root":
            args.append("--root")
        args.append(revision)
        commits.append({
            "revision": fields[0], "short_revision": fields[0][:8],
            "authored_at": fields[1], "committed_at": fields[2], "summary": fields[3],
            "change": parse_numstat(run_git(root, *args)),
            "footprint": tree_footprint(root, revision),
        })
    return commits


def collect_knowledge(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    renderer = markdown_renderer()
    ledgers: dict[str, Any] = {}
    documents: list[dict[str, Any]] = []
    for source in canonical_sources(root):
        relative = source.relative_to(root).as_posix()
        raw = source.read_text(encoding="utf-8", errors="replace")
        digest = sha256_bytes(raw.encode())
        structured = None
        yaml_status = None
        kind = "source"
        if source.suffix.lower() in {".yml", ".yaml"}:
            structured, yaml_status = parse_yaml_document(raw)
            kind = "ledger" if source.parent == root / "knowledge" and source.name in LEDGERS else "yaml"
        if source.parent == root / "knowledge" and source.name in LEDGERS:
            ledgers[source.stem] = structured if isinstance(structured, dict) else {"_parse_error": yaml_status}
        metadata, body = parse_frontmatter(raw)
        if metadata.get("type") == "Engineering Journal":
            kind = "journal"
        elif source.name == "index.md":
            kind = "index"
        heading = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
        ledger_title = source.stem.removeprefix("clineflow_").replace("_", " ").title() if kind == "ledger" else None
        documents.append({
            "id": digest[:16], "path": relative,
            "title": ledger_title or metadata.get("title") or (heading.group(1) if heading else source.name),
            "description": metadata.get("description", ""), "tags": metadata.get("tags", []),
            "status": metadata.get("status", ""), "generated_at": (metadata.get("generated") or {}).get("at"),
            "kind": kind, "structured": structured, "yaml": yaml_status,
            "hash": digest, "raw": raw, "html": safe_markdown(renderer, body),
        })
    return ledgers, documents


def associate_events(events: list[dict[str, Any]], commits: list[dict[str, Any]]) -> None:
    for event in events:
        revision = event.get("git_revision")
        if revision:
            event["association"] = {"kind": "exact", "revision": str(revision)}
            continue
        try:
            event_time = dt.datetime.fromisoformat(str(event.get("at", "")).replace("Z", "+00:00"))
        except ValueError:
            event["association"] = {"kind": "none"}
            continue
        refs = {str(ref).removeprefix("../") for ref in event.get("refs", [])}
        candidates: list[tuple[float, dict[str, Any], list[str]]] = []
        for commit in commits:
            try:
                commit_time = dt.datetime.fromisoformat(commit["committed_at"])
            except ValueError:
                continue
            delta = abs((commit_time - event_time).total_seconds())
            matching = sorted(refs.intersection(commit["change"]["paths"]))
            if delta <= 48 * 3600 and matching:
                candidates.append((delta, commit, matching))
        if candidates:
            delta, commit, matching = min(candidates, key=lambda item: item[0])
            event["association"] = {
                "kind": "inferred", "revision": commit["revision"], "short_revision": commit["short_revision"],
                "matching_refs": matching, "distance_seconds": int(delta),
            }
        else:
            event["association"] = {"kind": "none"}


def current_change(root: Path) -> dict[str, Any]:
    change = parse_numstat(run_git(root, "diff", "HEAD", "--numstat"))
    tracked = set(run_git(root, "ls-files").splitlines())
    for source in canonical_sources(root):
        relative = source.relative_to(root).as_posix()
        if relative in tracked:
            continue
        lines = source.read_bytes().count(b"\n")
        change["files"] += 1
        change["insertions"] += lines
        change["net"] += lines
        change["paths"].append(relative)
        bucket = change["areas"].setdefault("knowledge", {"files": 0, "insertions": 0, "deletions": 0, "binaries": 0})
        bucket["files"] += 1
        bucket["insertions"] += lines
    return change


def collect_runs(root: Path) -> list[dict[str, Any]]:
    """Collect prior report timestamps without recursively reading report content."""
    runs = root / "knowledge" / "dashboard" / "runs"
    result: list[dict[str, Any]] = []
    if not runs.is_dir():
        return result
    for manifest_path in sorted(runs.glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        generated_at = manifest.get("generated_at")
        if isinstance(generated_at, str):
            result.append({"run_id": manifest_path.parent.name, "generated_at": generated_at})
    return result


def exact_usage(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose usage only when an event contains explicit numeric provider values."""
    records: list[dict[str, Any]] = []
    for event in events:
        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue
        numeric = {
            key: value for key, value in usage.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        if numeric and isinstance(usage.get("provider"), str):
            records.append({"at": event.get("at"), "provider": usage["provider"], "values": numeric})
    return records


def previous_snapshot(root: Path, source_hash: str) -> tuple[str | None, dict[str, Any] | None]:
    runs = root / "knowledge" / "dashboard" / "runs"
    if not runs.is_dir():
        return None, None
    for snapshot in sorted(runs.glob("*/snapshot.json"), reverse=True):
        try:
            data = json.loads(snapshot.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("source_hash") != source_hash:
            return snapshot.parent.name, data
    return None, None


def git_snapshot(root: Path, revision: str) -> dict[str, Any] | None:
    resolved = run_git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").strip()
    if not resolved:
        return None
    paths = run_git(root, "ls-tree", "-r", "--name-only", resolved, "knowledge").splitlines()
    documents = []
    for relative in paths:
        if relative.startswith("knowledge/dashboard/") or Path(relative).suffix.lower() not in SOURCE_SUFFIXES:
            continue
        payload = subprocess.run(
            ["git", "-C", str(root), "show", f"{resolved}:{relative}"], capture_output=True, check=False
        ).stdout
        documents.append({"path": relative, "hash": sha256_bytes(payload)})
    return {"run_id": f"git:{resolved[:8]}", "documents": documents}


def select_baseline(root: Path, source_hash: str, selector: str) -> tuple[str | None, dict[str, Any] | None]:
    if selector == "none":
        return None, None
    if selector in {"previous", "run:previous"}:
        run_id, snapshot = previous_snapshot(root, source_hash)
        if snapshot:
            return run_id, snapshot
        snapshot = git_snapshot(root, "HEAD")
        return (snapshot or {}).get("run_id"), snapshot
    if selector == "head":
        snapshot = git_snapshot(root, "HEAD")
        return (snapshot or {}).get("run_id"), snapshot
    if selector.startswith("git:"):
        snapshot = git_snapshot(root, selector[4:])
        if not snapshot:
            raise ValueError(f"comparison revision does not resolve: {selector[4:]}")
        return snapshot["run_id"], snapshot
    if selector.startswith("run:"):
        run_id = selector[4:]
        path = root / "knowledge" / "dashboard" / "runs" / run_id / "snapshot.json"
        if not path.is_file():
            raise ValueError(f"comparison run does not exist: {run_id}")
        return run_id, json.loads(path.read_text())
    raise ValueError(f"unsupported comparison selector: {selector}")


def calculate_drift(current: list[dict[str, Any]], prior: dict[str, Any] | None) -> dict[str, Any]:
    if not prior:
        return {"baseline": None, "added": [item["path"] for item in current], "removed": [], "changed": []}
    old = {item["path"]: item["hash"] for item in prior.get("documents", [])}
    new = {item["path"]: item["hash"] for item in current}
    return {
        "baseline": prior.get("run_id"),
        "added": sorted(set(new) - set(old)), "removed": sorted(set(old) - set(new)),
        "changed": sorted(path for path in set(new).intersection(old) if new[path] != old[path]),
    }


def validate_insights(path: Path | None, document_ids: set[str]) -> dict[str, Any] | None:
    if not path:
        return None
    return validate_insights_data(json.loads(path.read_text()), document_ids)


def validate_insights_data(data: Any, document_ids: set[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("insights must be a JSON object")
    allowed = {"executive_summary", "project_phases", "notable_changes", "risks", "questions"}
    if set(data) - allowed:
        raise ValueError("insights contain unsupported fields")
    for key in ("project_phases", "notable_changes", "risks", "questions"):
        for item in data.get(key, []):
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                raise ValueError(f"{key} items require text")
            refs = item.get("source_ids", [])
            if not isinstance(refs, list) or not set(refs).issubset(document_ids):
                raise ValueError(f"{key} contains an unknown source id")
    return data


def derive_observations(snapshot: dict[str, Any], insights_path: Path | None = None) -> dict[str, Any]:
    """Create a source-linked narrative model as a replaceable pipeline stage."""
    ledgers = snapshot.get("ledgers", {})
    goals = ledgers.get("clineflow_goals") or {}
    specification = ledgers.get("clineflow_specification") or {}
    verification = ledgers.get("clineflow_verification") or {}
    session = ledgers.get("clineflow_last_session") or {}
    events = snapshot.get("events", [])
    documents = snapshot.get("documents", [])
    document_ids = {item["id"] for item in documents}
    path_ids = {item["path"]: item["id"] for item in documents}
    source_ids = [path_ids[path] for path in (
        "knowledge/clineflow_goals.yml", "knowledge/clineflow_last_session.yml",
        "knowledge/clineflow_verification.yml", "knowledge/clineflow_specification.yml",
    ) if path in path_ids]
    latest_event = max(events, key=lambda item: str(item.get("at", "")), default={})
    active_goal = next(iter(goals.get("active_goals") or []), None)
    next_move = session.get("next_recommended_step") or active_goal or "Review the latest durable context."
    latest_change = session.get("latest_change") or latest_event.get("summary") or "Durable context is ready to explore."
    open_questions = list(specification.get("open_questions") or [])
    open_verification = list(verification.get("open_verification") or [])
    drift = snapshot.get("drift") or {}
    changed_count = sum(len(drift.get(key) or []) for key in ("added", "changed", "removed"))
    observations: dict[str, Any] = {
        "schema": OBSERVATION_SCHEMA,
        "generated_at": snapshot["run_at"],
        "generator": {"kind": "deterministic", "name": "clineflow-dashboard-observer", "version": "1"},
        "source": {"snapshot_schema": snapshot["schema"], "source_hash": snapshot["source_hash"]},
        "executive_summary": latest_change,
        "audiences": {
            "executive": {
                "headline": active_goal or "Knowledge state is captured and ready for review.",
                "why_it_matters": f"{changed_count} canonical sources changed since the selected baseline.",
                "next_move": next_move,
            },
            "manager": {
                "headline": latest_event.get("summary") or latest_change,
                "why_it_matters": f"{len(open_questions) + len(open_verification)} unresolved questions or verification items remain visible.",
                "next_move": next_move,
            },
            "engineer": {
                "headline": f"{len(documents)} canonical sources and {len(events)} timeline events are inspectable.",
                "why_it_matters": "Every observation can be traced back to normalized facts and canonical source documents.",
                "next_move": next_move,
            },
        },
        "project_phases": [],
        "notable_changes": ([{"text": latest_change, "source_ids": source_ids}] if latest_change else []),
        "risks": [{"text": str(item), "source_ids": source_ids} for item in open_verification],
        "questions": [{"text": str(item), "source_ids": source_ids} for item in open_questions],
    }
    supplied = validate_insights(insights_path, document_ids)
    if supplied:
        for key, value in supplied.items():
            observations[key] = value
        observations["generator"] = {"kind": "provided", "name": "invoking-agent", "version": "1"}
    return observations


def validate_observations(path: Path, snapshot: dict[str, Any]) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get("schema") != OBSERVATION_SCHEMA:
        raise ValueError(f"observations must use {OBSERVATION_SCHEMA}")
    if data.get("source", {}).get("source_hash") != snapshot.get("source_hash"):
        raise ValueError("observations do not match the facts source hash")
    audiences = data.get("audiences")
    required_audiences = {"executive", "manager", "engineer"}
    required_story_fields = {"headline", "why_it_matters", "next_move"}
    if not isinstance(audiences, dict) or set(audiences) != required_audiences:
        raise ValueError("observations require executive, manager, and engineer narratives")
    for audience, story in audiences.items():
        if not isinstance(story, dict) or not required_story_fields.issubset(story) or any(
            not isinstance(story[field], str) for field in required_story_fields
        ):
            raise ValueError(f"{audience} narrative requires text headline, why_it_matters, and next_move")
    validate_insights_payload = {key: data.get(key) for key in (
        "executive_summary", "project_phases", "notable_changes", "risks", "questions"
    ) if key in data}
    validate_insights_data(validate_insights_payload, {item["id"] for item in snapshot["documents"]})
    return data


def collect(root: Path, compare: str = "previous") -> dict[str, Any]:
    ledgers, documents = collect_knowledge(root)
    commits = collect_commits(root)
    events = list((ledgers.get("clineflow_timeline") or {}).get("events", []))
    associate_events(events, commits)
    source_hash = sha256_bytes("".join(item["hash"] for item in documents).encode())
    baseline_id, baseline = select_baseline(root, source_hash, compare)
    run_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA, "run_at": run_at, "run_id": run_at.replace("-", "").replace(":", ""),
        "source_hash": source_hash, "git": {
            "head": run_git(root, "rev-parse", "HEAD").strip() or None,
            "branch": run_git(root, "branch", "--show-current").strip() or None,
            "dirty": bool(run_git(root, "status", "--porcelain", "--untracked-files=all").strip()),
        },
        "ledgers": ledgers, "documents": documents, "events": events, "commits": commits,
        "runs": collect_runs(root), "usage": exact_usage(events),
        "current_change": current_change(root), "current_footprint": tree_footprint(root),
        "drift": calculate_drift(documents, baseline), "baseline_run": baseline_id,
    }


def load_assets(runtime: Path) -> tuple[dict[str, str], list[dict[str, Any]]]:
    asset_dir = runtime / "assets"
    manifest_path = runtime / "asset-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    values: dict[str, str] = {}
    for asset in manifest["assets"]:
        path = asset_dir / asset["name"]
        payload = path.read_bytes()
        if sha256_bytes(payload) != asset["sha256"]:
            raise RuntimeError(f"cached asset failed verification: {asset['name']}")
        if asset["kind"] == "font":
            values[asset["name"]] = base64.b64encode(payload).decode()
        else:
            values[asset["name"]] = payload.decode("utf-8")
    return values, manifest["assets"]


def safe_json_for_script(data: Any) -> str:
    return json.dumps(json_safe(data), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build_page(runtime: Path, data: dict[str, Any], observations: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    assets, asset_manifest = load_assets(runtime)
    source_dir = Path(__file__).resolve().parent
    custom_css = (source_dir / "visor.css").read_text()
    custom_js = (source_dir / "visor.js").read_text()
    font_css = f"""
@font-face{{font-family:'Space Grotesk';src:url(data:font/woff2;base64,{assets['space-grotesk.woff2']}) format('woff2');font-weight:400 700;font-display:swap}}
@font-face{{font-family:'IBM Plex Mono';src:url(data:font/woff2;base64,{assets['ibm-plex-mono-400.woff2']}) format('woff2');font-weight:400;font-display:swap}}
@font-face{{font-family:'IBM Plex Mono';src:url(data:font/woff2;base64,{assets['ibm-plex-mono-500.woff2']}) format('woff2');font-weight:500;font-display:swap}}
"""
    csp = "default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'"
    page = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"{csp}\"><title>ClineFlow Knowledge Visor</title><style>{font_css}{custom_css}</style></head><body><a class=\"skip\" href=\"#main\">Skip to knowledge</a><div id=\"app\"></div><script>{assets['echarts.min.js']}</script><script>{assets['cytoscape.min.js']}</script><script>{assets['gsap.min.js']}</script><script id=\"clineflow-data\" type=\"application/json\">{safe_json_for_script(data)}</script><script id=\"clineflow-observations\" type=\"application/json\">{safe_json_for_script(observations)}</script><script>{custom_js}</script></body></html>"""
    return page, asset_manifest


def render_report(root: Path, runtime: Path, data: dict[str, Any], observations: dict[str, Any], no_open: bool) -> Path:
    runs_dir = root / "knowledge" / "dashboard" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = data["run_id"]
    run_dir = runs_dir / run_id
    counter = 2
    while run_dir.exists():
        run_dir = run_dir.with_name(f"{run_id}-{counter}")
        counter += 1
    temporary = runs_dir / f".{run_dir.name}.tmp-{os.getpid()}"
    temporary.mkdir()
    data["run_id"] = run_dir.name
    page, asset_manifest = build_page(runtime, data, observations)
    report_manifest = {
        "schema": SCHEMA,
        "generator_version": next((line.split("=", 1)[1] for line in (runtime / ".active").read_text().splitlines() if line.startswith("component_version=")), "unknown"),
        "run_id": data["run_id"], "generated_at": data["run_at"],
        "source_hash": data["source_hash"], "baseline_run": data.get("baseline_run"),
        "git": data["git"], "assets": asset_manifest,
        "observations": {"schema": observations["schema"], "generator": observations["generator"]},
        "browser_network": "disabled", "warnings": [],
    }
    (temporary / "index.html").write_text(page)
    (temporary / "manifest.json").write_text(json.dumps(report_manifest, indent=2, ensure_ascii=False) + "\n")
    (temporary / "snapshot.json").write_text(json.dumps(json_safe(data), indent=2, ensure_ascii=False) + "\n")
    (temporary / "observations.json").write_text(json.dumps(json_safe(observations), indent=2, ensure_ascii=False) + "\n")
    for path in temporary.iterdir():
        try:
            path.chmod(0o600)
        except OSError:
            pass
    temporary.rename(run_dir)
    update_launcher(root)
    if not no_open:
        webbrowser.open(run_dir.joinpath("index.html").as_uri())
    return run_dir


def update_launcher(root: Path) -> None:
    dashboard = root / "knowledge" / "dashboard"
    links = []
    for run in sorted(dashboard.glob("runs/*/index.html"), reverse=True):
        run_id = run.parent.name
        links.append(f'<li><a href="runs/{html.escape(run_id)}/index.html">{html.escape(run_id)}</a></li>')
    launcher = "<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'unsafe-inline'; connect-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'\"><title>ClineFlow dashboard runs</title><style>body{font:16px system-ui;background:#07100f;color:#ecfff9;padding:3rem}a{color:#65fbd2}li{margin:.7rem}</style><h1>ClineFlow dashboard runs</h1><ol>" + "".join(links) + "</ol>"
    dashboard.joinpath("index.html").write_text(launcher)


def sanitized_export(root: Path, runtime: Path, run: str, output: Path) -> None:
    runs = root / "knowledge" / "dashboard" / "runs"
    if run == "latest":
        choices = sorted(path for path in runs.iterdir() if path.is_dir()) if runs.is_dir() else []
        if not choices:
            raise RuntimeError("no dashboard runs exist")
        source = choices[-1]
    else:
        source = runs / run
    snapshot = json.loads(source.joinpath("snapshot.json").read_text())
    source_observations = source / "observations.json"
    clean_ledgers = {name: {key: value for key, value in ledger.items() if not key.endswith("_refs")} for name, ledger in snapshot["ledgers"].items()}
    sanitized = {
        "schema": SCHEMA, "run_at": snapshot["run_at"], "source_hash": "redacted",
        "run_id": "sanitized-export", "git": {"head": None, "branch": None, "dirty": False},
        "ledgers": clean_ledgers,
        "documents": [{**{key: item.get(key) for key in ("id", "title", "description", "tags", "status", "generated_at")}, "path": f"source-{index + 1}", "hash": "redacted", "raw": f"{item.get('title', '')} {item.get('description', '')}", "html": f"<h1>{html.escape(str(item.get('title', 'Knowledge concept')))}</h1><p>{html.escape(str(item.get('description', 'Full content excluded from sanitized export.')))}</p>"} for index, item in enumerate(snapshot["documents"])],
        "events": [{key: event.get(key) for key in ("at", "type", "summary")} for event in snapshot["events"]],
        "commits": [{key: commit.get(key) for key in ("authored_at", "committed_at", "summary", "change", "footprint")} for commit in snapshot["commits"]],
        "runs": [{"run_id": "redacted", "generated_at": item.get("generated_at")} for item in snapshot.get("runs", [])],
        "usage": [],
        "current_change": {key: value for key, value in snapshot["current_change"].items() if key != "paths"}, "current_footprint": snapshot["current_footprint"],
        "drift": snapshot["drift"], "sanitized": True,
    }
    observations = json.loads(source_observations.read_text()) if source_observations.is_file() else derive_observations(sanitized)
    observations["source"] = {"snapshot_schema": sanitized["schema"], "source_hash": sanitized.get("source_hash")}
    output.mkdir(parents=True, exist_ok=False)
    page, asset_manifest = build_page(runtime, sanitized, observations)
    output.joinpath("data.json").write_text(json.dumps(sanitized, indent=2, ensure_ascii=False) + "\n")
    output.joinpath("observations.json").write_text(json.dumps(observations, indent=2, ensure_ascii=False) + "\n")
    output.joinpath("index.html").write_text(page)
    output.joinpath("manifest.json").write_text(json.dumps({"schema": SCHEMA, "sanitized": True, "assets": asset_manifest, "browser_network": "disabled"}, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(prog="dashboard-engine")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime", type=Path, required=True)
    sub = parser.add_subparsers(dest="command")
    generate = sub.add_parser("generate")
    generate.add_argument("--insights", type=Path)
    generate.add_argument("--compare", default="previous")
    generate.add_argument("--no-open", action="store_true")
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--output", type=Path, required=True)
    collect_parser.add_argument("--compare", default="previous")
    observe = sub.add_parser("observe")
    observe.add_argument("--facts", type=Path, required=True)
    observe.add_argument("--output", type=Path, required=True)
    observe.add_argument("--insights", type=Path)
    render = sub.add_parser("render")
    render.add_argument("--facts", type=Path, required=True)
    render.add_argument("--insights", type=Path)
    render.add_argument("--observations", type=Path)
    render.add_argument("--no-open", action="store_true")
    export = sub.add_parser("export")
    export.add_argument("--run", default="latest")
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    command = args.command or "generate"
    if command == "collect":
        args.output.write_text(json.dumps(collect(root, compare=args.compare), indent=2, ensure_ascii=False) + "\n")
        return 0
    if command == "observe":
        snapshot = json.loads(args.facts.read_text())
        args.output.write_text(json.dumps(derive_observations(snapshot, args.insights), indent=2, ensure_ascii=False) + "\n")
        return 0
    if command == "render":
        data = json.loads(args.facts.read_text())
        observations = validate_observations(args.observations, data) if args.observations else derive_observations(data, args.insights)
        print(render_report(root, args.runtime, data, observations, args.no_open) / "index.html")
        return 0
    if command == "export":
        sanitized_export(root, args.runtime, args.run, args.output)
        print(args.output / "index.html")
        return 0
    data = collect(root, args.compare)
    observations = derive_observations(data, args.insights)
    print(render_report(root, args.runtime, data, observations, args.no_open) / "index.html")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
