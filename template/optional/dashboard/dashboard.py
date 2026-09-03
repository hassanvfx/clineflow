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


def validate_insights_data(data: Any, document_ids: set[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("insights must be a JSON object")
    allowed = {"executive_summary", "project_phases", "notable_changes", "risks", "questions", "delivery_estimate"}
    if set(data) - allowed:
        raise ValueError("insights contain unsupported fields")
    for key in ("project_phases", "notable_changes", "risks", "questions"):
        for item in data.get(key, []):
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                raise ValueError(f"{key} items require text")
            refs = item.get("source_ids", [])
            if not isinstance(refs, list) or not set(refs).issubset(document_ids):
                raise ValueError(f"{key} contains an unknown source id")
    if "delivery_estimate" in data:
        validate_delivery_estimate(data["delivery_estimate"], document_ids)
    return data


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
    text = re.sub(r"^\d{4}-\d{2}-\d{2}(?:[T ][^\s]+)?\s*(?:[·—:-]\s*)?", "", text).strip()
    text = re.sub(r"^(?:event|summary|change)\s*:\s*", "", text, flags=re.IGNORECASE)
    if not text:
        return "Recorded event"
    natural_breaks = re.split(r"(?<=[.!?])\s+|\s+\(|\s+—\s+|\s+[-:]\s+", text, maxsplit=1)
    candidate = natural_breaks[0].strip() or text
    if len(candidate) <= limit:
        return candidate
    clipped = candidate[:limit + 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{clipped or candidate[:limit]}…"


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
    return re.sub(r"\s+", " ", str(value).replace("_", " ")).strip().title()


def guided_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Build the document-guided view before HTML rendering; raw source stays available separately."""
    structured = doc.get("structured")
    sections: list[dict[str, Any]] = []
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
    document_ids = {item["id"] for item in snapshot["documents"]}
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
    validate_insights_payload = {key: data.get(key) for key in (
        "executive_summary", "project_phases", "notable_changes", "risks", "questions", "delivery_estimate"
    ) if key in data}
    validate_insights_data(validate_insights_payload, document_ids)
    return data


def collect(root: Path, compare: str = "previous") -> dict[str, Any]:
    ledgers, documents = collect_knowledge(root)
    commits = collect_commits(root)
    events = [normalize_event(item) for item in (ledgers.get("clineflow_timeline") or {}).get("events", [])]
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
        {**display_record(item, "Decision needed", [document_id_for_path["knowledge/clineflow_specification.yml"]] if document_id_for_path.get("knowledge/clineflow_specification.yml") else []), "why": "The specification still leaves this choice open.", "next": "Choose an owner and record the decision."}
        for item in specification.get("open_questions") or []
    ] + [
        {**display_record(item, "Proof gap", [document_id_for_path["knowledge/clineflow_verification.yml"]] if document_id_for_path.get("knowledge/clineflow_verification.yml") else []), "why": "The implementation has no recorded verification for this point yet.", "next": "Run or record the missing evidence."}
        for item in verification.get("open_verification") or []
    ]
    constraints = [
        {**display_record(item, "Constraint", [document_id_for_path["knowledge/clineflow_specification.yml"]] if document_id_for_path.get("knowledge/clineflow_specification.yml") else []), "why": "This boundary shapes the implementation decision.", "next": "Keep the constraint visible while deciding."}
        for item in specification.get("constraints") or []
    ]
    active_goal = observation_text(next(iter(goals.get("active_goals") or []), ""))
    headline = active_goal or (latest.get("title") if latest else "Build the first durable project record")
    onboarding = {
        "empty": not documents,
        "title": "Start the story with one deliberate record" if not documents else "Strengthen the next useful signal",
        "text": "Create the five ClineFlow ledgers, then record one goal, one next move, and one timeline event." if not documents else "Add a clear goal, next recommended move, and verification note to turn sparse context into a useful narrative.",
    }
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
    return json_safe({
        "schema": PRESENTATION_SCHEMA,
        "generated_at": data.get("run_at"),
        "source": {"snapshot_schema": data.get("schema"), "source_hash": data.get("source_hash"), "observation_schema": observations.get("schema")},
        "report": {"run_id": data.get("run_id"), "git": data.get("git") or {}, "retention": data.get("retention")},
        "now": {
            "headline": headline,
            "summary": observations.get("executive_summary") or session.get("latest_change") or onboarding["text"],
            "intent": active_goal or observation_text(session.get("next_recommended_step") or "No active goal recorded."),
            "next_move": observation_text(session.get("next_recommended_step") or "Capture the next deliberate move in the knowledge base."),
            "latest_activity": latest,
            "latest_verification": latest_verification,
            "unresolved_count": len(unresolved),
        },
        "story": observations.get("project_story") or {},
        "audiences": observations.get("audiences") or {},
        "timeline": timeline,
        "documents": documents,
        "unresolved": unresolved,
        "decisions": constraints + unresolved,
        "onboarding": onboarding,
        "agentic_loop": agentic_loop,
        "project_pulse": project_pulse,
        "delivery_estimate": delivery_estimate,
        "evidence": [display_record(item, "Verification evidence", ledger_source("knowledge/clineflow_verification.yml")) for item in verification.get("evidence") or verification.get("acceptance_criteria") or []],
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
    page = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><meta http-equiv=\"Content-Security-Policy\" content=\"{csp}\"><title>ClineFlow Knowledge Visor</title><style>{font_css}{custom_css}</style></head><body><a class=\"skip\" href=\"#main\">Skip to knowledge</a><div id=\"app\"></div><script>{assets['echarts.min.js']}</script><script>{assets['gsap.min.js']}</script><script id=\"clineflow-data\" type=\"application/json\">{safe_json_for_script(data)}</script><script id=\"clineflow-observations\" type=\"application/json\">{safe_json_for_script(observations)}</script><script id=\"clineflow-presentation\" type=\"application/json\">{safe_json_for_script(presentation)}</script><script>{custom_js}</script></body></html>"""
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
    data["retention"] = retention
    presentation = build_presentation(data, observations, str(root.resolve()))
    page, asset_manifest = build_page(runtime, data, observations, presentation)
    report_manifest = {
        "schema": SCHEMA,
        "generator_version": next((line.split("=", 1)[1] for line in (runtime / ".active").read_text().splitlines() if line.startswith("component_version=")), "unknown"),
        "run_id": data["run_id"], "generated_at": data["run_at"],
        "source_hash": data["source_hash"], "baseline_run": data.get("baseline_run"),
        "git": data["git"], "assets": asset_manifest,
        "observations": {"schema": observations["schema"], "generator": observations["generator"]},
        "presentation": {"schema": presentation["schema"]}, "retention": retention,
        "browser_network": "disabled", "warnings": [],
    }
    (temporary / "index.html").write_text(page)
    (temporary / "manifest.json").write_text(json.dumps(report_manifest, indent=2, ensure_ascii=False) + "\n")
    (temporary / "snapshot.json").write_text(json.dumps(json_safe(data), indent=2, ensure_ascii=False) + "\n")
    (temporary / "observations.json").write_text(json.dumps(json_safe(observations), indent=2, ensure_ascii=False) + "\n")
    (temporary / "presentation.json").write_text(json.dumps(presentation, indent=2, ensure_ascii=False) + "\n")
    for path in temporary.iterdir():
        try:
            path.chmod(0o600)
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
    if command == "observe":
        snapshot = json.loads(args.facts.read_text())
        args.output.write_text(json.dumps(derive_observations(snapshot, args.insights), indent=2, ensure_ascii=False) + "\n")
        return 0
    if command == "render":
        data = json.loads(args.facts.read_text())
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
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
