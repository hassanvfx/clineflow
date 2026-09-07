"""Narrow, merge-safe global MCP client registration.

Only documented client locations are considered. In particular, Cline uses
visible runtime settings rather than a project-local fallback, and Continue's
YAML is touched only through one marker-delimited owned block.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import __version__
from .contracts import SERVER_NAME

CONTINUE_BEGIN = "# BEGIN CLINEFLOW MCP MANAGED ENTRY"
CONTINUE_END = "# END CLINEFLOW MCP MANAGED ENTRY"
CLINE_STORAGE = "saoudrizwan.claude-dev"


@dataclass(frozen=True)
class Target:
    client: str
    path: Path
    format: str
    marker: Path
    reload: str


def _reload(client: str) -> str:
    if client == "cline":
        return "Restart Cline or run Developer: Reload Window so Cline discovers the ClineFlow MCP server."
    return f"Restart or reload {client} to discover the ClineFlow MCP server."


def _cline_host_path(host_root: Path, host: str) -> Target:
    path = host_root / host / "User" / "globalStorage" / CLINE_STORAGE / "settings" / "cline_mcp_settings.json"
    return Target("cline", path, "json-mcp", path.parent.parent, _reload("cline"))


def _cline_targets(home: Path, system: str) -> list[Target]:
    if system == "Darwin":
        base = home / "Library" / "Application Support"
    elif system == "Windows":
        base = home / "AppData" / "Roaming"
    else:
        base = home / ".config"
    candidates = [_cline_host_path(base, host) for host in ("Code", "Code - Insiders", "Cursor", "Windsurf")]
    candidates.extend((
        Target("cline", home / ".cline" / "data" / "settings" / "cline_mcp_settings.json", "json-mcp",
               home / ".cline" / "data" / "settings", _reload("cline")),
        # This legacy path is never created. It is considered only when it
        # already exists so an exact owned entry can be preserved or removed.
        Target("cline", home / ".cline" / "mcp.json", "json-mcp", home / ".cline" / "mcp.json", _reload("cline")),
    ))
    return [target for target in candidates if target.path.exists() or target.marker.is_dir()]


def targets(home: Path | None = None, system: str | None = None) -> list[Target]:
    """Return fixed recognized targets only; never scan arbitrary client paths."""
    home = home or Path.home()
    system = system or platform.system()
    result = [
        Target("codex", home / ".codex" / "config.toml", "toml", home / ".codex", _reload("codex")),
        Target("claude-code", home / ".claude.json", "json-mcp", home / ".claude", _reload("claude-code")),
        Target("copilot", home / ".copilot" / "mcp-config.json", "json-servers", home / ".copilot", _reload("copilot")),
        Target("cursor", home / ".cursor" / "mcp.json", "json-mcp", home / ".cursor", _reload("cursor")),
        Target("windsurf", home / ".codeium" / "windsurf" / "mcp.json", "json-mcp", home / ".codeium" / "windsurf", _reload("windsurf")),
    ]
    result.extend(_cline_targets(home, system))
    continue_dir = home / ".continue"
    if (continue_dir / "config.yaml").exists():
        result.append(Target("continue", continue_dir / "config.yaml", "continue", continue_dir, _reload("continue")))
    elif (continue_dir / "config.json").exists():
        result.append(Target("continue", continue_dir / "config.json", "json-mcp", continue_dir, _reload("continue")))
    elif continue_dir.is_dir():
        result.append(Target("continue", continue_dir / "config.yaml", "continue", continue_dir, _reload("continue")))
    return result


def command() -> str:
    value = os.environ.get("CLINEFLOW_MCP_COMMAND")
    # An explicit override is authoritative.  Falling back after it fails
    # could register a different runtime than the installer just validated.
    candidates = [Path(value)] if value else []
    if not value:
        found = shutil.which("clineflow-mcp-server")
        if found:
            candidates.append(Path(found))
    for candidate in candidates:
        if not candidate.is_absolute() or not candidate.is_file() or not os.access(candidate, os.X_OK):
            continue
        try:
            result = subprocess.run([str(candidate), "--version"], text=True, capture_output=True,
                                    check=False, timeout=3)
        except OSError:
            continue
        if result.returncode == 0 and result.stdout.strip() == __version__:
            return str(candidate.resolve())
    return ""


def server_entry() -> dict[str, Any]:
    value = command()
    if not value:
        raise ValueError("a verified absolute clineflow-mcp-server launcher is required")
    return {"command": value, "args": []}


def _read(target: Target) -> dict[str, Any] | str:
    if not target.path.exists():
        return "" if target.format == "continue" else {}
    text = target.path.read_text(encoding="utf-8")
    if target.format == "toml":
        return tomllib.loads(text)
    if target.format == "continue":
        return text
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("configuration root must be an object")
    return value


def _json_key(target: Target) -> str:
    return "servers" if target.format == "json-servers" else "mcpServers"


def _continue_content(entry: dict[str, Any]) -> str:
    return (f"{CONTINUE_BEGIN}\n"
            "mcpServers:\n"
            f"  - name: {SERVER_NAME}\n"
            f"    command: {json.dumps(entry['command'])}\n"
            "    args: []\n"
            f"{CONTINUE_END}\n")


def _continue_entry(text: str) -> str | None:
    match = re.search(rf"(?ms)^{re.escape(CONTINUE_BEGIN)}\n.*?^{re.escape(CONTINUE_END)}\n?", text)
    return match.group(0) if match else None


def _entry(data: dict[str, Any] | str, target: Target) -> Any:
    if target.format == "continue":
        assert isinstance(data, str)
        block = _continue_entry(data)
        if block is not None:
            return server_entry() if block == _continue_content(server_entry()) else {"managed_block": "changed"}
        if CONTINUE_BEGIN in data or CONTINUE_END in data or re.search(r"(?m)^mcpServers:\s*$", data):
            return {"unmanaged": "continue_mcp_servers"}
        return None
    if target.format == "toml":
        assert isinstance(data, dict)
        servers = data.get("mcp_servers", {})
        if not isinstance(servers, dict):
            raise ValueError("mcp_servers must be a TOML table")
        return servers.get(SERVER_NAME)
    assert isinstance(data, dict)
    servers = data.get(_json_key(target), {})
    if not isinstance(servers, dict):
        raise ValueError("MCP server section must be an object")
    return servers.get(SERVER_NAME)


def _render(data: dict[str, Any] | str, target: Target) -> str:
    expected = server_entry()
    current = _entry(data, target)
    if current not in (None, expected):
        raise ValueError("existing configuration is user-managed")
    if target.format == "continue":
        assert isinstance(data, str)
        separator = "" if not data or data.endswith("\n") else "\n"
        return data + separator + _continue_content(expected)
    if target.format == "toml":
        prior = target.path.read_text(encoding="utf-8") if target.path.exists() else ""
        return prior.rstrip() + "\n\n[mcp_servers.clineflow]\ncommand = %s\nargs = []\n" % json.dumps(expected["command"])
    assert isinstance(data, dict)
    merged = dict(data)
    key = _json_key(target)
    servers = dict(merged.get(key, {}))
    servers[SERVER_NAME] = expected
    merged[key] = servers
    return json.dumps(merged, indent=2, sort_keys=True) + "\n"


def plan(home: Path | None = None, system: str | None = None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for target in targets(home, system):
        detected = target.marker.exists() or target.path.exists()
        base = {"client": target.client, "path": str(target.path), "format": target.format, "reload": target.reload}
        if not detected:
            result.append({**base, "action": "not_detected"})
            continue
        try:
            expected = server_entry()
            current = _entry(_read(target), target)
            if current is None:
                action, reason = "add", "detected client has no ClineFlow entry"
            elif current == expected:
                action, reason = "unchanged", "owned entry already matches"
            else:
                action, reason = "skip", "existing ClineFlow entry is user-managed"
        except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
            action, reason = "skip", "configuration is malformed or unsupported"
            if "verified absolute" in str(error):
                reason = "a verified absolute ClineFlow MCP launcher is unavailable"
        result.append({**base, "action": action, "reason": reason})
    return result


def _atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else 0o600
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _target_map(home: Path | None, system: str | None) -> dict[str, Target]:
    return {str(target.path): target for target in targets(home, system)}


def apply(home: Path | None = None, system: str | None = None) -> list[dict[str, str]]:
    server_entry()
    result = plan(home, system)
    by_path = _target_map(home, system)
    for item in result:
        if item["action"] != "add":
            continue
        target = by_path[item["path"]]
        _atomic(target.path, _render(_read(target), target))
        item["validation"] = "passed" if _entry(_read(target), target) == server_entry() else "failed"
    return result


def _remove_toml(text: str) -> str:
    return re.sub(r"(?ms)^\[mcp_servers\.clineflow\].*?(?=^\[|\Z)", "", text).rstrip() + "\n"


def remove(home: Path | None = None, apply_changes: bool = False, system: str | None = None) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    expected = server_entry()
    for target in targets(home, system):
        if not target.path.exists():
            continue
        try:
            data, entry = _read(target), _entry(_read(target), target)
        except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError):
            result.append({"client": target.client, "path": str(target.path), "format": target.format,
                           "action": "skip", "reason": "malformed", "reload": target.reload})
            continue
        if entry != expected:
            continue
        result.append({"client": target.client, "path": str(target.path), "format": target.format,
                       "action": "remove", "reload": target.reload})
        if not apply_changes:
            continue
        if target.format == "continue":
            assert isinstance(data, str)
            _atomic(target.path, re.sub(rf"(?ms)^{re.escape(CONTINUE_BEGIN)}\n.*?^{re.escape(CONTINUE_END)}\n?", "", data).rstrip() + "\n")
        elif target.format == "toml":
            _atomic(target.path, _remove_toml(target.path.read_text(encoding="utf-8")))
        else:
            assert isinstance(data, dict)
            key = _json_key(target)
            servers = dict(data[key])
            servers.pop(SERVER_NAME, None)
            data[key] = servers
            _atomic(target.path, json.dumps(data, indent=2, sort_keys=True) + "\n")
    return result
