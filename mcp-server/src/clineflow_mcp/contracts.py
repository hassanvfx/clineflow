"""Versioned public contract constants for the ClineFlow MCP server."""

from __future__ import annotations

from . import __version__

SERVER_NAME = "clineflow"
WORKSPACE = ".clineflow-mcp"
COMPATIBILITY = {
    "mcp_version": __version__,
    "clineflow_release": ">=2026.08.15.0",
    "clineflow_schema": [2, 3],
    "okf_schema": "0.2",
}
ENDPOINTS = {
    "resources": ["clineflow://contract/latest", "clineflow://schema/okf/v0.2", "clineflow://endpoints"],
    "tools": [
        "clineflow_consult", "clineflow_install", "clineflow_update", "clineflow_remove",
        "clineflow_healthcheck", "clineflow_fix", "clineflow_dashboard_generate",
        "clineflow_dashboard_settings", "clineflow_dashboard_export",
    ],
}
OKF_SCHEMA = {
    "name": "ClineFlow Open Knowledge Format bundle",
    "version": "0.2",
    "root": "knowledge/",
    "required_bundle_files": [
        "index.md", "log.md", "clineflow_specification.yml", "clineflow_verification.yml",
        "clineflow_goals.yml", "clineflow_last_session.yml", "clineflow_timeline.yml",
    ],
    "journals": {
        "path": "knowledge/journals/<topic>/<stream>--<tenant>.md",
        "type": "Engineering Journal",
        "required_frontmatter": ["type", "status", "author.id", "clineflow.schema", "clineflow.topic", "clineflow.stream"],
    },
    "updates": {
        "path": "knowledge/updates/<topic>/<uuid>--<tenant>.yml",
        "schema": 3,
        "immutable": True,
        "required_reviews": ["specification", "verification", "goals", "last_session", "timeline"],
    },
    "ownership": {"canonical_knowledge": "read_only", "mcp_dashboard_workspace": WORKSPACE},
}
CLIENT_REGISTRY = {
    "codex": {"format": "toml", "target": "~/.codex/config.toml"},
    "claude-code": {"format": "json-mcp", "target": "~/.claude.json"},
    "copilot": {"format": "json-servers", "target": "~/.copilot/mcp-config.json"},
    "cline": {"format": "json-mcp", "target": "detected documented Cline runtime settings"},
    "cursor": {"format": "json-mcp", "target": "~/.cursor/mcp.json"},
    "windsurf": {"format": "json-mcp", "target": "~/.codeium/windsurf/mcp.json"},
    "continue": {"format": "marker-delimited YAML", "target": "~/.continue/config.yaml"},
}
RESULT_ENVELOPE = {
    "required": ["status"],
    "optional": ["message", "recommendation", "checks", "actions", "returncode", "stdout", "stderr"],
    "errors": ["invalid_root", "authorization_required", "unsupported", "action_required", "busy", "failed"],
}


def contract() -> dict[str, object]:
    return {"server": SERVER_NAME, "compatibility": COMPATIBILITY, "endpoints": ENDPOINTS,
            "okf_schema": OKF_SCHEMA, "client_registry": CLIENT_REGISTRY, "result_envelope": RESULT_ENVELOPE,
            "workspace": {"path": WORKSPACE, "canonical_knowledge": "read_only"}}
