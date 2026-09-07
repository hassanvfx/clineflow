"""Prepare the global, checksum-verified dashboard renderer runtime."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import urllib.request
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent


def _state_home() -> Path:
    configured = os.environ.get("CLINEFLOW_MCP_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "clineflow-mcp"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download(url: str, destination: Path, expected: str) -> None:
    temporary = destination.with_name(f".{destination.name}.download")
    try:
        with urllib.request.urlopen(url, timeout=30) as response, temporary.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        if _digest(temporary) != expected:
            raise RuntimeError(f"dashboard asset checksum mismatch: {destination.name}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_runtime() -> Path:
    """Materialize renderer code/assets globally, never inside a project."""
    runtime = _state_home() / "dashboard-runtime"
    assets = runtime / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    manifest_source = Path(os.environ.get("CLINEFLOW_MCP_DASHBOARD_MANIFEST", PACKAGE / "component-manifest"))
    for name in ("engine.py", "engine.py.lock", "visor.css", "visor.js", "THIRD_PARTY_LICENSES.md"):
        source, destination = PACKAGE / name, runtime / name
        if not destination.exists() or _digest(destination) != _digest(source):
            shutil.copy2(source, destination)
    manifest_destination = runtime / "component-manifest"
    if not manifest_destination.exists() or _digest(manifest_destination) != _digest(manifest_source):
        shutil.copy2(manifest_source, manifest_destination)
    asset_manifest = []
    for line in manifest_source.read_text(encoding="utf-8").splitlines():
        parts = line.split("|")
        if len(parts) != 8 or parts[0] != "asset":
            continue
        _, _kind, name, _version, primary, fallback, expected, _license = parts
        destination = assets / name
        asset_manifest.append({"name": name, "kind": _kind, "version": _version, "sha256": expected,
                               "license": _license, "primary": primary,
                               "fallback": None if fallback == "-" else fallback})
        if destination.exists() and _digest(destination) == expected:
            continue
        try:
            _download(primary, destination, expected)
        except OSError:
            if fallback == "-":
                raise
            _download(fallback, destination, expected)
    (runtime / "asset-manifest.json").write_text(
        json.dumps({"component_version": "2026.09.03.18", "assets": asset_manifest}, indent=2) + "\n",
        encoding="utf-8",
    )
    (runtime / ".active").write_text("component_version=2026.09.03.18\n", encoding="utf-8")
    return runtime
