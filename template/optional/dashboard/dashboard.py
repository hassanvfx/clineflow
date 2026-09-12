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
import shutil
import subprocess
import sys
import unicodedata
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
PRESENTATION_SCHEMA = "clineflow-dashboard-presentation/v1"
DELIVERY_ESTIMATE_SCHEMA = "clineflow-dashboard-delivery-estimate/v1"
AGENT_INSIGHTS_SCHEMA = "clineflow-dashboard-agent-insights/v1"
AGENT_CONTRACT_SCHEMA = "clineflow-dashboard-agent-observation-contract/v1"
DIAGNOSTIC_SCHEMA = "clineflow-dashboard-diagnostic/v1"
AGENT_INSIGHT_FIELDS = ("executive_summary", "delivery_estimate")
# The sole global control for deterministic post-composition quality review.
# A pass checks a fixed artifact candidate; it never asks a model to rewrite it.
MAX_ARTIFACT_JUDGE_PASSES = 5
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
    additive = (knowledge / "updates").is_dir()
    return sorted(
        path for path in knowledge.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SOURCE_SUFFIXES
        and "dashboard" not in path.relative_to(knowledge).parts
        and not (additive and (
            path.name in LEDGERS
            or path == knowledge / "log.md"
            or path == knowledge / "journals" / "index.md"
            or "topics" in path.relative_to(knowledge).parts
        ))
    )


def markdown_renderer() -> MarkdownIt:
    return MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False}).enable("table").enable("strikethrough")


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
    try:
        parsed = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        # A read-only dashboard must not fail because one optional Markdown
        # source has malformed frontmatter. Retain its full body as a source.
        return {}, text
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
    # Add the generated ledger projections deliberately.  Additive OKF projects
    # exclude them from canonical_sources() because immutable updates are the
    # source of record, but a report needs the current projected context as a
    # read-only input.  Their inclusion is presentation-only and never writes a
    # canonical source.
    ledger_paths = [root / "knowledge" / name for name in LEDGERS]
    sources = [path for path in ledger_paths if path.is_file()]
    sources.extend(path for path in canonical_sources(root) if path not in sources)
    for source in sorted(sources):
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
            "author": metadata.get("author", {}), "clineflow": metadata.get("clineflow", {}),
            "kind": kind, "structured": structured, "yaml": yaml_status,
            "hash": digest, "raw": raw, "html": safe_markdown(renderer, body),
        })
    return ledgers, documents


def journal_workstream(document: dict[str, Any]) -> str:
    """Group a journal by explicit topic, then by a safe source tag."""
    topic = (document.get("clineflow") or {}).get("topic")
    if isinstance(topic, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", topic):
        return topic
    tags = document.get("tags") or []
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", tag) and tag not in {"engineering", "journal", "reference"}:
                return tag
    return "unclassified"


def dated_values(data: list[dict[str, Any]], key: str) -> list[str]:
    """Return parseable ISO-like timestamps without claiming missing coverage."""
    values: list[str] = []
    for item in data:
        value = item.get(key)
        if not isinstance(value, str):
            continue
        try:
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        values.append(value)
    return sorted(values)


def report_identity(data: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    """Build explicit report identity from captured facts, never UI selection.

    Fixture facts may carry this model already.  The function intentionally does
    not call Git: rendering a fixture must not acquire its host's Git identity.
    """
    supplied = data.get("report_identity")
    if isinstance(supplied, dict):
        return supplied
    git = data.get("git") if isinstance(data.get("git"), dict) else {}
    commits = data.get("commits") if isinstance(data.get("commits"), list) else []
    dated_events = dated_values(data.get("events") or [], "at")
    dated_journals = dated_values(data.get("documents") or [], "generated_at")
    range_values = sorted(dated_events + dated_journals)
    latest_commit = commits[-1] if commits else None
    head = git.get("head") if isinstance(git.get("head"), str) else None
    dirty = git.get("dirty")
    condition = (
        {"state": "working-tree-modified", "label": "Working tree modified", "detail": "Captured local repository state includes uncommitted changes."}
        if dirty is True else
        {"state": "clean", "label": "Working tree clean", "detail": "No changes were recorded by Git at capture."}
        if dirty is False and head else
        {"state": "unknown", "label": "Snapshot condition not captured", "detail": "The source did not provide a Git working-tree condition."}
    )
    project_title = root.name if root else "Project record"
    return {
        "project": {"title": project_title, "description": None, "source_kind": "local-repository"},
        "capture": {"captured_at": data.get("run_at"), "source_origin": "local repository", "kind": "repository"},
        "coverage": {
            "from": range_values[0] if range_values else None,
            "to": range_values[-1] if range_values else None,
            "included": ["project knowledge", "journal records", "timeline events", "captured Git history"],
            "limit": "Coverage reflects included dated records; it does not claim uninterrupted project history.",
        },
        "revision": {"value": head, "short": head[:8] if head else None, "label": "Captured Git HEAD", "kind": "head" if head else "unavailable"},
        "latest_commit": ({
            "value": latest_commit.get("revision"), "short": latest_commit.get("short_revision"),
            "summary": latest_commit.get("summary"), "committed_at": latest_commit.get("committed_at"),
            "label": "Latest captured commit", "kind": "commit",
        } if isinstance(latest_commit, dict) else {
            "value": None, "short": None, "summary": None, "committed_at": None,
            "label": "Latest captured commit unavailable", "kind": "unavailable",
        }),
        "condition": condition,
    }


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
    """Collect completed report references in generated-time order."""
    runs = root / "knowledge" / "dashboard" / "runs"
    result: list[dict[str, Any]] = []
    if not runs.is_dir():
        return result
    for manifest_path in runs.glob("*/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        generated_at = manifest.get("generated_at")
        if manifest.get("schema") == SCHEMA and manifest.get("run_id") == manifest_path.parent.name and isinstance(generated_at, str):
            result.append({"run_id": manifest_path.parent.name, "generated_at": generated_at})
    return sorted(result, key=lambda item: (str(item["generated_at"]), str(item["run_id"])))


def report_selector(root: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return same-project report routes for the offline header selector."""
    current_identity = data.get("report_identity") or report_identity(data, root)
    current_id = str(data.get("run_id") or "")
    entries = [{
        "run_id": current_id,
        "generated_at": data.get("report_generated_at") or data.get("run_at"),
        "href": "index.html",
        "current": True,
    }]
    for candidate in collect_runs(root):
        if candidate["run_id"] == current_id:
            continue
        try:
            snapshot = json.loads((root / "knowledge" / "dashboard" / "runs" / candidate["run_id"] / "snapshot.json").read_text())
        except (OSError, json.JSONDecodeError):
            continue
        prior_identity = snapshot.get("report_identity") or {}
        if {
            "title": (prior_identity.get("project") or {}).get("title"),
            "source_kind": (prior_identity.get("project") or {}).get("source_kind"),
        } != {
            "title": (current_identity.get("project") or {}).get("title"),
            "source_kind": (current_identity.get("project") or {}).get("source_kind"),
        }:
            continue
        entries.append({
            "run_id": candidate["run_id"], "generated_at": candidate["generated_at"],
            "href": f"../{candidate['run_id']}/index.html", "current": False,
        })
    return sorted(entries, key=lambda item: (str(item.get("generated_at") or ""), str(item.get("run_id") or "")), reverse=True)


def report_event_key(event: dict[str, Any]) -> str:
    """Compare only normalized chronology fields, never opaque event metadata."""
    value = {key: event.get(key) for key in ("at", "type", "title", "summary", "refs")}
    return sha256_bytes(json.dumps(json_safe(value), sort_keys=True, separators=(",", ":")).encode())


def report_unresolved_count(snapshot: dict[str, Any]) -> int:
    ledgers = snapshot.get("ledgers") or {}
    specification = ledgers.get("clineflow_specification") or {}
    verification = ledgers.get("clineflow_verification") or {}
    session = ledgers.get("clineflow_last_session") or {}
    return (
        len(specification.get("open_questions") or [])
        + len(verification.get("open_verification") or [])
        + sum(1 for ledger in (specification, verification, session) for item in ledger.get("items") or [] if isinstance(item, dict) and item.get("unresolved"))
    )


def collect_previous_report(root: Path, project: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Read the direct chronological predecessor's frozen JSON, if one exists."""
    for candidate in reversed(collect_runs(root)):
        try:
            run_dir = root / "knowledge" / "dashboard" / "runs" / str(candidate["run_id"])
            snapshot = json.loads(run_dir.joinpath("snapshot.json").read_text())
            observations = json.loads(run_dir.joinpath("observations.json").read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if snapshot.get("schema") != SCHEMA or observations.get("schema") != OBSERVATION_SCHEMA:
            continue
        prior_project = (snapshot.get("report_identity") or {}).get("project") or {}
        if project and {
            "title": prior_project.get("title"), "source_kind": prior_project.get("source_kind"),
        } != {
            "title": project.get("title"), "source_kind": project.get("source_kind"),
        }:
            continue
        documents = [item for item in snapshot.get("documents") or [] if isinstance(item, dict)]
        events = [normalize_event(item) for item in snapshot.get("events") or []]
        sparks = [item for item in observations.get("sparks") or [] if isinstance(item, dict)]
        return {
            "run_id": candidate["run_id"], "generated_at": candidate["generated_at"],
            "source_hash": snapshot.get("source_hash"),
            "document_paths": sorted(str(item.get("path")) for item in documents if item.get("path")),
            "journal_paths": sorted(str(item.get("path")) for item in documents if item.get("kind") == "journal" and item.get("path")),
            "event_keys": sorted(report_event_key(item) for item in events),
            "event_count": len(events), "unresolved_count": report_unresolved_count(snapshot),
            "sparks": sparks,
        }
    return None


def attach_previous_report(root: Path, snapshot: dict[str, Any]) -> None:
    """Attach a compact predecessor summary before deterministic observation."""
    project = (snapshot.get("report_identity") or {}).get("project") or None
    previous = collect_previous_report(root, project)
    snapshot["previous_report"] = previous
    snapshot["previous_spark_run"] = previous.get("run_id") if previous else None
    snapshot["previous_sparks"] = previous.get("sparks", []) if previous else []


def report_history(snapshot: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    """Explain report-to-report change from frozen JSON representations only."""
    documents = [item for item in snapshot.get("documents") or [] if isinstance(item, dict)]
    current_paths = {str(item.get("path")) for item in documents if item.get("path")}
    current_journals = {str(item.get("path")) for item in documents if item.get("kind") == "journal" and item.get("path")}
    current_events = {report_event_key(normalize_event(item)) for item in snapshot.get("events") or []}
    current_unresolved = report_unresolved_count(snapshot)
    current_sparks = [item for item in observations.get("sparks") or [] if isinstance(item, dict)]
    previous = snapshot.get("previous_report")
    if not isinstance(previous, dict):
        return {
            "mode": "baseline", "previous_run": None, "previous_generated_at": None,
            "summary": "Baseline established from this first complete local dashboard report.",
            "cards": [
                {"label": "REPORT LINEAGE", "value": "Baseline", "text": "No earlier complete dashboard JSON is available. The next report will compare against this frozen record."},
                {"label": "SOURCE SET", "value": f"{len(current_paths)} records", "text": f"{len(current_journals)} journals and {len(current_events)} dated timeline events establish the initial chronology."},
                {"label": "LEARNING SET", "value": f"{len(current_sparks)} Sparks", "text": "These source-bound notes are the initial comparison set; a repeat report does not add evidence by itself."},
            ],
        }
    previous_paths = set(previous.get("document_paths") or [])
    previous_journals = set(previous.get("journal_paths") or [])
    previous_events = set(previous.get("event_keys") or [])
    added_sources, removed_sources = current_paths - previous_paths, previous_paths - current_paths
    added_events, removed_events = current_events - previous_events, previous_events - current_events
    reconciliation = (observations.get("observations_harness") or {}).get("reconciliation") or {}
    unresolved_delta = current_unresolved - int(previous.get("unresolved_count") or 0)
    unresolved_text = "unchanged" if unresolved_delta == 0 else (f"{abs(unresolved_delta)} more" if unresolved_delta > 0 else f"{abs(unresolved_delta)} fewer")
    return {
        "mode": "comparison", "previous_run": previous.get("run_id"), "previous_generated_at": previous.get("generated_at"),
        "summary": f"Compared with the preceding report {previous.get('run_id')} generated {previous.get('generated_at')}.",
        "cards": [
            {"label": "REPORT LINEAGE", "value": "Chronological comparison", "text": f"This report follows {previous.get('run_id')} in generated time and reads its frozen snapshot and observations JSON."},
            {"label": "RECORD DELTA", "value": f"+{len(added_sources)} / −{len(removed_sources)} sources", "text": f"Journals: {len(current_journals)} now versus {len(previous_journals)} before. Unresolved entries are {unresolved_text}."},
            {"label": "ACTIVITY DELTA", "value": f"+{len(added_events)} / −{len(removed_events)} events", "text": "Event identities compare normalized date, type, title, summary, and explicit references—not file order or inferred effort."},
            {"label": "LEARNING DELTA", "value": f"{reconciliation.get('new', 0)} new · {reconciliation.get('revised', 0)} revised", "text": f"{reconciliation.get('unchanged', 0)} unchanged and {reconciliation.get('retired', 0)} retired source-bound Sparks. Repetition alone adds no support."},
        ],
    }


def dashboard_settings_path(root: Path) -> Path:
    return root / "knowledge" / "dashboard" / "settings.json"


def parse_retention(value: Any) -> int | None:
    """Return a positive report count or None for unlimited retention."""
    if value is None or value == "unlimited":
        return None
    if isinstance(value, bool):
        raise ValueError("retention must be a positive integer or unlimited")
    try:
        retention = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("retention must be a positive integer or unlimited") from error
    if retention < 1:
        raise ValueError("retention must be a positive integer or unlimited")
    return retention


def read_retention(root: Path) -> int | None:
    path = dashboard_settings_path(root)
    if not path.is_file():
        return 3
    try:
        settings = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError("dashboard settings.json must contain valid JSON") from error
    if not isinstance(settings, dict) or set(settings) != {"retention"}:
        raise ValueError("dashboard settings.json must contain only a retention field")
    return parse_retention(settings["retention"])


def write_retention(root: Path, value: Any) -> int | None:
    retention = parse_retention(value)
    path = dashboard_settings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps({"retention": retention}, indent=2) + "\n")
    temporary.replace(path)
    return retention


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


def validate_insights_data(
    data: Any, document_ids: set[str], *, allow_deterministic_summary: bool = False,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("insights must be a JSON object")
    allowed = set(AGENT_INSIGHT_FIELDS)
    if set(data) - allowed:
        raise ValueError(f"insights contain unsupported fields; allowed fields are: {', '.join(AGENT_INSIGHT_FIELDS)}")
    if "executive_summary" in data:
        summary = data["executive_summary"]
        if not (allow_deterministic_summary and isinstance(summary, str) and summary.strip()):
            if not isinstance(summary, dict) or set(summary) != {"text", "source_ids"}:
                raise ValueError("executive_summary requires exactly text and source_ids")
            if not isinstance(summary["text"], str) or not summary["text"].strip():
                raise ValueError("executive_summary requires non-empty text")
            source_ids = summary["source_ids"]
            if not isinstance(source_ids, list) or not source_ids or not all(isinstance(item, str) for item in source_ids) or not set(source_ids).issubset(document_ids):
                raise ValueError("executive_summary requires at least one known source_id")
    if "delivery_estimate" in data:
        validate_delivery_estimate(data["delivery_estimate"], document_ids)
    return data


def observation_contract(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Describe the intentionally narrow, cited agent input boundary for one facts bundle."""
    documents = [
        {
            "id": item.get("id"), "title": item.get("title"), "path": item.get("path"),
            "kind": item.get("kind"),
        }
        for item in snapshot.get("documents", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    source_ids = [item["id"] for item in documents]
    example_source = source_ids[0] if source_ids else "<source-id-from-source-register>"
    return {
        "schema": AGENT_CONTRACT_SCHEMA,
        "facts": {
            "schema": snapshot.get("schema"), "source_hash": snapshot.get("source_hash"),
            "source_register": documents,
        },
        "agent_input": {
            "schema": AGENT_INSIGHTS_SCHEMA,
            "allowed_fields": list(AGENT_INSIGHT_FIELDS),
            "rules": [
                "Submit only the fields you can support from the source register.",
                "Every submitted narrative must name one or more source_ids from this exact facts bundle.",
                "Do not submit a complete observations document; the observer deterministically fills that required model.",
                "Do not submit HTML, dashboard layout, PDF content, Spark identities, or calculated delivery totals.",
            ],
            "example": {
                "executive_summary": {
                    "text": "A concise, source-bound summary of the recorded change.",
                    "source_ids": [example_source],
                }
            },
        },
        "deterministic_observer": {
            "output_schema": OBSERVATION_SCHEMA,
            "fills": [
                "audience narratives", "origin, overall, recent, and digest narratives",
                "journal coverage", "relationship unknowns", "project story", "Spark candidates and reconciliation",
            ],
            "guarantee": "The observer binds every required observation to this facts source_hash before rendering.",
        },
        "retry": {
            "diagnostic_schema": DIAGNOSTIC_SCHEMA,
            "policy": "On invalid agent input, emit one JSON diagnostic, correct the named field once, and rerun observe. If it still fails, omit the optional agent input and use the deterministic baseline.",
            "command": "dashboard observe --facts <facts.json> --insights <corrected-insights.json> --output <observations.json> --json-errors",
        },
    }


def finite_number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"delivery estimate {label} must be a number")
    result = float(value)
    if result != result or result in {float("inf"), float("-inf")}:
        raise ValueError(f"delivery estimate {label} must be finite")
    if positive and result <= 0:
        raise ValueError(f"delivery estimate {label} must be positive")
    if not positive and result < 0:
        raise ValueError(f"delivery estimate {label} must not be negative")
    return result


def validate_delivery_estimate(value: Any, document_ids: set[str]) -> dict[str, Any]:
    """Validate explicit agent planning inputs; calculated totals are never accepted."""
    if not isinstance(value, dict):
        raise ValueError("delivery_estimate must be an object")
    expected = {"schema", "agent", "constants", "perspective", "rationale", "source_ids"}
    if set(value) != expected or value.get("schema") != DELIVERY_ESTIMATE_SCHEMA:
        raise ValueError(f"delivery_estimate must use {DELIVERY_ESTIMATE_SCHEMA} with supported fields")
    agent = value.get("agent")
    if not isinstance(agent, dict) or set(agent) != {"name", "model", "configuration_label"} or any(
        not isinstance(agent.get(key), str) or not agent[key].strip() for key in agent
    ):
        raise ValueError("delivery estimate agent requires name, model, and configuration_label")
    constants = value.get("constants")
    if not isinstance(constants, dict) or set(constants) != {
        "currency", "loaded_hourly_rate", "baseline_hours", "current_direct_cost",
        "ai_without_clineflow", "no_ai",
    }:
        raise ValueError("delivery estimate constants are incomplete")
    currency = constants.get("currency")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("delivery estimate currency must be a three-letter uppercase code")
    finite_number(constants.get("loaded_hourly_rate"), "loaded_hourly_rate", positive=True)
    finite_number(constants.get("baseline_hours"), "baseline_hours", positive=True)
    finite_number(constants.get("current_direct_cost"), "current_direct_cost")
    for scenario in ("ai_without_clineflow", "no_ai"):
        item = constants.get(scenario)
        if not isinstance(item, dict) or set(item) != {"effort_multiplier", "direct_cost"}:
            raise ValueError(f"delivery estimate {scenario} requires effort_multiplier and direct_cost")
        finite_number(item.get("effort_multiplier"), f"{scenario}.effort_multiplier", positive=True)
        finite_number(item.get("direct_cost"), f"{scenario}.direct_cost")
    for text_key in ("perspective", "rationale"):
        if not isinstance(value.get(text_key), str) or not value[text_key].strip():
            raise ValueError(f"delivery estimate {text_key} must be non-empty text")
    source_ids = value.get("source_ids")
    if not isinstance(source_ids, list) or not source_ids or not all(isinstance(item, str) for item in source_ids) or not set(source_ids).issubset(document_ids):
        raise ValueError("delivery estimate requires known supporting source_ids")
    return value


def calculate_delivery_estimate(value: dict[str, Any]) -> dict[str, Any]:
    """Turn validated inputs into transparent scenario outputs before browser rendering."""
    constants = value["constants"]
    hourly_rate = finite_number(constants["loaded_hourly_rate"], "loaded_hourly_rate", positive=True)
    baseline_hours = finite_number(constants["baseline_hours"], "baseline_hours", positive=True)
    raw_scenarios = (
        ("current", "Current AI + ClineFlow", 1.0, constants["current_direct_cost"]),
        ("ai_without_clineflow", "AI without ClineFlow", constants["ai_without_clineflow"]["effort_multiplier"], constants["ai_without_clineflow"]["direct_cost"]),
        ("no_ai", "No AI", constants["no_ai"]["effort_multiplier"], constants["no_ai"]["direct_cost"]),
    )
    scenarios: list[dict[str, Any]] = []
    for key, label, multiplier, direct_cost in raw_scenarios:
        hours = baseline_hours * finite_number(multiplier, f"{key}.effort_multiplier", positive=True)
        direct = finite_number(direct_cost, f"{key}.direct_cost")
        scenarios.append({
            "id": key, "label": label, "estimated_hours": round(hours, 2),
            "direct_cost": round(direct, 2), "estimated_cost": round(hours * hourly_rate + direct, 2),
        })
    baseline = scenarios[0]
    for item in scenarios:
        item["delta_hours"] = round(item["estimated_hours"] - baseline["estimated_hours"], 2)
        item["delta_cost"] = round(item["estimated_cost"] - baseline["estimated_cost"], 2)
    return {
        "schema": DELIVERY_ESTIMATE_SCHEMA,
        "disclaimer": "Estimated planning model — not measured labor, productivity, or realized savings.",
        "agent": value["agent"], "currency": constants["currency"], "perspective": value["perspective"],
        "rationale": value["rationale"], "source_ids": value["source_ids"], "scenarios": scenarios,
        "reference_inputs": {
            "loaded_hourly_rate": round(hourly_rate, 2), "baseline_hours": round(baseline_hours, 2),
            "current_direct_cost": round(finite_number(constants["current_direct_cost"], "current_direct_cost"), 2),
            "ai_without_clineflow": constants["ai_without_clineflow"], "no_ai": constants["no_ai"],
        },
    }


def observation_text(value: Any) -> str:
    """Turn a structured ledger statement into a compact human-readable observation."""
    if value is None:
        return "Not recorded"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " · ".join(observation_text(item) for item in value) or "Not recorded"
    if isinstance(value, dict):
        for key in ("text", "summary", "title", "name", "criterion", "requirement", "description", "message", "label", "value"):
            candidate = value.get(key)
            if candidate is not None and not isinstance(candidate, (dict, list)):
                return str(candidate)
        return " · ".join(f"{str(key).replace('_', ' ')}: {observation_text(item)}" for key, item in value.items()) or "Structured record"
    return str(value)


def first_present(value: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        candidate = value.get(key)
        if candidate not in (None, ""):
            return candidate
    return None


def concise_title(value: Any, limit: int = 74) -> str:
    """Create a scannable title when a timeline record has only a long note."""
    text = re.sub(r"\s+", " ", observation_text(value)).strip()
    # Timeline entries are frequently authored as "at: <timestamp> · event: ...".
    # A timestamp is useful metadata, but it is a poor headline.
    text = re.sub(r"^(?:at|on)\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b20\d{2}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z?)?\b", "", text)
    text = re.sub(r"^[\s·—:-]+", "", text)
    text = re.sub(r"\s*\(see\s+[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\d{4}-\d{2}-\d{2}(?:[T ][^\s]+)?\s*(?:[·—:-]\s*)?", "", text).strip()
    text = re.sub(r"^(?:event|summary|change)\s*:\s*", "", text, flags=re.IGNORECASE)
    if not text:
        return "Recorded event"
    natural_breaks = re.split(r"(?<=[.!?])\s+|\s+\(|\s+—\s+|:\s*", text, maxsplit=1)
    candidate = natural_breaks[0].strip() or text
    if len(candidate) <= limit:
        return candidate
    clipped = candidate[:limit + 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{clipped or candidate[:limit]}…"


def permalink_slug(value: Any) -> str:
    """Create a stable, filesystem-safe segment for a local permalink."""
    normalized = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "project"


def blog_topic(presentation: dict[str, Any]) -> dict[str, Any]:
    """Compose a structured release article only from the frozen report model."""
    identity = presentation.get("identity") or {}
    project = identity.get("project") or {}
    workspace = presentation.get("workspace") or {}
    activity = presentation.get("activity") or {}
    evidence = presentation.get("evidence_register") or {}
    now = presentation.get("now") or {}
    documents = presentation.get("documents") or []
    timeline = activity.get("events") or []
    journals = [item for item in documents if item.get("kind") == "journal"]
    source_paths = [str(item.get("path")) for item in documents if item.get("path")]
    latest_change = observation_text(now.get("latest_change") or now.get("headline") or "No current technical change is recorded.")
    event_titles = [concise_title(item.get("title") or item.get("summary")) for item in timeline[:3]]
    journal_routes = [
        f"{item.get('title') or 'Untitled journal'} — {compact_summary(item.get('description') or 'No description recorded.', 160)}"
        for item in journals[:3]
    ]
    verification = evidence.get("verification") or []
    sections = [
        {
            "title": "What I changed",
            "body": f"In this release, I changed the reference approach: {latest_change}",
        },
        {
            "title": "How I worked through it",
            "body": (
                "I kept the work trace in this order: " + "; ".join(event_titles) + "."
                if event_titles else "No dated development events were included in this frozen release."
            ),
        },
        {
            "title": "Where I left the technical trail",
            "body": (
                "I recorded the surrounding decisions here: " + "; ".join(journal_routes) + "."
                if journal_routes else
                f"I left {len(documents)} frozen knowledge records for this release."
            ),
        },
        {
            "title": "How I checked the work",
            "body": (
                f"I can point to {len(verification)} verification record{'s' if len(verification) != 1 else ''}; "
                f"the snapshot shows {now.get('unresolved_count', 0)} open or conflicting record{'s' if now.get('unresolved_count', 0) != 1 else ''}."
            ),
        },
    ]
    return {
        "title": f"I changed: {concise_title(latest_change, 68)}",
        "dek": f"This is my engineering note for {project.get('title') or 'the project'}: {observation_text(now.get('summary') or latest_change)}",
        "technical_topic": concise_title(latest_change, 120),
        "sections": sections,
        "source_paths": source_paths,
        "project_title": project.get("title") or "Project record",
    }


def blog_page(article: dict[str, Any], archive_href: str) -> str:
    """Render a dependency-free permanent article page for a frozen release."""
    sections = "".join(
        f"<section><p class=eyebrow>{index:02d} · TECHNICAL NOTE</p><h2>{html.escape(section['title'])}</h2><p>{html.escape(section['body'])}</p></section>"
        for index, section in enumerate(article.get("sections") or [], 1)
    )
    sources = "".join(f"<li><code>{html.escape(path)}</code></li>" for path in article.get("source_paths") or []) or "<li>No source paths were captured.</li>"
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'\"><title>{html.escape(article['title'])} · Engineering Blog</title><style>
      :root{{--ink:#172033;--muted:#627087;--line:#dbe2ec;--paper:#fbfaf7;--accent:#6849df}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:18px/1.65 ui-sans-serif,system-ui,sans-serif}}main{{width:min(920px,calc(100% - 40px));margin:auto;padding:42px 0 84px}}a{{color:var(--accent);font-weight:700;text-decoration:none}}.eyebrow{{margin:0 0 12px;color:var(--muted);font:600 12px/1.35 ui-monospace,monospace;letter-spacing:.1em}}header{{padding:18px 0 40px;border-bottom:1px solid var(--line)}}h1{{max-width:850px;margin:14px 0;font-size:clamp(2.5rem,7vw,5.5rem);line-height:.95;letter-spacing:-.07em}}.dek{{max-width:720px;color:var(--muted);font-size:1.15rem}}.meta{{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px;color:var(--muted);font:12px ui-monospace,monospace}}section{{padding:34px 0;border-bottom:1px solid var(--line)}}h2{{margin:0 0 10px;font-size:1.5rem;letter-spacing:-.04em}}section p:last-child{{max-width:760px;margin:0}}footer{{padding-top:32px;color:var(--muted);font-size:.88rem}}ul{{padding-left:20px}}code{{overflow-wrap:anywhere}}@media print{{body{{background:#fff}}main{{width:100%;padding:0}}a{{color:inherit}}}}
    </style></head><body><main><a href=\"{html.escape(archive_href)}\">← Engineering notebook</a><header><p class=\"eyebrow\">{html.escape(article['project_title']).upper()} · ENGINEERING NOTEBOOK</p><h1>{html.escape(article['title'])}</h1><p class=\"dek\">{html.escape(article['dek'])}</p><p class=\"meta\"><span>Published {html.escape(article['generated_at'])}</span><span>·</span><span>{html.escape(article['run_id'])}</span><span>·</span><span>Source hash {html.escape(article['source_hash'][:12])}</span></p><p class=\"meta\"><a href=\"article.json\">Agent-readable article.json</a><span>·</span><a href=\"../../index.json\">Archive index.json</a></p></header>{sections}<footer><p class=\"eyebrow\">MY SOURCE TRAIL</p><ul>{sources}</ul><p>This first-person note is deterministically assembled from the frozen project record. The linked JSON retains the structured input for agents.</p></footer></main></body></html>"""


def blog_index_page(project_title: str, articles: list[dict[str, Any]]) -> str:
    latest = articles[0] if articles else {}
    history = "".join(
        f"""<article class=\"entry\"><p class=\"entry-date\">{html.escape(print_timestamp(item.get('generated_at')))}</p><div class=\"entry-body\"><p class=\"eyebrow\">RELEASE NOTE · {html.escape(item.get('run_id') or 'Frozen record')}</p><h2><a href=\"{html.escape(item['url'])}\">{html.escape(item['title'])}</a></h2><p>{html.escape(item.get('dek', 'Source-bound engineering release note.'))}</p><dl><div><dt>Technical topic</dt><dd>{html.escape(item.get('technical_topic', 'Technical record'))}</dd></div><div><dt>Source identity</dt><dd><code>{html.escape(str(item.get('source_hash') or 'Not recorded')[:12])}</code></dd></div></dl></div><div class=\"entry-actions\"><a href=\"{html.escape(item['url'])}\">Read note →</a><a href=\"{html.escape(item.get('json_url', item['url'].replace('index.html', 'article.json')))}\">Article JSON</a></div></article>"""
        for item in articles
    ) or "<p class=\"empty\">No changed frozen source bundle has been published yet.</p>"
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'\"><title>{html.escape(project_title)} · Engineering Blog</title><style>
      :root{{--ink:#172033;--muted:#627087;--line:#dbe2ec;--paper:#fbfaf7;--accent:#6849df;--wash:#f0edff}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 ui-sans-serif,system-ui,sans-serif}}main{{width:min(1060px,calc(100% - 40px));margin:auto;padding:32px 0 84px}}a{{color:var(--accent);font-weight:720;text-decoration:none}}a:hover{{text-decoration:underline}}.eyebrow{{margin:0;color:var(--muted);font:600 11px/1.35 ui-monospace,monospace;letter-spacing:.11em}}.masthead{{padding:24px 0 38px;border-bottom:1px solid var(--line)}}.masthead-nav{{display:flex;justify-content:space-between;gap:20px;margin-bottom:48px}}h1{{max-width:850px;margin:14px 0;font-size:clamp(3rem,7vw,6rem);line-height:.91;letter-spacing:-.075em}}.intro{{max-width:680px;color:var(--muted);font-size:1.1rem}}.summary{{display:grid;grid-template-columns:1.45fr repeat(2,1fr);gap:1px;margin:34px 0;background:var(--line);border:1px solid var(--line)}}.summary>div{{min-height:128px;padding:20px;background:#fff}}.summary strong{{display:block;margin-top:10px;font-size:1.28rem;letter-spacing:-.035em}}.summary span{{color:var(--muted)}}.history-head{{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:54px 0 16px}}.history-head h2{{margin:6px 0 0;font-size:2rem;letter-spacing:-.055em}}.history{{border-top:1px solid var(--line)}}.entry{{display:grid;grid-template-columns:170px minmax(0,1fr) 130px;gap:24px;padding:28px 0;border-bottom:1px solid var(--line)}}.entry-date{{margin:0;color:var(--muted);font:12px/1.45 ui-monospace,monospace}}.entry-body h2{{margin:8px 0;font-size:1.5rem;line-height:1.1;letter-spacing:-.045em}}.entry-body>p:not(.eyebrow){{margin:0;color:var(--muted)}}dl{{display:flex;flex-wrap:wrap;gap:18px;margin:18px 0 0;padding-top:14px;border-top:1px solid var(--line)}}dt{{color:var(--muted);font:600 10px ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase}}dd{{margin:3px 0 0;font-size:.88rem}}code{{overflow-wrap:anywhere}}.entry-actions{{display:flex;flex-direction:column;align-items:flex-start;gap:10px;font-size:.88rem}}.empty{{padding:26px 0;color:var(--muted)}}footer{{padding-top:34px;color:var(--muted);font-size:.85rem}}@media(max-width:720px){{main{{width:min(100% - 28px,1060px)}}.masthead-nav,.history-head{{align-items:start;flex-direction:column}}.summary,.entry{{grid-template-columns:1fr}}.summary{{gap:1px}}.entry{{gap:12px}}}}
    </style></head><body><main><header class=\"masthead\"><div class=\"masthead-nav\"><p class=\"eyebrow\">{html.escape(project_title).upper()} · ENGINEERING INDEX</p><a href=\"index.json\">Archive JSON →</a></div><p class=\"eyebrow\">SOURCE-BOUND RELEASE HISTORY</p><h1>The record of how the work changed.</h1><p class=\"intro\">A durable engineering history, not a feed. A note appears only when a frozen source bundle changes; each entry remains linked to its original structured article.</p></header><section class=\"summary\" aria-label=\"Engineering archive summary\"><div><p class=\"eyebrow\">LATEST PUBLISHED NOTE</p><strong>{html.escape(latest.get('title') or 'No note published')}</strong><span>{html.escape(latest.get('technical_topic') or 'Waiting for a changed source bundle')}</span></div><div><p class=\"eyebrow\">PUBLISHED RELEASES</p><strong>{len(articles)}</strong><span>durable source-bound note{'s' if len(articles) != 1 else ''}</span></div><div><p class=\"eyebrow\">LAST PUBLISHED</p><strong>{html.escape(print_timestamp(latest.get('generated_at')))}</strong><span>not the last dashboard render</span></div></section><section><div class=\"history-head\"><div><p class=\"eyebrow\">CHRONOLOGICAL ARCHIVE</p><h2>Release notes</h2></div><p class=\"eyebrow\">NEWEST FIRST · PERMALINKED · JSON-BACKED</p></div><div class=\"history\">{history}</div></section><footer>This index is deterministically composed from the project’s frozen release archive. It retains no-op dashboard reports as reports, not as duplicate engineering articles.</footer></main></body></html>"""


def publish_blog(root: Path, presentation: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    """Publish one article for changed facts, or reconcile to the prior article."""
    project = (presentation.get("identity") or {}).get("project") or {}
    project_slug = permalink_slug(project.get("title"))
    archive = root / "knowledge" / "dashboard" / "blog" / project_slug
    articles_dir = archive / "articles"
    archive.mkdir(parents=True, exist_ok=True)
    index_path = archive / "index.json"
    existing: list[dict[str, Any]] = []
    if index_path.is_file():
        try:
            saved = json.loads(index_path.read_text())
            if saved.get("schema") == "clineflow-dashboard-blog-index/v1" and isinstance(saved.get("articles"), list):
                existing = [item for item in saved["articles"] if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError):
            existing = []
    source_hash = str(data.get("source_hash") or "")
    article_id = f"{project_slug}-{source_hash[:16]}" if source_hash else permalink_slug(data.get("run_id"))
    relative_url = f"articles/{article_id}/index.html"
    matching_release = [item for item in existing if item.get("source_hash") == source_hash]
    # A dashboard render is not a release. Re-running identical frozen facts
    # must not write or present an old article as a newly published note.
    published = not matching_release
    if published:
        topic = blog_topic(presentation)
        article = {
            "schema": "clineflow-dashboard-blog-article/v1", "id": article_id, "run_id": data.get("run_id"),
            "generated_at": data.get("report_generated_at"), "last_rendered_at": data.get("report_generated_at"),
            "source_hash": source_hash, "url": relative_url, "json_url": f"articles/{article_id}/article.json", **topic,
        }
        article_dir = articles_dir / article_id
        article_dir.mkdir(parents=True, exist_ok=True)
        article_dir.joinpath("article.json").write_text(json.dumps(json_safe(article), indent=2, ensure_ascii=False) + "\n")
        article_dir.joinpath("index.html").write_text(blog_page(article, "../../index.html"))
        archive_items = [item for item in existing if item.get("source_hash") != source_hash and item.get("id") != article_id]
        archive_items.append({key: article[key] for key in ("id", "run_id", "generated_at", "source_hash", "url", "json_url", "title", "dek", "technical_topic")})
        archive_items.sort(key=lambda item: (str(item.get("generated_at") or ""), str(item.get("id") or "")), reverse=True)
        archive_index = {"schema": "clineflow-dashboard-blog-index/v1", "project": {"title": project.get("title"), "slug": project_slug}, "generated_at": data.get("report_generated_at"), "articles": archive_items}
        index_path.write_text(json.dumps(json_safe(archive_index), indent=2, ensure_ascii=False) + "\n")
        archive.joinpath("index.html").write_text(blog_index_page(str(project.get("title") or "Project record"), archive_items))
    else:
        archive_items = existing
        prior = sorted(matching_release, key=lambda item: (str(item.get("generated_at") or ""), str(item.get("id") or "")), reverse=True)[0]
        article_id = str(prior.get("id") or article_id)
        relative_url = str(prior.get("url") or f"articles/{article_id}/index.html")
        try:
            article = json.loads((articles_dir / article_id / "article.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Older archives can retain only index metadata. Keep it as-is
            # instead of manufacturing a replacement post on a no-op run.
            article = {"schema": "clineflow-dashboard-blog-article/v1", **prior}
        # The index is a view over durable history. It may be refreshed for an
        # existing archive without turning this unchanged report into a post.
        archive.joinpath("index.html").write_text(blog_index_page(str(project.get("title") or "Project record"), archive_items))
    public_base = os.environ.get("CLINEFLOW_DASHBOARD_PUBLIC_BASE_URL", "").strip().rstrip("/")
    public_archive = None
    if public_base.startswith(("https://", "http://")):
        public_archive = f"{public_base}/knowledge/dashboard/blog/{project_slug}/index.html"
        sitemap_urls = "".join(
            f"  <url><loc>{html.escape(public_base + '/knowledge/dashboard/blog/' + project_slug + '/' + item['url'])}</loc><lastmod>{html.escape(str(item.get('generated_at') or '')[:10])}</lastmod></url>\n"
            for item in archive_items
        )
        sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{html.escape(public_archive)}</loc><lastmod>{html.escape(str(data.get("report_generated_at") or "")[:10])}</lastmod></url>\n{sitemap_urls}</urlset>\n'
        archive.joinpath("sitemap.xml").write_text(sitemap)
        archive.joinpath("robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {public_base}/knowledge/dashboard/blog/{project_slug}/sitemap.xml\n")
    report_prefix = f"../../blog/{project_slug}/"
    def report_article(item: dict[str, Any]) -> dict[str, Any]:
        item_url = str(item.get("url") or f"articles/{item.get('id', article_id)}/index.html")
        item_json = str(item.get("json_url") or item_url.replace("index.html", "article.json"))
        return {**item, "url": f"{report_prefix}{item_url}", "json_url": f"{report_prefix}{item_json}"}

    latest_published = report_article(article)
    return {
        "title": "Engineering Blog", "archive_url": f"{report_prefix}index.html", "index_json": f"{report_prefix}index.json",
        "public_archive_url": public_archive,
        "publication": {
            "status": "published" if published else "nothing_new",
            "message": "A new source-bound engineering note was published for this frozen release." if published else "Nothing new was published: the frozen source is unchanged since the last engineering note.",
            "source_hash": source_hash, "last_published_at": article.get("generated_at"),
        },
        "current": latest_published if published else None,
        "latest_published": latest_published,
        "articles": [report_article(item) for item in archive_items],
    }


def compact_summary(value: Any, limit: int = 180) -> str:
    """Create readable summary copy while retaining the original value in detail."""
    text = re.sub(r"\s+", " ", observation_text(value)).strip()
    if len(text) <= limit:
        return text
    clipped = text[:limit + 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{clipped or text[:limit]}…"


def display_record(value: Any, kind: str, source_ids: list[str] | None = None) -> dict[str, Any]:
    """Prepare an inspectable record: a short label, a readable summary, and full detail."""
    raw = json_safe(value)
    if isinstance(value, dict) and value.get("alternatives"):
        record = guided_ledger_record(value)
        return {**record, "kind": kind, "source_ids": source_ids or [], "raw": raw}
    if isinstance(value, dict):
        preferred = next((key for key in ("title", "summary", "status", "criterion", "requirement", "name", "text", "description") if value.get(key) not in (None, "")), None)
        title_value = value.get(preferred) if preferred else value
        title = concise_title(title_value, 68)
        remaining = {key: item for key, item in value.items() if key != preferred}
        summary = compact_summary(remaining or title_value)
        fields = [{"label": humanize_key(key), "value": compact_summary(item, 150), "detail": observation_text(item)} for key, item in remaining.items()]
    else:
        title = concise_title(value, 68)
        summary = compact_summary(value)
        fields = []
    return {"kind": kind, "title": title, "summary": summary, "detail": observation_text(value), "fields": fields, "source_ids": source_ids or [], "raw": raw}


def humanize_key(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).replace("_", " ").replace("-", " ")).strip().title()


def guided_ledger_record(value: Any) -> dict[str, Any]:
    """Turn an append-only ledger item into reader copy without exposing its storage IDs."""
    if not isinstance(value, dict):
        text = observation_text(value)
        highlights = [compact_summary(item, 180) for item in re.split(r";\s+", text) if item.strip()]
        return {"title": concise_title(text, 68), "summary": compact_summary(text, 190), "detail": text, "highlights": highlights[:6], "status": "Recorded", "raw": value}
    alternatives = value.get("alternatives") or []
    statements = [
        observation_text(item.get("statement") if isinstance(item, dict) else item)
        for item in alternatives
    ]
    detail = "\n\n".join(item for item in statements if item and item != "Not recorded")
    if not detail:
        detail = observation_text({key: item for key, item in value.items() if key not in {"id", "record"}})
    highlights = [compact_summary(item, 180) for item in re.split(r";\s+", detail) if item.strip()]
    if len(highlights) < 2:
        highlights = [compact_summary(item, 180) for item in re.split(r"(?<=[.!?])\s+", detail) if item.strip()]
    identifier = value.get("id") or value.get("title") or value.get("name") or "Recorded item"
    return {
        "title": humanize_key(identifier),
        "summary": compact_summary(detail, 210),
        "detail": detail,
        "highlights": highlights[:6],
        "status": "Open" if value.get("unresolved") else "Recorded",
        "raw": json_safe(value),
    }


def guided_ledger_document(doc: dict[str, Any], structured: dict[str, Any]) -> dict[str, Any]:
    """Present ledger facts as a small record catalogue, not a YAML-shaped dump."""
    metadata = [
        {"label": humanize_key(key), "value": observation_text(structured[key])}
        for key in ("version", "updated_at", "generated_at")
        if structured.get(key) not in (None, "")
    ]
    sections: list[dict[str, Any]] = []
    excluded = {"version", "updated_at", "generated_at", "ledger", "records", "items", "journal_refs"}
    for key, value in structured.items():
        if key in excluded or value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            sections.append({"label": humanize_key(key), "type": "list", "items": [display_record(item, humanize_key(key)) for item in value]})
        elif isinstance(value, dict):
            sections.append({"label": humanize_key(key), "type": "fields", "items": [
                {"label": humanize_key(item_key), "value": compact_summary(item_value, 170), "detail": observation_text(item_value)}
                for item_key, item_value in value.items()
            ]})
        else:
            detail = observation_text(value)
            sections.append({"label": humanize_key(key), "type": "scalar", "value": compact_summary(value, 220), "detail": detail})
    return {
        "summary": compact_summary(doc.get("description") or f"{humanize_key(structured.get('ledger') or doc.get('title') or 'Ledger')} ledger."),
        "sections": sections,
        "ledger_meta": metadata,
        "ledger_records": [guided_ledger_record(item) for item in structured.get("items") or []],
    }


def guided_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Build the document-guided view before HTML rendering; raw source stays available separately."""
    structured = doc.get("structured")
    sections: list[dict[str, Any]] = []
    if doc.get("kind") == "ledger" and isinstance(structured, dict):
        return guided_ledger_document(doc, structured)
    if isinstance(structured, dict):
        for key, value in structured.items():
            if isinstance(value, list):
                sections.append({"label": humanize_key(key), "type": "list", "items": [display_record(item, humanize_key(key)) for item in value]})
            elif isinstance(value, dict):
                sections.append({"label": humanize_key(key), "type": "fields", "items": [
                    {"label": humanize_key(item_key), "value": compact_summary(item_value, 170), "detail": observation_text(item_value)}
                    for item_key, item_value in value.items()
                ]})
            else:
                detail = observation_text(value)
                sections.append({"label": humanize_key(key), "type": "scalar", "value": compact_summary(value, 220), "detail": detail})
    elif isinstance(structured, list):
        sections.append({"label": "Recorded items", "type": "list", "items": [display_record(item, "Recorded item") for item in structured]})
    elif doc.get("kind") == "journal":
        _, body = parse_frontmatter(str(doc.get("raw") or ""))
        chunks = re.split(r"^#\s+(.+?)\s*$", body, flags=re.MULTILINE)
        preferred = {"goal", "task contract", "decisions", "verification results", "open issues"}
        for index in range(1, len(chunks) - 1, 2):
            label, detail = chunks[index].strip(), chunks[index + 1].strip()
            if label.lower() in preferred and detail:
                sections.append({
                    "label": label,
                    "type": "markdown",
                    "html": safe_markdown(markdown_renderer(), detail),
                })
        if not sections and body.strip():
            sections.append({
                "label": "Journal summary",
                "type": "markdown",
                "html": safe_markdown(markdown_renderer(), body),
            })
    else:
        detail = observation_text(structured if structured is not None else doc.get("raw", ""))
        sections.append({"label": "Recorded source", "type": "scalar", "value": compact_summary(detail, 220), "detail": detail})
    return {
        "summary": compact_summary(doc.get("description") or "Structured source ready to inspect."),
        "sections": sections,
    }


def normalize_event(value: Any) -> dict[str, Any]:
    """Normalize flexible timeline records without discarding their source structure."""
    if not isinstance(value, dict):
        return {"at": None, "type": "event", "summary": observation_text(value), "refs": [], "raw": value}
    refs = first_present(value, "refs", "references", "links", "journal_refs", "evidence_refs") or []
    if not isinstance(refs, list):
        refs = [refs]
    note = first_present(value, "summary", "text", "description", "message", "detail", "change", "event")
    title = first_present(value, "short_title", "title", "label", "name")
    normalized = {
        "at": first_present(value, "at", "timestamp", "occurred_at", "datetime", "date", "time"),
        "type": first_present(value, "type", "kind", "category", "event_type", "action") or "event",
        "title": concise_title(title if title is not None else note if note is not None else value),
        "summary": note,
        "refs": [str(item) for item in refs],
        "raw": value,
    }
    normalized["summary"] = observation_text(normalized["summary"] if normalized["summary"] is not None else value)
    for key in ("actor", "git_revision", "usage", "usage_capture"):
        if key in value:
            normalized[key] = value[key]
    return json_safe(normalized)


def citation(source_ids: list[str], title: str, text: Any, **extra: Any) -> dict[str, Any]:
    """Create one source-bound report statement before it reaches the browser."""
    return {"title": title, "text": observation_text(text), "source_ids": source_ids, **extra}


def stable_spark_id(path: str) -> str:
    """Keep a Spark identity stable while the content of its source evolves."""
    return f"spark-{sha256_bytes(path.encode())[:14]}"


def journal_spark_seed(document: dict[str, Any], synthesized_at: str) -> dict[str, Any]:
    """Create a conservative candidate from the journal's own declared decision material."""
    _, body = parse_frontmatter(str(document.get("raw") or ""))
    chunks = re.split(r"^#\s+(.+?)\s*$", body, flags=re.MULTILINE)
    selected_label, selected_detail = "Journal record", document.get("description") or body
    sections = [(chunks[index].strip(), chunks[index + 1].strip()) for index in range(1, len(chunks) - 1, 2)]
    for preferred in ("decisions", "verification results", "task contract", "goal"):
        found = next(((label, detail) for label, detail in sections if label.lower() == preferred and detail), None)
        if found:
            label, detail = found
            selected_label, selected_detail = label, detail
            break
    # Keep a complete first paragraph/list item; do not flatten the entire journal.
    blocks = re.split(r"\n\s*\n|\n(?=[-*+]\s)", selected_detail.strip())
    excerpt = next((block for block in blocks if re.match(r"^[-*+]\s", block)), blocks[0])
    table = [line.strip() for line in excerpt.splitlines() if line.strip().startswith("|")]
    if len(table) >= 3 and re.match(r"^[| :\-]+$", table[1]):
        cells = [cell.strip() for cell in table[2].strip("|").split("|")]
        # Read a single decision row, preserving the column meaning in the excerpt.
        excerpt = "\n\n".join(f"**{heading.strip()}:** {cell}" for heading, cell in zip(table[0].strip("|").split("|"), cells))
    plain = html.unescape(re.sub(r"<[^>]+>", " ", safe_markdown(markdown_renderer(), excerpt)))
    learning = compact_summary(plain or document.get("title") or "Recorded journal insight", 360)
    named = re.search(r"\*\*(.+?)\*\*", excerpt)
    title = named.group(1).rstrip(":") if named and len(named.group(1)) > 10 else re.split(r"\s+—\s+|\s+\(|;", learning)[0]
    if len(table) >= 3 and re.match(r"^[| :\-]+$", table[1]):
        title = cells[1] if len(cells) > 1 else cells[0]
    return {
        "id": stable_spark_id(str(document.get("path") or document.get("id") or "journal")),
        "title": compact_summary(title, 100),
        "learning": learning,
        "excerpt": excerpt,
        "basis": "recorded_decision" if selected_label.lower() == "decisions" else "source_excerpt",
        "source_title": document.get("title") or "Journal",
        "scope": f"Source-specific learning from {document.get('title') or 'a journal'}.",
        "state": "emerging",
        "origins": [{"source_id": document["id"], "locator": f"# {selected_label}"}],
        "supporting": [],
        "challenging": [],
        "limits": "Extracted from one journal. Reuse within its stated scope; independent corroboration has not been established.",
        "synthesized_at": synthesized_at,
    }


def fallback_spark_seed(source_id: str, active_goal: Any, next_move: Any, synthesized_at: str) -> dict[str, Any]:
    learning = compact_summary(active_goal or next_move or "Capture a durable project objective before drawing a learning.", 360)
    return {
        "id": "spark-current-project-focus",
        "title": "Current project focus",
        "learning": learning,
        "scope": "Current project record.",
        "state": "emerging",
        "origins": [{"source_id": source_id, "locator": "Current recorded objective"}],
        "supporting": [],
        "challenging": [],
        "limits": "Generated from the current ledger because no journal source is available yet.",
        "synthesized_at": synthesized_at,
    }


def reconcile_sparks(candidates: list[dict[str, Any]], previous: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reconcile each run's candidates with the prior emitted Spark set."""
    prior_by_id = {str(item.get("id")): item for item in previous if item.get("id")}
    emitted: list[dict[str, Any]] = []
    lifecycle_counts = {"new": 0, "unchanged": 0, "reinforced": 0, "revised": 0, "retired": 0}
    for candidate in candidates:
        prior = prior_by_id.pop(candidate["id"], None)
        fingerprint = sha256_bytes(f"{candidate['learning']}\n{candidate['scope']}".encode())
        if not prior:
            lifecycle = "new"
        elif prior.get("fingerprint") == fingerprint:
            lifecycle = "unchanged"
        else:
            lifecycle = "revised"
        candidate["fingerprint"] = fingerprint
        candidate["lifecycle"] = lifecycle
        lifecycle_counts[lifecycle] += 1
        emitted.append(candidate)
    retired = [{"id": identifier, "title": item.get("title") or "Prior Spark", "reason": "Its source is absent from the current synthesis."} for identifier, item in prior_by_id.items()]
    lifecycle_counts["retired"] = len(retired)
    return emitted, {"previous_count": len(previous), "current_count": len(emitted), "retired_items": retired, **lifecycle_counts}


def explicit_relationships(snapshot: dict[str, Any], path_ids: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose only relationships explicitly recorded in the source material.

    A shared journal reference is useful evidence of a link, but never proof of
    a supersession or a causal decision chain. Missing relationship metadata is
    reported as an unknown instead of being fabricated from nearby prose.
    """
    relations: list[dict[str, Any]] = []
    for event in snapshot.get("events", []):
        event_refs = [path_ids[ref] for ref in event.get("refs", []) if ref in path_ids]
        if event_refs:
            relations.append({
                "kind": "event_reference", "title": event.get("title") or "Recorded event",
                "text": "This activity explicitly cites the linked source record.",
                "at": event.get("at"), "source_ids": event_refs,
            })
    journals = [item for item in snapshot.get("documents", []) if item.get("kind") == "journal"]
    unknowns = [] if not journals else [{
        "title": "Decision-chain metadata is not recorded",
        "text": "The report can show explicit source references, but it cannot establish supersession, override, or coworker influence without stable relationship fields in the canonical records.",
        "source_ids": [item["id"] for item in journals],
    }]
    return relations, unknowns


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
    ordered_events = sorted((item for item in events if item.get("at")), key=lambda item: str(item["at"]))
    first_event = ordered_events[0] if ordered_events else {}
    active_goal = next(iter(goals.get("active_goals") or []), None)
    next_move = session.get("next_recommended_step") or active_goal or "Review the latest durable context."
    latest_change = session.get("latest_change") or latest_event.get("summary") or "Durable context is ready to explore."
    open_questions = list(specification.get("open_questions") or [])
    open_verification = list(verification.get("open_verification") or [])
    drift = snapshot.get("drift") or {}
    changed_count = sum(len(drift.get(key) or []) for key in ("added", "changed", "removed"))
    timeline_source = [path_ids["knowledge/clineflow_timeline.yml"]] if "knowledge/clineflow_timeline.yml" in path_ids else []
    urgency_items = [observation_text(item) for item in [*open_questions, *open_verification]]
    milestones = [
        {"at": event.get("at"), "title": event.get("title") or concise_title(event.get("summary")), "source_ids": timeline_source}
        for event in (ordered_events[:1] + ordered_events[-2:])
    ]
    deduplicated_milestones = list({(item["at"], item["title"]): item for item in milestones}.values())
    journal_ids = [item["id"] for item in documents if item.get("kind") == "journal"]
    relationships, relationship_unknowns = explicit_relationships(snapshot, path_ids)
    journal_sources = [item for item in documents if item.get("kind") == "journal"]
    spark_candidates = [journal_spark_seed(item, snapshot["run_at"]) for item in journal_sources]
    if not spark_candidates and source_ids:
        spark_candidates = [fallback_spark_seed(source_ids[0], active_goal, next_move, snapshot["run_at"])]
    sparks, spark_reconciliation = reconcile_sparks(spark_candidates, snapshot.get("previous_sparks") or [])
    origin_text = (
        f"The recorded story begins with {first_event.get('title') or 'the first available durable record'}"
        f" and is grounded in {len(journal_ids)} journal{'s' if len(journal_ids) != 1 else ''}."
    )
    overall_text = (
        f"{len(documents)} canonical records and {len(events)} timeline events form the current report range. "
        f"{observation_text(active_goal or latest_change)}"
    )
    recent_text = observation_text(latest_event.get("summary") or latest_change)
    digest_text = observation_text(next_move)
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
                "source_ids": source_ids,
            },
            "manager": {
                "headline": latest_event.get("summary") or latest_change,
                "why_it_matters": f"{len(open_questions) + len(open_verification)} unresolved questions or verification items remain visible.",
                "next_move": next_move,
                "source_ids": source_ids,
            },
            "engineer": {
                "headline": f"{len(documents)} canonical sources and {len(events)} timeline events are inspectable.",
                "why_it_matters": "Every observation can be traced back to normalized facts and canonical source documents.",
                "next_move": next_move,
                "source_ids": source_ids,
            },
        },
        "narratives": {
            "origin": citation(timeline_source or journal_ids, "Origin", origin_text),
            "overall": citation(source_ids, "Overall record", overall_text),
            "recent": citation(timeline_source or source_ids, "Most recent story", recent_text, at=latest_event.get("at")),
            "digest": citation(source_ids, "Executive digest", digest_text),
        },
        "coverage": {
            "journal_ids": journal_ids,
            "covered_journal_ids": journal_ids,
            "uncovered_journal_ids": [],
        },
        "relationship_analysis": {"relationships": relationships, "unknowns": relationship_unknowns},
        "sparks": sparks,
        "observations_harness": {
            "schema": "clineflow-dashboard-sparks/v1", "repair_limit": 2,
            "candidate_count": len(spark_candidates), "published_count": len(sparks),
            "reconciled_from_run": snapshot.get("previous_spark_run"),
            "reconciliation": spark_reconciliation,
            "note": "Every run emits source-bound Spark candidates, reconciles stable identities with the prior run, and withholds only records with no available source.",
        },
        "project_story": {
            "evolution": {
                "title": "How the project evolved",
                "text": (
                    f"From {first_event.get('title') or 'its first recorded milestone'} to "
                    f"{latest_event.get('title') or 'the current state'}, the knowledge base records "
                    f"{len(events)} milestones rather than a single status snapshot."
                ),
                "source_ids": timeline_source,
            },
            "important_now": {
                "title": "What matters now",
                "text": observation_text(active_goal or latest_change),
                "source_ids": [item for item in source_ids if item in {path_ids.get("knowledge/clineflow_goals.yml"), path_ids.get("knowledge/clineflow_last_session.yml")}],
            },
            "urgency": {
                "title": "What needs attention",
                "text": " · ".join(urgency_items[:3]) if urgency_items else "No unresolved questions or verification gaps are recorded right now.",
                "source_ids": [item for item in source_ids if item in {path_ids.get("knowledge/clineflow_specification.yml"), path_ids.get("knowledge/clineflow_verification.yml")}],
            },
            "next_action": {
                "title": "The next deliberate move",
                "text": observation_text(next_move),
                "source_ids": [path_ids["knowledge/clineflow_last_session.yml"]] if "knowledge/clineflow_last_session.yml" in path_ids else source_ids,
            },
            "milestones": deduplicated_milestones,
        },
        "project_phases": [],
        "notable_changes": ([{"text": latest_change, "source_ids": source_ids}] if latest_change else []),
        "risks": [{"text": observation_text(item), "source_ids": source_ids} for item in open_verification],
        "questions": [{"text": observation_text(item), "source_ids": source_ids} for item in open_questions],
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
    document_ids = {item["id"] for item in snapshot["documents"]}
    audiences = data.get("audiences")
    required_audiences = {"executive", "manager", "engineer"}
    required_story_fields = {"headline", "why_it_matters", "next_move", "source_ids"}
    if not isinstance(audiences, dict) or set(audiences) != required_audiences:
        raise ValueError("observations require executive, manager, and engineer narratives")
    for audience, story in audiences.items():
        if not isinstance(story, dict) or not required_story_fields.issubset(story) or any(
            not isinstance(story[field], str) for field in ("headline", "why_it_matters", "next_move")
        ):
            raise ValueError(f"{audience} narrative requires text headline, why_it_matters, and next_move")
        if not isinstance(story["source_ids"], list) or not set(story["source_ids"]).issubset(document_ids):
            raise ValueError(f"{audience} narrative contains an unknown source id")
    project_story = data.get("project_story")
    required_project_story = {"evolution", "important_now", "urgency", "next_action", "milestones"}
    if not isinstance(project_story, dict) or not required_project_story.issubset(project_story):
        raise ValueError("observations require a complete source-bound project story")
    for key in ("evolution", "important_now", "urgency", "next_action"):
        card = project_story[key]
        if not isinstance(card, dict) or not isinstance(card.get("title"), str) or not isinstance(card.get("text"), str):
            raise ValueError(f"project story {key} requires title and text")
        refs = card.get("source_ids", [])
        if not isinstance(refs, list) or not set(refs).issubset(document_ids):
            raise ValueError(f"project story {key} contains an unknown source id")
    if not isinstance(project_story["milestones"], list):
        raise ValueError("project story milestones must be a list")
    for milestone in project_story["milestones"]:
        if not isinstance(milestone, dict) or not isinstance(milestone.get("title"), str):
            raise ValueError("project story milestones require a title")
        refs = milestone.get("source_ids", [])
        if not isinstance(refs, list) or not set(refs).issubset(document_ids):
            raise ValueError("project story milestone contains an unknown source id")
    narratives = data.get("narratives")
    if not isinstance(narratives, dict) or set(narratives) != {"origin", "overall", "recent", "digest"}:
        raise ValueError("observations require origin, overall, recent, and executive-digest narratives")
    for name, statement in narratives.items():
        if not isinstance(statement, dict) or not isinstance(statement.get("title"), str) or not isinstance(statement.get("text"), str):
            raise ValueError(f"narrative {name} requires title and text")
        if not isinstance(statement.get("source_ids"), list) or not set(statement["source_ids"]).issubset(document_ids):
            raise ValueError(f"narrative {name} contains an unknown source id")
    coverage = data.get("coverage")
    journal_ids = {item["id"] for item in snapshot["documents"] if item.get("kind") == "journal"}
    if not isinstance(coverage, dict) or set(coverage) != {"journal_ids", "covered_journal_ids", "uncovered_journal_ids"}:
        raise ValueError("observations require explicit journal coverage")
    for key in coverage:
        if not isinstance(coverage[key], list) or not set(coverage[key]).issubset(document_ids):
            raise ValueError(f"coverage {key} contains an unknown source id")
    if set(coverage["journal_ids"]) != journal_ids or set(coverage["covered_journal_ids"]).union(coverage["uncovered_journal_ids"]) != journal_ids:
        raise ValueError("journal coverage must account for every journal exactly once")
    analysis = data.get("relationship_analysis")
    if not isinstance(analysis, dict) or set(analysis) != {"relationships", "unknowns"}:
        raise ValueError("observations require explicit relationship analysis")
    for group in ("relationships", "unknowns"):
        if not isinstance(analysis[group], list):
            raise ValueError(f"relationship analysis {group} must be a list")
        for item in analysis[group]:
            if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not isinstance(item.get("source_ids"), list) or not set(item["source_ids"]).issubset(document_ids):
                raise ValueError(f"relationship analysis {group} contains an invalid citation")
    sparks = data.get("sparks", [])
    if not isinstance(sparks, list):
        raise ValueError("sparks must be a list")
    if document_ids and not sparks:
        raise ValueError("observations require at least one source-bound Spark when source records are available")
    allowed_spark_states = {"emerging", "supported", "contested", "superseded"}
    spark_ids: list[str] = []
    for index, spark in enumerate(sparks):
        if not isinstance(spark, dict):
            raise ValueError(f"spark {index} must be an object")
        required = {"id", "title", "learning", "scope", "state", "origins", "supporting", "challenging", "limits", "synthesized_at"}
        if not required.issubset(spark):
            raise ValueError(f"spark {index} is missing required fields")
        if not all(isinstance(spark.get(field), str) for field in ("id", "title", "learning", "scope", "limits", "synthesized_at")):
            raise ValueError(f"spark {index} requires string identity, learning, scope, limits, and synthesized_at")
        if spark.get("state") not in allowed_spark_states:
            raise ValueError(f"spark {index} has an unsupported evidence state")
        spark_ids.append(spark["id"])
        for field in ("origins", "supporting", "challenging"):
            references = spark.get(field)
            if not isinstance(references, list):
                raise ValueError(f"spark {index} {field} must be a list")
            if field == "origins" and not references:
                raise ValueError(f"spark {index} requires at least one origin")
            for reference in references:
                if not isinstance(reference, dict) or not isinstance(reference.get("source_id"), str) or not isinstance(reference.get("locator"), str):
                    raise ValueError(f"spark {index} {field} references require source_id and locator")
                if reference["source_id"] not in document_ids or not reference["locator"].strip():
                    raise ValueError(f"spark {index} {field} contains an unresolved source locator")
        if spark.get("state") == "contested" and not spark.get("challenging"):
            raise ValueError(f"spark {index} marked contested without challenging evidence")
        if spark.get("state") == "supported":
            origins = {(ref["source_id"], ref["locator"].strip()) for ref in spark["origins"]}
            support = {(ref["source_id"], ref["locator"].strip()) for ref in spark["supporting"]}
            if not support - origins:
                raise ValueError(f"spark {index} marked supported without additional evidence beyond its origins")
    if len(spark_ids) != len(set(spark_ids)):
        raise ValueError("spark ids must be unique")
    validate_insights_payload = {
        key: data.get(key) for key in AGENT_INSIGHT_FIELDS if key in data
    }
    validate_insights_data(validate_insights_payload, document_ids, allow_deterministic_summary=True)
    return data


def collect(root: Path, compare: str = "previous") -> dict[str, Any]:
    ledgers, documents = collect_knowledge(root)
    commits = collect_commits(root)
    events = [normalize_event(item) for item in (ledgers.get("clineflow_timeline") or {}).get("events", [])]
    associate_events(events, commits)
    source_hash = sha256_bytes("".join(item["hash"] for item in documents).encode())
    baseline_id, baseline = select_baseline(root, source_hash, compare)
    run_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    data = {
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
    attach_previous_report(root, data)
    data["report_identity"] = report_identity(data, root)
    return data


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


def print_timestamp(value: Any) -> str:
    """Format a recorded timestamp for a human-facing local archive."""
    if not value:
        return "Not recorded"
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)
    return parsed.astimezone(dt.timezone.utc).strftime("%b %-d, %Y")


def build_presentation(data: dict[str, Any], observations: dict[str, Any], draft_scope: str | None = None) -> dict[str, Any]:
    """Build the only view model consumed by the browser renderer."""
    documents = [{**item, "guided": guided_document(item)} for item in data.get("documents", [])]
    document_ids = {item.get("id") for item in documents}
    document_id_for_path = {item.get("path"): item.get("id") for item in documents}
    ledgers = data.get("ledgers") or {}
    specification = ledgers.get("clineflow_specification") or {}
    verification = ledgers.get("clineflow_verification") or {}
    goals = ledgers.get("clineflow_goals") or {}
    session = ledgers.get("clineflow_last_session") or {}
    specification_snapshot_at = specification.get("updated_at") or specification.get("generated_at")
    verification_snapshot_at = verification.get("updated_at") or verification.get("generated_at")
    events = [normalize_event(item) for item in data.get("events", [])]
    timeline = [
        {"lane": "event", "when": item.get("at"), "label": item.get("type") or "event", "title": item.get("title"), "summary": item.get("summary"), "refs": item.get("refs", []), "association": item.get("association")}
        for item in events
    ]
    timeline.extend({
        "lane": "journal", "when": item.get("generated_at"), "label": "journal", "title": item.get("title"),
        "summary": item.get("description") or item.get("title"), "source_id": item.get("id"),
    } for item in documents if item.get("generated_at"))
    timeline.extend({
        "lane": "commit", "when": item.get("committed_at"), "label": "git", "title": concise_title(item.get("summary")),
        "summary": item.get("summary"),
    } for item in data.get("commits", []))
    timeline.sort(key=lambda item: str(item.get("when") or ""), reverse=True)
    latest = next((item for item in timeline if item["lane"] in {"event", "commit"}), None)
    latest_verification = next((item for item in timeline if item["lane"] == "event" and item["label"] == "verification"), None)
    unresolved = [
        {**display_record(item, "Decision needed", [document_id_for_path["knowledge/clineflow_specification.yml"]] if document_id_for_path.get("knowledge/clineflow_specification.yml") else []), "why": "The specification still leaves this choice open.", "next": "Choose an owner and record the decision.", "recorded_at": specification_snapshot_at, "date_label": "Ledger snapshot"}
        for item in specification.get("open_questions") or []
    ] + [
        {**display_record(item, "Proof gap", [document_id_for_path["knowledge/clineflow_verification.yml"]] if document_id_for_path.get("knowledge/clineflow_verification.yml") else []), "why": "The implementation has no recorded verification for this point yet.", "next": "Run or record the missing evidence.", "recorded_at": verification_snapshot_at, "date_label": "Ledger snapshot"}
        for item in verification.get("open_verification") or []
    ]
    for ledger_name, ledger in (("specification", specification), ("verification", verification), ("last_session", session)):
        source_id = document_id_for_path.get(f"knowledge/clineflow_{ledger_name}.yml")
        unresolved.extend({**display_record(item, "Conflicting records", [source_id] if source_id else []), "recorded_at": (specification_snapshot_at if ledger_name == "specification" else verification_snapshot_at if ledger_name == "verification" else session.get("updated_at") or session.get("generated_at")), "date_label": "Ledger snapshot"}
                          for item in ledger.get("items") or [] if item.get("unresolved"))
    constraints = [
        {**display_record(item, "Constraint", [document_id_for_path["knowledge/clineflow_specification.yml"]] if document_id_for_path.get("knowledge/clineflow_specification.yml") else []), "why": "This boundary shapes the implementation decision.", "next": "Keep the constraint visible while deciding.", "recorded_at": specification_snapshot_at, "date_label": "Ledger snapshot"}
        for item in specification.get("constraints") or []
    ]
    active_goal = observation_text(next(iter(goals.get("active_goals") or []), ""))
    headline = concise_title(active_goal or (latest.get("title") if latest else "Build the first durable project record"), 68)
    def ledger_source(path: str) -> list[str]:
        return [document_id_for_path[path]] if document_id_for_path.get(path) else []
    first_constraint = next(iter(specification.get("constraints") or []), None)
    first_question = next(iter(specification.get("open_questions") or []), None)
    first_gap = next(iter(verification.get("open_verification") or []), None)
    proof_text = observation_text(first_gap) if first_gap else (latest_verification.get("title") if latest_verification else "Record verification evidence for the completed move.")
    agentic_loop = [
        {"step": "01", "label": "Aim", "text": active_goal or "Record the active project goal.", "source_ids": ledger_source("knowledge/clineflow_goals.yml")},
        {"step": "02", "label": "Decide", "text": observation_text(first_question or first_constraint or "No active constraint or open decision is recorded."), "source_ids": ledger_source("knowledge/clineflow_specification.yml")},
        {"step": "03", "label": "Act", "text": observation_text(session.get("next_recommended_step") or "Choose and record the next deliberate move."), "source_ids": ledger_source("knowledge/clineflow_last_session.yml")},
        {"step": "04", "label": "Prove", "text": proof_text, "source_ids": ledger_source("knowledge/clineflow_verification.yml")},
    ]
    commits = data.get("commits") or []
    project_pulse = {
        "commits": [{
            "when": item.get("committed_at"), "summary": concise_title(item.get("summary")),
            "revision": item.get("short_revision"), "change": item.get("change") or {},
            "footprint": item.get("footprint") or {},
        } for item in commits],
        "working_tree": {
            "change": data.get("current_change") or {}, "footprint": data.get("current_footprint") or {},
            "dirty": bool((data.get("git") or {}).get("dirty")),
        },
        "summary": (
            f"{len(commits)} committed change{'s' if len(commits) != 1 else ''} provide the historical pulse; "
            "the working-tree snapshot is labeled separately."
            if commits else "No committed Git history is available yet. Generate a first commit to establish the pulse."
        ),
    }
    estimate_input = observations.get("delivery_estimate")
    delivery_estimate = calculate_delivery_estimate(estimate_input) if estimate_input else None
    journals_by_topic: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        if document.get("kind") != "journal":
            continue
        topic = journal_workstream(document)
        journals_by_topic.setdefault(topic, []).append({
            "id": document.get("id"), "title": document.get("title"),
            "description": document.get("description"), "status": document.get("status"),
            "generated_at": document.get("generated_at"), "path": document.get("path"),
        })
    for items in journals_by_topic.values():
        items.sort(key=lambda item: str(item.get("generated_at") or ""), reverse=True)
    identity = report_identity(data)
    history = report_history(data, observations)
    history_sources = ledger_source("knowledge/clineflow_timeline.yml") + ledger_source("knowledge/clineflow_last_session.yml")
    for card in history["cards"]:
        card["source_ids"] = history_sources
    event_times = sorted(item.get("at") for item in events if item.get("at"))
    project_title = identity.get("project", {}).get("title") or "this project"
    journal_docs = [item for item in documents if item.get("kind") == "journal"]
    journal_docs.sort(key=lambda item: str(item.get("generated_at") or ""), reverse=True)
    references: dict[str, int] = {}
    for event in events:
        for path in event.get("refs") or []:
            if document_id_for_path.get(path):
                references[path] = references.get(path, 0) + 1
    focus_path = max(references, key=references.get) if references else None
    focus_doc = next((item for item in documents if item.get("path") == focus_path), None)
    focus_doc = focus_doc or (journal_docs[0] if journal_docs else None)
    focus_sources = [focus_doc.get("id")] if focus_doc and focus_doc.get("id") else []
    recorded_days = sorted({str(value)[:10] for value in event_times if str(value)[:10]})
    active_days = 0
    if len(recorded_days) >= 2:
        try:
            active_days = (dt.date.fromisoformat(recorded_days[-1]) - dt.date.fromisoformat(recorded_days[0])).days + 1
        except ValueError:
            active_days = len(recorded_days)
    elif recorded_days:
        active_days = 1
    activity_source_ids = ledger_source("knowledge/clineflow_timeline.yml") or focus_sources
    process_item = first_gap or first_question
    process_sources = ledger_source("knowledge/clineflow_verification.yml") if first_gap else ledger_source("knowledge/clineflow_specification.yml")
    process_sources = process_sources or ledger_source("knowledge/clineflow_last_session.yml")
    if process_item:
        process_value = "Close one recorded gap"
        process_text = observation_text(process_item)
    else:
        process_value = "Keep the record current"
        process_text = observation_text(session.get("next_recommended_step") or "Record the next deliberate move and its proof.")
    commentary = [
        {
            "label": "ACTIVE RECORD",
            "value": f"{len(recorded_days)} active date{'s' if len(recorded_days) != 1 else ''}" if recorded_days else "No dated activity",
            "text": f"{len(event_times)} dated events over {active_days} calendar days. This measures record coverage, not work effort." if recorded_days else "No dated timeline events in this snapshot.",
            "source_ids": activity_source_ids,
        },
        {
            "label": "CHANGE FOCUS",
            "value": focus_doc.get("title") if focus_doc else "No linked focus",
            "text": f"Cited by {references.get(focus_path, 0)} timeline record{'s' if references.get(focus_path, 0) != 1 else ''}." if focus_path else "Link timeline records to a journal or ledger to establish a focus.",
            "source_ids": focus_sources,
        },
        {
            "label": "RECORD CADENCE",
            "value": f"{len(events)} moments across {len(recorded_days)} dates" if recorded_days else "No dated moments",
            "text": "Open Activity for the grouped chronological sequence and its source records." if events else "The first dated event will create a chronological sequence.",
            "source_ids": activity_source_ids,
        },
        {
            "label": "PROCESS MOVE",
            "value": process_value,
            "text": process_text,
            "source_ids": process_sources,
        },
    ]
    def assistant_prompt(source_name: str, question: str) -> str:
        return (
            f"I am orienting to {project_title}. Read the {source_name} in the project knowledge record and answer:\n\n"
            f"{question}\n\n"
            "Cite the source, distinguish recorded fact from inference, and finish with the next action I should take."
        )
    aim_question = "What is the active objective, what boundary does it set, and what is the next recorded move?"
    trace_question = (
        f"What changed in {focus_doc.get('title', 'the most recent journal')}, why did it matter, and which prior decision does it build on?"
        if focus_doc else "Which journal should I read first to understand the current direction, and why?"
    )
    prove_question = (
        f"What evidence is still needed to close this recorded gap: {observation_text(process_item)}?"
        if process_item else "What is the next move, and what evidence should I record when it is complete?"
    )
    onboarding = {
        "empty": not documents,
        "title": "Learn this project from its record" if documents else "Start the project record",
        "text": "Follow the source route, then copy a question into your project assistant when you want a deeper explanation.",
        "steps": [
            {"step": "01", "title": "Frame the work", "question": aim_question, "prompt": assistant_prompt("Goals and latest-session ledgers", aim_question), "source_ids": ledger_source("knowledge/clineflow_goals.yml") + ledger_source("knowledge/clineflow_last_session.yml")},
            {"step": "02", "title": "Trace the change", "question": trace_question, "prompt": assistant_prompt(focus_doc.get("title", "journal portfolio") if focus_doc else "journal portfolio", trace_question), "source_ids": focus_sources},
            {"step": "03", "title": "Check the proof", "question": prove_question, "prompt": assistant_prompt("Verification and specification ledgers", prove_question), "source_ids": process_sources},
        ],
    }
    design_records = [guided_ledger_record(item) for item in specification.get("items") or specification.get("confirmed") or []]
    proof_records = [{**display_record(item, "Verification evidence", ledger_source("knowledge/clineflow_verification.yml")), "recorded_at": verification_snapshot_at, "date_label": "Ledger snapshot"}
                     for item in verification.get("evidence") or verification.get("items") or verification.get("acceptance_criteria") or []]
    update_dates = {
        str((document.get("structured") or {}).get("id")): (document.get("structured") or {}).get("at")
        for document in documents
        if str(document.get("path") or "").startswith("knowledge/updates/")
        and isinstance(document.get("structured"), dict)
        and (document.get("structured") or {}).get("id")
        and (document.get("structured") or {}).get("at")
    }
    session_snapshot_at = session.get("updated_at") or session.get("generated_at")
    def follow_up_record(item: Any) -> dict[str, Any]:
        source_dates = [
            update_dates.get(str(alternative.get("record")))
            for alternative in item.get("alternatives") or []
            if isinstance(alternative, dict)
        ] if isinstance(item, dict) else []
        recorded_at = max((value for value in source_dates if isinstance(value, str)), default=session_snapshot_at)
        return {
            **display_record(item, "Recorded follow-up", ledger_source("knowledge/clineflow_last_session.yml")),
            "recorded_at": recorded_at,
            "date_label": "Last updated" if recorded_at and recorded_at in source_dates else "Ledger snapshot",
        }
    session_records = [follow_up_record(item) for item in session.get("items") or []]
    next_steps = session.get("next_recommended_step")
    latest_change_text = observation_text(session.get("latest_change") or (latest or {}).get("summary") or "No recent change is recorded.")
    onboarding["title"] = f"Get oriented in {project_title}"
    onboarding["text"] = "Read the essentials, inspect a source, then take a focused question into your project assistant."
    route_content = [
        ("Understand the design", compact_summary(design_records[0]["detail"], 460) if design_records else (journal_docs[-1].get("description") if journal_docs else "No design record is available."), ledger_source("knowledge/clineflow_specification.yml")),
        ("Catch up on the latest change", compact_summary(latest_change_text, 460), ledger_source("knowledge/clineflow_last_session.yml")),
        ("Find the evidence", f"{len(proof_records)} verification records and {len(unresolved)} conflicting or open entries are available. Read the recorded checks before relying on a completion claim.", ledger_source("knowledge/clineflow_verification.yml")),
    ]
    for step, (title, answer, ids) in zip(onboarding["steps"], route_content):
        step.update(title=title, answer=answer, source_ids=ids)
        paths = [item["path"] for item in documents if item["id"] in ids]
        step["question"] = {
            "01": f"Explain the key design decisions in this specification. What must I understand before changing {project_title}?",
            "02": "Trace the latest recorded change to its decisions and tests. Which records explain why it was needed?",
            "03": "Which verification results apply to the latest change, and what still needs checking before I reuse this work?",
        }[step["step"]]
        step["prompt"] = assistant_prompt(", ".join(paths) or "available source records", step["question"])
    if design_records:
        onboarding["steps"][0]["points"] = design_records[0]["highlights"][:3]
    contributors = sorted({str(item.get("actor")) for item in events if item.get("actor")})
    coverage = observations.get("coverage") or {}
    provenance = {
        "facts_source_hash": data.get("source_hash"),
        "observations_source_hash": (observations.get("source") or {}).get("source_hash"),
        "journal_count": len(coverage.get("journal_ids") or []),
        "covered_journal_count": len(coverage.get("covered_journal_ids") or []),
        "uncovered_journal_ids": coverage.get("uncovered_journal_ids") or [],
        "source_count": len(documents),
    }
    workstream_sources = [item.get("id") for item in journal_docs if item.get("id")]
    coverage_sources = ledger_source("knowledge/clineflow_timeline.yml") + ledger_source("knowledge/clineflow_last_session.yml")
    return_sources = focus_sources or workstream_sources or ledger_source("knowledge/clineflow_specification.yml")
    contributor_value = (
        f"{len(contributors)} recorded contributor{'s' if len(contributors) != 1 else ''}"
        if contributors else "No recorded contributors"
    )
    dated_value = (
        f"{active_days or len(recorded_days)} recorded day{'s' if (active_days or len(recorded_days)) != 1 else ''}"
        if recorded_days else "No dated record"
    )
    linked_value = f"{len(references)} traceable link{'s' if len(references) != 1 else ''}"
    decision_lenses = [
        {
            "id": "product_manager",
            "label": "Product manager",
            "description": "Use the record to align ownership, product rhythm, and the next decision.",
            "insights": [
                {
                    "category": "team", "label": "Team", "value": contributor_value,
                    "text": "This is a recorded authorship signal, not a staffing or capacity estimate.",
                    "source_ids": activity_source_ids,
                },
                {
                    "category": "time", "label": "Time", "value": dated_value,
                    "text": f"{len(events)} dated record{'s' if len(events) != 1 else ''} establish the visible product rhythm; they do not measure effort.",
                    "source_ids": coverage_sources or activity_source_ids,
                },
                {
                    "category": "return", "label": "Return", "value": f"{len(journals_by_topic)} workstream{'s' if len(journals_by_topic) != 1 else ''}",
                    "text": "Recorded return proxy: a reusable, source-linked basis for prioritization—not financial ROI.",
                    "source_ids": workstream_sources or return_sources,
                },
            ],
        },
        {
            "id": "executive",
            "label": "Executive",
            "description": "Read the scope, record coverage, and governance value without unsupported financial claims.",
            "insights": [
                {
                    "category": "team", "label": "Team", "value": f"{len(journals_by_topic)} named workstream{'s' if len(journals_by_topic) != 1 else ''}",
                    "text": "The portfolio is visible through its named records; it is not an organization chart or headcount.",
                    "source_ids": workstream_sources or activity_source_ids,
                },
                {
                    "category": "time", "label": "Time", "value": dated_value,
                    "text": "Calendar coverage shows when the record was active; it is not a budget, burn rate, or delivery forecast.",
                    "source_ids": coverage_sources or activity_source_ids,
                },
                {
                    "category": "return", "label": "Return", "value": f"{provenance.get('covered_journal_count', 0)}/{provenance.get('journal_count', 0)} journals covered",
                    "text": "Recorded return proxy: decision traceability across the source base—not realized revenue or financial ROI.",
                    "source_ids": return_sources,
                },
            ],
        },
        {
            "id": "technical_lead",
            "label": "Technical lead",
            "description": "Inspect traceability, engineering cadence, and the reusable evidence behind the next technical move.",
            "insights": [
                {
                    "category": "team", "label": "Team", "value": linked_value,
                    "text": "Linked records make handoffs and decisions inspectable; they do not establish team size or ownership capacity.",
                    "source_ids": focus_sources or activity_source_ids,
                },
                {
                    "category": "time", "label": "Time", "value": f"{len(events)} dated engineering moment{'s' if len(events) != 1 else ''}",
                    "text": "The timeline reports recorded moments over dated coverage, not implementation hours or velocity.",
                    "source_ids": activity_source_ids,
                },
                {
                    "category": "return", "label": "Return", "value": linked_value,
                    "text": "Recorded return proxy: a traceable change path that can reduce rediscovery—not financial ROI.",
                    "source_ids": return_sources,
                },
            ],
        },
    ]
    relationships = (observations.get("relationship_analysis") or {}).get("relationships", [])
    relationship_unknowns = (observations.get("relationship_analysis") or {}).get("unknowns", [])
    return json_safe({
        "schema": PRESENTATION_SCHEMA,
        "generated_at": data.get("report_generated_at") or data.get("run_at"),
        "source": {"snapshot_schema": data.get("schema"), "source_hash": data.get("source_hash"), "observation_schema": observations.get("schema")},
        "report": {"run_id": data.get("run_id"), "git": data.get("git") or {}, "retention": data.get("retention"), "selector": data.get("report_selector") or []},
        "identity": identity,
        "now": {
            "headline": headline,
            "summary": observation_text(observations.get("executive_summary")) or session.get("latest_change") or onboarding["text"],
            "intent": active_goal,
            "next_move": observation_text(next_steps) if next_steps else "No single next step is designated. Review the recorded follow-ups before choosing one.",
            "latest_change": latest_change_text,
            "source_ids": ledger_source("knowledge/clineflow_last_session.yml"),
            "follow_ups": session_records,
            "latest_activity": latest,
            "latest_verification": latest_verification,
            "unresolved_count": len(unresolved),
        },
        "story": observations.get("project_story") or {},
        "narratives": observations.get("narratives") or {},
        "sparks": [{**item, "excerpt_html": safe_markdown(markdown_renderer(), item.get("excerpt") or item.get("learning") or "")} for item in observations.get("sparks") or []],
        "observations_harness": observations.get("observations_harness") or {},
        "audiences": observations.get("audiences") or {},
        "timeline": timeline,
        "documents": documents,
        "unresolved": unresolved,
        "decisions": constraints + unresolved,
        "onboarding": onboarding,
        "agentic_loop": agentic_loop,
        "project_pulse": project_pulse,
        "delivery_estimate": delivery_estimate,
        "workspace": {
            "ledgers": [{"id": item.get("id"), "title": item.get("title"), "path": item.get("path"), "structured": item.get("structured")} for item in documents if item.get("kind") == "ledger"],
            "workstreams": [{"topic": topic, "journals": items} for topic, items in sorted(journals_by_topic.items())],
            "commentary": commentary,
            "report_history": history,
            "decision_lenses": decision_lenses,
        },
        "activity": {"events": events, "contributors": contributors, "types": sorted({str(item.get("type") or "event") for item in events})},
        "evidence_register": {
            "verification": proof_records,
            "decisions": constraints + unresolved,
            "relationships": relationships, "unknowns": relationship_unknowns, "provenance": provenance,
        },
        "blog": data.get("blog") or {},
        "evidence": proof_records,
        "metrics": {
            "documents": len(documents), "events": len(events), "usage": len(data.get("usage") or []),
            "drift": data.get("drift") or {"added": [], "changed": [], "removed": []},
            "current_change": data.get("current_change") or {}, "current_footprint": data.get("current_footprint") or {},
            "commits": data.get("commits") or [],
        },
    })


def build_page(runtime: Path, data: dict[str, Any], observations: dict[str, Any], presentation: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
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
    page = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"{csp}\"><title>ClineFlow Knowledge Visor</title><style>{font_css}{custom_css}</style></head><body><a class=\"skip\" href=\"#main\">Skip to knowledge</a><div id=\"app\"></div><script id=\"clineflow-data\" type=\"application/json\">{safe_json_for_script(data)}</script><script id=\"clineflow-observations\" type=\"application/json\">{safe_json_for_script(observations)}</script><script id=\"clineflow-presentation\" type=\"application/json\">{safe_json_for_script(presentation)}</script><script>{custom_js}</script></body></html>"""
    return page, asset_manifest


def completed_runs(runs_dir: Path) -> list[Path]:
    """Return only complete report directories owned by this dashboard schema."""
    result: list[Path] = []
    for candidate in runs_dir.iterdir() if runs_dir.is_dir() else []:
        manifest = candidate / "manifest.json"
        if not candidate.is_dir() or not manifest.is_file():
            continue
        try:
            payload = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("schema") == SCHEMA and payload.get("run_id") == candidate.name:
            result.append(candidate)
    return sorted(result, key=lambda path: path.name, reverse=True)


def prune_runs(runs_dir: Path, retention: int | None) -> None:
    if retention is None:
        return
    for run in completed_runs(runs_dir)[retention:]:
        shutil.rmtree(run)


def render_report(root: Path, runtime: Path, data: dict[str, Any], observations: dict[str, Any], no_open: bool, retention: int | None = None) -> Path:
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
    data["report_generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    data["retention"] = retention
    data["report_selector"] = report_selector(root, data)
    presentation = build_presentation(data, observations, str(root.resolve()))
    presentation["blog"] = publish_blog(root, presentation, data)
    page, asset_manifest = build_page(runtime, data, observations, presentation)
    report_manifest = {
        "schema": SCHEMA,
        "generator_version": next((line.split("=", 1)[1] for line in (runtime / ".active").read_text().splitlines() if line.startswith("component_version=")), "unknown"),
        "run_id": data["run_id"], "generated_at": data["report_generated_at"],
        "source_hash": data["source_hash"], "baseline_run": data.get("baseline_run"),
        "git": data["git"], "assets": asset_manifest,
        "observations": {"schema": observations["schema"], "generator": observations["generator"]},
        "presentation": {"schema": presentation["schema"]}, "retention": retention,
        "blog": {"schema": "clineflow-dashboard-blog-index/v1", "archive": presentation["blog"]["archive_url"], "article": (presentation["blog"].get("current") or presentation["blog"].get("latest_published") or {}).get("url"), "publication_status": (presentation["blog"].get("publication") or {}).get("status")},
        "browser_network": "disabled", "warnings": [],
    }
    (temporary / "index.html").write_text(page)
    (temporary / "manifest.json").write_text(json.dumps(report_manifest, indent=2, ensure_ascii=False) + "\n")
    (temporary / "snapshot.json").write_text(json.dumps(json_safe(data), indent=2, ensure_ascii=False) + "\n")
    (temporary / "observations.json").write_text(json.dumps(json_safe(observations), indent=2, ensure_ascii=False) + "\n")
    (temporary / "presentation.json").write_text(json.dumps(presentation, indent=2, ensure_ascii=False) + "\n")
    for path in temporary.iterdir():
        try:
            path.chmod(0o700 if path.is_dir() else 0o600)
        except OSError:
            pass
    temporary.rename(run_dir)
    prune_runs(runs_dir, retention)
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
    observations.pop("delivery_estimate", None)
    output.mkdir(parents=True, exist_ok=False)
    sanitized["retention"] = None
    presentation = build_presentation(sanitized, observations, "sanitized-export")
    presentation.pop("delivery_estimate", None)
    page, asset_manifest = build_page(runtime, sanitized, observations, presentation)
    output.joinpath("data.json").write_text(json.dumps(sanitized, indent=2, ensure_ascii=False) + "\n")
    output.joinpath("observations.json").write_text(json.dumps(observations, indent=2, ensure_ascii=False) + "\n")
    output.joinpath("presentation.json").write_text(json.dumps(presentation, indent=2, ensure_ascii=False) + "\n")
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
    generate.add_argument("--retain")
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--output", type=Path, required=True)
    collect_parser.add_argument("--compare", default="previous")
    observe = sub.add_parser("observe")
    observe.add_argument("--facts", type=Path, required=True)
    observe.add_argument("--output", type=Path, required=True)
    observe.add_argument("--insights", type=Path)
    observe.add_argument("--json-errors", action="store_true")
    contract = sub.add_parser("contract")
    contract.add_argument("--facts", type=Path, required=True)
    contract.add_argument("--json-errors", action="store_true")
    render = sub.add_parser("render")
    render.add_argument("--facts", type=Path, required=True)
    render.add_argument("--insights", type=Path)
    render.add_argument("--observations", type=Path)
    render.add_argument("--no-open", action="store_true")
    render.add_argument("--retain")
    settings = sub.add_parser("settings")
    settings.add_argument("--show", action="store_true")
    settings.add_argument("--retain")
    export = sub.add_parser("export")
    export.add_argument("--run", default="latest")
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    command = args.command or "generate"
    if command == "settings":
        if args.retain is not None:
            retention = write_retention(root, args.retain)
            print(json.dumps({"retention": retention}))
            return 0
        if args.show:
            print(json.dumps({"retention": read_retention(root)}))
            return 0
        parser.error("settings requires --show or --retain")
    if command == "collect":
        args.output.write_text(json.dumps(collect(root, compare=args.compare), indent=2, ensure_ascii=False) + "\n")
        return 0
    if command == "contract":
        snapshot = json.loads(args.facts.read_text())
        if snapshot.get("schema") != SCHEMA or not isinstance(snapshot.get("source_hash"), str):
            raise ValueError(f"facts must use {SCHEMA} with a source_hash")
        print(json.dumps(observation_contract(snapshot), indent=2, ensure_ascii=False))
        return 0
    if command == "observe":
        snapshot = json.loads(args.facts.read_text())
        attach_previous_report(root, snapshot)
        args.output.write_text(json.dumps(derive_observations(snapshot, args.insights), indent=2, ensure_ascii=False) + "\n")
        return 0
    if command == "render":
        data = json.loads(args.facts.read_text())
        attach_previous_report(root, data)
        observations = validate_observations(args.observations, data) if args.observations else derive_observations(data, args.insights)
        retention = parse_retention(args.retain) if args.retain is not None else read_retention(root)
        print(render_report(root, args.runtime, data, observations, args.no_open, retention) / "index.html")
        return 0
    if command == "export":
        sanitized_export(root, args.runtime, args.run, args.output)
        print(args.output / "index.html")
        return 0
    data = collect(root, args.compare)
    observations = derive_observations(data, args.insights)
    retention = parse_retention(args.retain) if args.retain is not None else read_retention(root)
    print(render_report(root, args.runtime, data, observations, args.no_open, retention) / "index.html")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        if "--json-errors" in sys.argv:
            message = str(error)
            scope = "agent_input" if any(term in message.lower() for term in ("insights", "executive_summary", "delivery estimate")) else "facts_or_observations"
            print(json.dumps({
                "schema": DIAGNOSTIC_SCHEMA,
                "status": "error",
                "errors": [{
                    "code": "INVALID_AGENT_INPUT" if scope == "agent_input" else "INVALID_DASHBOARD_INPUT",
                    "scope": scope,
                    "message": message,
                    "retryable": True,
                    "next_action": "Correct only the named field, then rerun the same command once. Use the deterministic baseline without --insights if the correction cannot be supported by the source register.",
                }],
            }, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
