"""MCP-owned Knowledge Visor operations with the established renderer."""

from __future__ import annotations

from pathlib import Path
from contextlib import contextmanager
from threading import RLock
from typing import Any
from uuid import uuid4

from .dashboard_runtime import engine
from .dashboard_runtime.runtime import ensure_runtime
from .workspace import ensure

_CONFIGURATION_LOCK = RLock()


def _boundary(root: Path) -> Path:
    return ensure(root) / "dashboard"


@contextmanager
def _configured(root: Path):
    """Temporarily bind the legacy renderer to one project's workspace.

    The extracted renderer still accepts its destination through a module-level
    compatibility variable.  MCP requests can be concurrent, so serialize that
    binding and always restore it before another root is served.
    """
    with _CONFIGURATION_LOCK:
        previous = engine.DASHBOARD_ROOT
        engine.DASHBOARD_ROOT = _boundary(root)
        try:
            yield ensure_runtime()
        finally:
            engine.DASHBOARD_ROOT = previous


def generate(root: Path, insights: dict[str, Any] | None = None) -> dict[str, object]:
    """Render the full Knowledge Visor without opening a browser."""
    with _configured(root) as runtime:
        facts = engine.collect(root, compare="previous")
        observations = engine.derive_observations(facts)
        if insights:
            # The MCP accepts the established insights contract, validates every
            # source reference against this exact facts snapshot, then merges only
            # validated fields into the deterministic observation model.
            document_ids = {item["id"] for item in facts["documents"]}
            validated = engine.validate_insights_data(insights, document_ids)
            observations.update(validated)
            observations["generator"] = {"kind": "provided", "name": "invoking-agent", "version": "1"}
        report = engine.render_report(root, runtime, facts, observations, no_open=True,
                                      retention=engine.read_retention(root))
        return {"status": "generated", "run_id": report.name, "report": str(report / "index.html"),
                "workspace": str(_boundary(root).parent)}


def settings(root: Path, retention: int | str | None = None) -> dict[str, object]:
    with _configured(root):
        value = engine.write_retention(root, retention) if retention is not None else engine.read_retention(root)
        return {"status": "settings", "retention": value, "path": str(_boundary(root) / "settings.json")}


def export(root: Path, run_id: str, authorized: bool) -> dict[str, object]:
    if not authorized:
        return {"status": "authorization_required", "message": "Ask the user to authorize a sanitized dashboard export."}
    with _configured(root) as runtime:
        destination = ensure(root) / "exports" / f"{run_id}-{uuid4().hex[:8]}"
        engine.sanitized_export(root, runtime, run_id, destination)
        return {"status": "exported", "path": str(destination), "sanitized": True}
