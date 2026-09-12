#!/usr/bin/env python3
"""Freeze the current Ad Crush operational knowledge into a dashboard fixture.

The fixture freezes the sibling's generated ledger projections together with
the committed active journals.  The projections are intentionally ignored by
the sibling repository, so a Git commit cannot name their exact bytes; the
fixture manifest instead records their content hash and capture timestamp.
Immutable update records remain represented through those projections and are
not copied into a large, duplicated test archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


LEDGERS = (
    "clineflow_specification.yml",
    "clineflow_verification.yml",
    "clineflow_goals.yml",
    "clineflow_last_session.yml",
    "clineflow_timeline.yml",
)


def git_bytes(source: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source), "show", f"{commit}:{path}"])


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def frontmatter(raw: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", raw, flags=re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    for key in ("title", "description", "status"):
        field = re.search(rf"^{key}:\s*[\"']?(.*?)[\"']?\s*$", match.group(1), flags=re.MULTILINE)
        if field:
            result[key] = field.group(1).strip()
    timestamp = re.search(r"^\s+at:\s*(\S+)", match.group(1), flags=re.MULTILINE)
    if timestamp:
        result["generated_at"] = timestamp.group(1)
    topic = re.search(r"^\s+topic:\s*(\S+)", match.group(1), flags=re.MULTILINE)
    if topic:
        result["topic"] = topic.group(1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "--verify", f"{args.commit}^{{commit}}"], text=True).strip()
    listed = subprocess.check_output(["git", "-C", str(source), "ls-tree", "-r", "--name-only", commit, "knowledge"], text=True).splitlines()
    journal_paths = sorted(path for path in listed if path.startswith("knowledge/journals/") and path.endswith(".md") and not path.endswith(("index.md", "TASK_TEMPLATE.md")))
    paths = [f"knowledge/{ledger}" for ledger in LEDGERS] + journal_paths
    documents: list[dict[str, Any]] = []
    ledgers: dict[str, Any] = {}
    manifest_sources: list[dict[str, str]] = []
    for path in paths:
        # ClineFlow projects intentionally ignore generated clineflow_*.yml
        # projections. Capture those concrete current bytes, while journals
        # still come from the named sibling commit.
        payload = (source / path).read_bytes() if Path(path).name in LEDGERS else git_bytes(source, commit, path)
        raw = payload.decode("utf-8")
        digest = sha256(payload)
        manifest_sources.append({"path": path, "sha256": digest})
        name = Path(path).name
        if name in LEDGERS:
            structured = json.loads(raw)
            ledgers[Path(name).stem] = structured
            documents.append({
                "id": digest[:16], "path": path, "title": Path(name).stem.removeprefix("clineflow_").replace("_", " ").title(),
                "description": f"Frozen Ad Crush {Path(name).stem.removeprefix('clineflow_').replace('_', ' ')} ledger.",
                "kind": "ledger", "structured": structured, "raw": raw,
                "yaml": {"valid": True, "normalized": json.dumps(structured, ensure_ascii=False, indent=2) + "\n"}, "hash": digest,
            })
            continue
        metadata = frontmatter(raw)
        documents.append({
            "id": digest[:16], "path": path, "title": metadata.get("title", Path(path).stem),
            "description": metadata.get("description", "Frozen active Ad Crush engineering journal."),
            "kind": "journal", "status": metadata.get("status", ""), "generated_at": metadata.get("generated_at"),
            "clineflow": {"topic": metadata.get("topic", "unclassified")}, "raw": raw, "html": "", "hash": digest,
        })
    timeline = ledgers.get("clineflow_timeline") or {}
    run_at = timeline.get("generated_at") or "2026-09-11T00:00:00Z"
    source_hash = sha256("".join(item["hash"] for item in documents).encode())
    facts = {
        "schema": "clineflow-dashboard/v1", "run_at": run_at, "run_id": "adcrush-frozen-20260911",
        "source_hash": source_hash, "git": {"head": commit, "branch": "frozen-adcrush", "dirty": False},
        "ledgers": ledgers, "documents": documents, "events": timeline.get("events", []), "commits": [], "runs": [], "usage": [],
        "current_change": {"files": 0, "net": 0}, "current_footprint": {"knowledge_files": len(documents)},
        "drift": {"added": [], "changed": [], "removed": []}, "baseline_run": f"git:{commit[:8]}",
        "frozen_source": {"project": "sibling project ad-crush", "commit": commit, "scope": "five projected ledgers, active journals, and normalized timeline; immutable update archive is represented by the projections", "source_count": len(documents)},
        "report_identity": {
            "project": {
                "title": "Ad Crush",
                "description": "Frozen operational knowledge sample from sibling project ad-crush.",
                "source_kind": "frozen-sibling-sample",
            },
            "capture": {
                "captured_at": run_at,
                "source_origin": "sibling project ad-crush",
                "kind": "frozen-fixture",
            },
            "coverage": {
                "from": min((event.get("at") for event in timeline.get("events", []) if event.get("at")), default=None),
                "to": max((event.get("at") for event in timeline.get("events", []) if event.get("at")), default=None),
                "included": ["five captured ledger projections", "committed active journals", "normalized timeline"],
                "limit": "Ledger projections were captured from the sibling working tree; journals are bound to the named baseline commit. Immutable update records are not duplicated in this fixture.",
            },
            "revision": {"value": commit, "short": commit[:8], "label": "Frozen baseline revision", "kind": "baseline"},
            "latest_commit": {
                "value": None, "short": None, "summary": None, "committed_at": None,
                "label": "Latest captured commit unavailable", "kind": "unavailable",
            },
            "condition": {
                "state": "frozen-snapshot", "label": "Frozen source snapshot",
                "detail": "The fixture is a fixed report input; it does not inherit the host repository working-tree condition.",
            },
        },
    }
    manifest = {"schema": "clineflow-dashboard-fixture/v1", "project": "sibling project ad-crush", "commit": commit, "projection_mode": "captured ignored working-tree projections", "facts_source_hash": source_hash, "scope": facts["frozen_source"]["scope"], "sources": manifest_sources}
    args.output.mkdir(parents=True, exist_ok=True)
    args.output.joinpath("facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n")
    args.output.joinpath("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
