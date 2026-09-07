import os
import subprocess
import threading
from pathlib import Path
from hashlib import sha256

import pytest

from clineflow_mcp import dashboard
from clineflow_mcp.dashboard_runtime import engine
from clineflow_mcp.workspace import WorkspaceError, ensure, operation_lock, root_path


def test_workspace_only_writes_managed_boundary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CLINEFLOW_MCP_HOME", str(tmp_path / "global-runtime"))
    assets = tmp_path / "assets"
    assets.mkdir()
    lines = []
    for name in ("echarts.min.js", "gsap.min.js", "space-grotesk.woff2", "ibm-plex-mono-400.woff2", "ibm-plex-mono-500.woff2"):
        value = b"fixture asset"
        source_asset = assets / name
        source_asset.write_bytes(value)
        kind = "javascript" if name.endswith(".js") else "font"
        lines.append(f"asset|{kind}|{name}|test|{source_asset.as_uri()}|-|{sha256(value).hexdigest()}|test")
    manifest = tmp_path / "component-manifest"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setenv("CLINEFLOW_MCP_DASHBOARD_MANIFEST", str(manifest))
    (tmp_path / "knowledge").mkdir()
    source = tmp_path / "knowledge" / "note.md"
    source.write_text("# Durable context\n", encoding="utf-8")
    original = source.read_bytes()
    result = dashboard.generate(tmp_path)
    assert Path(result["report"]).is_file()
    assert source.read_bytes() == original
    assert (tmp_path / ".clineflow-mcp/dashboard/runs").is_dir()


def test_root_rejects_relative_and_symlink(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceError): root_path("relative")
    linked = tmp_path.parent / "clineflow-mcp-link"
    linked.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(WorkspaceError): root_path(str(linked))
    nested = linked / "nested"
    (tmp_path / "nested").mkdir()
    with pytest.raises(WorkspaceError): root_path(str(nested))


def test_stale_operation_lock_is_recovered_but_live_lock_is_preserved(tmp_path: Path) -> None:
    lock = ensure(tmp_path) / "locks" / "operation.lock"
    lock.write_text("999999999\n", encoding="utf-8")
    with operation_lock(tmp_path):
        assert lock.is_file()
    lock.write_text(f"{os.getpid()}\n", encoding="utf-8")
    with pytest.raises(WorkspaceError):
        with operation_lock(tmp_path):
            pass


def test_dashboard_root_binding_is_serialized_and_restored(tmp_path: Path, monkeypatch) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    one.mkdir(); two.mkdir()
    monkeypatch.setattr(dashboard, "ensure_runtime", lambda: tmp_path / "runtime")
    original = engine.DASHBOARD_ROOT
    entered, release, second_entered = threading.Event(), threading.Event(), threading.Event()

    def first() -> None:
        with dashboard._configured(one):
            assert engine.DASHBOARD_ROOT == one / ".clineflow-mcp/dashboard"
            entered.set()
            release.wait(timeout=2)

    def second() -> None:
        with dashboard._configured(two):
            assert engine.DASHBOARD_ROOT == two / ".clineflow-mcp/dashboard"
            second_entered.set()

    first_thread = threading.Thread(target=first)
    second_thread = threading.Thread(target=second)
    first_thread.start(); assert entered.wait(timeout=2)
    second_thread.start()
    assert not second_entered.wait(timeout=0.1)
    release.set()
    first_thread.join(timeout=2); second_thread.join(timeout=2)
    assert second_entered.is_set()
    assert engine.DASHBOARD_ROOT == original


def test_malformed_workspace_exclude_markers_abort_before_workspace_creation(tmp_path: Path) -> None:
    subprocess.run(["git", "-C", str(tmp_path), "init", "-q"], check=True)
    exclude = tmp_path / ".git/info/exclude"
    before = "# BEGIN CLINEFLOW MCP WORKSPACE\n/user-content\n"
    exclude.write_text(before, encoding="utf-8")
    with pytest.raises(WorkspaceError):
        ensure(tmp_path)
    assert exclude.read_text(encoding="utf-8") == before
    assert not (tmp_path / ".clineflow-mcp").exists()
