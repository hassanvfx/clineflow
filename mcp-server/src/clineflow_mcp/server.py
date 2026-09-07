"""ClineFlow's stdio MCP surface; stdout is reserved for MCP protocol traffic."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __version__, dashboard, lifecycle
from .contracts import ENDPOINTS, OKF_SCHEMA, contract
from .workspace import WorkspaceError, root_path

mcp = FastMCP("ClineFlow MCP", instructions=(
    "ClineFlow MCP is local and opt-in. Every project operation requires an explicit absolute root. "
    "Read canonical knowledge, but write only under .clineflow-mcp/. Always preview removal and repair before apply."
))


def _root(value: str) -> Path | dict[str, object]:
    try:
        return root_path(value)
    except WorkspaceError as error:
        return {"status": "invalid_root", "message": str(error)}


@mcp.resource("clineflow://contract/latest")
def latest_contract() -> str:
    return json.dumps(contract(), indent=2)


@mcp.resource("clineflow://schema/okf/v0.2")
def okf_schema() -> str:
    return json.dumps(OKF_SCHEMA, indent=2)


@mcp.resource("clineflow://endpoints")
def endpoint_catalog() -> str:
    return json.dumps(ENDPOINTS, indent=2)


@mcp.tool()
def clineflow_consult(root: str, latest: bool = False) -> dict[str, object]:
    """Inspect compatibility and installation state without changing a project."""
    selected = _root(root)
    return selected if isinstance(selected, dict) else lifecycle.consult(selected, latest)


@mcp.tool()
def clineflow_healthcheck(root: str) -> dict[str, object]:
    """Diagnose ClineFlow, knowledge, workspace, and dashboard readiness."""
    selected = _root(root)
    return selected if isinstance(selected, dict) else lifecycle.health(selected)


@mcp.tool()
def clineflow_install(root: str, authorized: bool = False) -> dict[str, object]:
    """Run the existing ClineFlow installer after caller authorization."""
    selected = _root(root)
    if isinstance(selected, dict): return selected
    return {"status": "authorization_required"} if not authorized else lifecycle.run(selected, "install", True)


@mcp.tool()
def clineflow_update(root: str, authorized: bool = False) -> dict[str, object]:
    """Run the existing transactional ClineFlow updater after authorization."""
    selected = _root(root)
    if isinstance(selected, dict): return selected
    return {"status": "authorization_required"} if not authorized else lifecycle.run(selected, "update", True)


@mcp.tool()
def clineflow_remove(root: str, authorized: bool = False) -> dict[str, object]:
    """Return removal preview first; apply only with explicit authorization."""
    selected = _root(root)
    return selected if isinstance(selected, dict) else lifecycle.run(selected, "remove", authorized)


@mcp.tool()
def clineflow_fix(root: str, apply: bool = False, authorized: bool = False) -> dict[str, object]:
    """Plan repair first; only apply managed/reconstructible repairs when authorized."""
    selected = _root(root)
    return selected if isinstance(selected, dict) else lifecycle.fix(selected, apply, authorized)


@mcp.tool()
def clineflow_dashboard_generate(root: str, insights: dict[str, Any] | None = None) -> dict[str, object]:
    """Generate an MCP-owned dashboard report without opening a browser."""
    selected = _root(root)
    try:
        return selected if isinstance(selected, dict) else dashboard.generate(selected, insights)
    except (OSError, ValueError) as error:
        return {"status": "failed", "message": str(error)}


@mcp.tool()
def clineflow_dashboard_settings(root: str, retention: int | str | None = None) -> dict[str, object]:
    """Read or set MCP-owned dashboard retention settings."""
    selected = _root(root)
    try:
        return selected if isinstance(selected, dict) else dashboard.settings(selected, retention)
    except (OSError, ValueError) as error:
        return {"status": "failed", "message": str(error)}


@mcp.tool()
def clineflow_dashboard_export(root: str, run_id: str, authorized: bool = False) -> dict[str, object]:
    """Create an explicitly authorized sanitized dashboard export."""
    selected = _root(root)
    try:
        return selected if isinstance(selected, dict) else dashboard.export(selected, run_id, authorized)
    except (OSError, ValueError) as error:
        return {"status": "failed", "message": str(error)}


def main() -> None:
    if sys.argv[1:] == ["--version"]:
        print(__version__)
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
