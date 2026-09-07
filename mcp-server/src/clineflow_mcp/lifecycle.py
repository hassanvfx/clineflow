"""Thin adapters to ClineFlow's installed lifecycle commands."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from hashlib import sha256
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .contracts import COMPATIBILITY
from .workspace import WorkspaceError, ensure, operation_lock, status as workspace_status


def compatibility(root: Path) -> dict[str, object]:
    state = root / ".clineflow/state"
    if not state.is_file():
        return {"status": "not_installed", "can_mutate": True}
    values = dict(line.split("=", 1) for line in state.read_text(encoding="utf-8").splitlines() if "=" in line)
    try:
        schema = int(values.get("migration_schema", "-1"))
    except ValueError:
        schema = -1
    supported = schema in COMPATIBILITY["clineflow_schema"]
    return {"status": "compatible" if supported else "unsupported", "release": values.get("release_version"),
            "schema": schema, "can_mutate": supported,
            "recommendation": None if supported else "Update the MCP server, restart the client, then update ClineFlow."}


def consult(root: Path, latest: bool = False) -> dict[str, object]:
    latest_contract = {"provenance": "bundled", "verified": True, "status": "available"}
    if latest:
        # Network retrieval is deliberately not implicit. A client may place a
        # verified latest-contract response in the global managed cache; absent
        # that evidence the server is candid that it is operating offline.
        cache = _global_state_home() / "latest-contract.json"
        cached = _verified_contract_cache(cache)
        if cached is not None:
            latest_contract = {"provenance": "cached", "verified": True, "status": "available", "path": str(cache),
                               "fetched_at": cached.get("fetched_at")}
        elif cache.is_file():
            latest_contract = {"provenance": "cached", "verified": False, "status": "unavailable", "path": str(cache),
                               "recommendation": "Refresh the latest-contract cache; its integrity checksum is invalid."}
        else:
            latest_contract = {"provenance": "offline", "verified": False, "status": "unavailable",
                               "recommendation": "Reconnect and refresh the MCP release metadata before relying on latest."}
    return {"status": "consultation", "root": str(root), "compatibility": compatibility(root), "workspace": str(root / ".clineflow-mcp"),
            "latest_contract": latest_contract}


def health(root: Path) -> dict[str, object]:
    checks: dict[str, object] = {"installation": compatibility(root), "knowledge": _knowledge_health(root),
                                 "agent_rules": _agent_rules_health(root), "dashboard": _dashboard_health(root)}
    try:
        checks["workspace"] = workspace_status(root)
    except WorkspaceError as error:
        checks["workspace"] = {"status": "corrupt", "message": str(error)}
    doctor = root / ".clineflow/bin/doctor"
    checks["doctor"] = _read_only_command(root, doctor, []) if doctor.is_file() else {"status": "unavailable"}
    checks["okf"] = _validator_health(root, "validate-okf")
    checks["knowledge_synchronization"] = _validator_health(root, "validate-knowledge-sync")
    bad = {"unsupported", "corrupt", "missing", "failed"}
    statuses = [value.get("status") for value in checks.values() if isinstance(value, dict)]
    return {"status": "attention_required" if any(value in bad for value in statuses) else "healthy", "checks": checks}


def run(root: Path, operation: str, authorized: bool = False) -> dict[str, object]:
    if operation == "remove" and not authorized:
        command = root / ".clineflow/bin/uninstall"
        if not command.is_file():
            return {"status": "action_required", "message": ".clineflow/bin/uninstall is unavailable; ClineFlow is not installed."}
        return _execute(root, command, ["--dry-run"], "remove_preview", mutate=False)
    if operation == "remove" and authorized:
        command, args = root / ".clineflow/bin/uninstall", ["--yes"]
    elif operation == "update":
        command, args = root / ".clineflow/bin/update", ["--yes"]
    elif operation == "install":
        command, args = root / ".clineflow/bin/install", ["--yes"]
    else:
        raise ValueError("unsupported lifecycle operation")
    if operation == "install" and not command.is_file():
        return _bootstrap_install(root)
    if not command.is_file():
        return {"status": "action_required", "message": f"{command.relative_to(root)} is unavailable; use the ClineFlow bootstrap installer first."}
    return _execute(root, command, args, operation, mutate=True)


def fix(root: Path, apply: bool = False, authorized: bool = False) -> dict[str, object]:
    report = health(root)
    checks = report["checks"]
    plan: list[dict[str, object]] = []
    workspace_check = checks["workspace"]
    if isinstance(workspace_check, dict) and workspace_check.get("status") == "missing":
        plan.append({"action": "create_workspace", "allowed": True, "owned": True})
    if isinstance(checks["dashboard"], dict) and checks["dashboard"].get("status") == "corrupt":
        plan.append({"action": "preserve_dashboard_diagnostics", "allowed": True, "owned": True})
    if not apply:
        return {"status": "plan", "actions": plan,
                "refuses": ["malformed journals", "immutable update records", "user-managed agent rules"]}
    if not authorized:
        return {"status": "authorization_required", "plan": plan}
    if any(action["action"] == "preserve_dashboard_diagnostics" for action in plan):
        return {"status": "action_required", "plan": plan,
                "message": "Dashboard data is corrupt and was not overwritten; inspect it before a reconstructive repair."}
    if any(action["action"] == "create_workspace" for action in plan):
        ensure(root)
    return {"status": "repaired", "actions": plan}


def _execute(root: Path, command: Path, args: list[str], operation: str, mutate: bool) -> dict[str, object]:
    if mutate and not compatibility(root).get("can_mutate", True):
        return {"status": "unsupported", "recommendation": compatibility(root).get("recommendation")}
    if mutate:
        try:
            with operation_lock(root):
                result = subprocess.run([str(command), *args], cwd=root, text=True, capture_output=True, check=False)
                receipt = ensure(root) / "operations" / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}.json"
                receipt.write_text(json.dumps({"operation": operation, "returncode": result.returncode, "stdout": result.stdout,
                                               "stderr": result.stderr}, indent=2) + "\n", encoding="utf-8")
        except WorkspaceError as error:
            return {"status": "busy", "message": str(error)}
    else:
        result = subprocess.run([str(command), *args], cwd=root, text=True, capture_output=True, check=False)
    return {"status": "completed" if result.returncode == 0 else "failed", "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def _global_state_home() -> Path:
    configured = os.environ.get("CLINEFLOW_MCP_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "clineflow-mcp"


def _read_only_command(root: Path, command: Path, args: list[str]) -> dict[str, object]:
    result = subprocess.run([str(command), *args], cwd=root, text=True, capture_output=True, check=False)
    return {"status": "ready" if result.returncode == 0 else "failed", "returncode": result.returncode,
            "stderr": result.stderr[-1000:]}


def _validator_health(root: Path, name: str) -> dict[str, object]:
    command = root / ".clineflow/bin" / name
    return _read_only_command(root, command, []) if command.is_file() else {"status": "unavailable"}


def _verified_contract_cache(path: Path) -> dict[str, object] | None:
    """Return a locally cached contract only when its canonical checksum matches."""
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        contract = cached["contract"]
        expected = cached["sha256"]
        payload = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if isinstance(contract, dict) and isinstance(expected, str) and sha256(payload).hexdigest() == expected:
            return cached
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def _knowledge_health(root: Path) -> dict[str, object]:
    knowledge = root / "knowledge"
    if not knowledge.is_dir():
        return {"status": "missing"}
    required = ("index.md", "log.md", "clineflow_specification.yml", "clineflow_verification.yml",
                "clineflow_goals.yml", "clineflow_last_session.yml", "clineflow_timeline.yml")
    missing = [name for name in required if not (knowledge / name).is_file()]
    return {"status": "missing" if missing else "ready", "missing": missing}


def _agent_rules_health(root: Path) -> dict[str, object]:
    marker = "<!-- BEGIN CLINEFLOW OKF RULES -->"
    candidates = ("AGENTS.md", "CLAUDE.md", ".clinerules", ".github/copilot-instructions.md", ".windsurf/rules/clineflow.md")
    present = [name for name in candidates if (root / name).is_file()]
    managed = [name for name in present if marker in (root / name).read_text(encoding="utf-8", errors="replace")]
    return {"status": "ready" if managed else "missing", "present": present, "managed": managed}


def _dashboard_health(root: Path) -> dict[str, object]:
    dashboard = root / ".clineflow-mcp/dashboard"
    if not dashboard.exists():
        return {"status": "not_generated"}
    if not dashboard.is_dir() or dashboard.is_symlink():
        return {"status": "corrupt"}
    runs = dashboard / "runs"
    if runs.exists() and not runs.is_dir():
        return {"status": "corrupt"}
    return {"status": "ready", "runs": len(list(runs.iterdir())) if runs.is_dir() else 0}


def _bootstrap_install(root: Path) -> dict[str, object]:
    """Use the authoritative bootstrap only when an authorized install lacks a local adapter."""
    url = os.environ.get(
        "CLINEFLOW_INSTALL_URL",
        "https://raw.githubusercontent.com/hassanvfx/clineflow/main/template/.clineflow/bin/install",
    )
    if not url.startswith("https://"):
        return {"status": "action_required", "message": "CLINEFLOW_INSTALL_URL must be HTTPS"}
    if not shutil.which("curl"):
        return {"status": "action_required", "message": "curl is required for the authoritative ClineFlow bootstrap"}
    fetched = subprocess.run(["curl", "-fsSL", url], text=True, capture_output=True, check=False)
    if fetched.returncode != 0:
        return {"status": "failed", "returncode": fetched.returncode, "stderr": fetched.stderr}
    result = subprocess.run(["bash", "-s", "--", "--yes"], cwd=root, input=fetched.stdout,
                            text=True, capture_output=True, check=False)
    receipt_root = ensure(root) / "operations"
    receipt = receipt_root / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}.json"
    receipt.write_text(json.dumps({"operation": "install", "bootstrap": url, "returncode": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n", encoding="utf-8")
    return {"status": "completed" if result.returncode == 0 else "failed", "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}
