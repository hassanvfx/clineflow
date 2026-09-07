from pathlib import Path

import json
import pytest

from clineflow_mcp import __version__
from clineflow_mcp.clients import apply, plan, remove, targets


def _launcher(path: Path) -> Path:
    path.write_text(f"#!/bin/sh\nprintf '{__version__}\\n'\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_setup_only_detects_existing_client_homes(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".codex").mkdir()
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    planned = plan(tmp_path)
    assert next(item for item in planned if item["client"] == "codex")["action"] == "add"
    assert next(item for item in planned if item["client"] == "cursor")["action"] == "not_detected"
    applied = apply(tmp_path)
    assert next(item for item in applied if item["client"] == "codex")["validation"] == "passed"


def test_conflicting_entry_is_never_owned_or_replaced(tmp_path: Path, monkeypatch) -> None:
    codex = tmp_path / ".codex"
    codex.mkdir()
    (codex / "config.toml").write_text("[mcp_servers.clineflow]\ncommand = '/user/launcher'\n", encoding="utf-8")
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    assert next(item for item in plan(tmp_path) if item["client"] == "codex")["action"] == "skip"


def test_unverified_launcher_is_never_written_to_a_detected_client(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".codex").mkdir()
    launcher = tmp_path / "clineflow-mcp-server"
    launcher.write_text("#!/bin/sh\nprintf 'not-clineflow'\n", encoding="utf-8")
    launcher.chmod(0o755)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    item = next(row for row in plan(tmp_path) if row["client"] == "codex")
    assert item["action"] == "skip"
    assert "verified absolute" in item["reason"]
    assert not (tmp_path / ".codex/config.toml").exists()


def test_every_supported_client_is_added_idempotently_and_exactly_removed(tmp_path: Path, monkeypatch) -> None:
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    # Cline only exposes an active target after its runtime settings directory
    # exists; a legacy `.cline/mcp.json` must not be created by setup.
    (tmp_path / ".cline/data/settings").mkdir(parents=True)
    all_targets = targets(tmp_path)
    for target in all_targets:
        target.marker.mkdir(parents=True, exist_ok=True)
        if target.format.startswith("json"):
            target.path.write_text(json.dumps({"preserve": {"client": target.client}}), encoding="utf-8")
        elif target.format == "continue":
            target.path.write_text("name: preserve\n", encoding="utf-8")
        else:
            target.path.write_text("model = 'preserve'\n", encoding="utf-8")
    applied = apply(tmp_path)
    assert {item["client"] for item in applied if item["action"] == "add"} == {target.client for target in all_targets}
    assert all(item["validation"] == "passed" for item in applied if item["action"] == "add")
    repeated = plan(tmp_path)
    assert all(item["action"] == "unchanged" for item in repeated)
    removed = remove(tmp_path, apply_changes=True)
    assert {item["client"] for item in removed} == {target.client for target in all_targets}
    for target in all_targets:
        text = target.path.read_text(encoding="utf-8")
        assert "clineflow" not in text
        assert "preserve" in text


def test_cline_runtime_and_continue_yaml_are_narrowly_merged(tmp_path: Path, monkeypatch) -> None:
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    runtime = (tmp_path / "Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings")
    runtime.mkdir(parents=True)
    continue_dir = tmp_path / ".continue"
    continue_dir.mkdir()
    ctargets = [target for target in targets(tmp_path, system="Darwin") if target.client == "cline"]
    assert len(ctargets) == 1
    assert ctargets[0].path.name == "cline_mcp_settings.json"
    applied = apply(tmp_path, system="Darwin")
    cline_result = next(item for item in applied if item["client"] == "cline")
    assert cline_result["validation"] == "passed"
    payload = json.loads(ctargets[0].path.read_text(encoding="utf-8"))
    assert payload["mcpServers"]["clineflow"]["command"] == str(launcher)
    assert not (tmp_path / ".cline/mcp.json").exists()
    continue_path = continue_dir / "config.yaml"
    assert "# BEGIN CLINEFLOW MCP MANAGED ENTRY" in continue_path.read_text(encoding="utf-8")
    removed = remove(tmp_path, apply_changes=True, system="Darwin")
    assert {item["path"] for item in removed} == {str(ctargets[0].path), str(continue_path)}
    assert "clineflow" not in ctargets[0].path.read_text(encoding="utf-8")
    assert "# BEGIN CLINEFLOW MCP MANAGED ENTRY" not in continue_path.read_text(encoding="utf-8")


def test_continue_existing_unmanaged_mcp_servers_is_preserved(tmp_path: Path, monkeypatch) -> None:
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    config = tmp_path / ".continue/config.yaml"
    config.parent.mkdir()
    config.write_text("mcpServers:\n  - name: user-server\n", encoding="utf-8")
    item = next(row for row in plan(tmp_path) if row["client"] == "continue")
    assert item["action"] == "skip"
    assert config.read_text(encoding="utf-8") == "mcpServers:\n  - name: user-server\n"


@pytest.mark.parametrize(
    ("system", "base"),
    [("Darwin", "Library/Application Support"), ("Linux", ".config"), ("Windows", "AppData/Roaming")],
)
def test_cline_known_platform_runtime_paths_are_detected_without_scanning(tmp_path: Path, monkeypatch, system: str, base: str) -> None:
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    settings = tmp_path / base / "Code/User/globalStorage/saoudrizwan.claude-dev/settings"
    settings.mkdir(parents=True)
    found = [target for target in targets(tmp_path, system=system) if target.client == "cline"]
    assert [target.path for target in found] == [settings / "cline_mcp_settings.json"]
    assert next(item for item in plan(tmp_path, system=system) if item["client"] == "cline")["action"] == "add"


def test_malformed_detected_client_is_skipped_without_writing(tmp_path: Path, monkeypatch) -> None:
    launcher = tmp_path / "clineflow-mcp-server"
    _launcher(launcher)
    monkeypatch.setenv("CLINEFLOW_MCP_COMMAND", str(launcher))
    cursor = next(target for target in targets(tmp_path) if target.client == "cursor")
    cursor.marker.mkdir(parents=True)
    cursor.path.write_text("not valid JSON", encoding="utf-8")
    before = cursor.path.read_text(encoding="utf-8")
    item = next(entry for entry in plan(tmp_path) if entry["client"] == "cursor")
    assert item["action"] == "skip"
    assert cursor.path.read_text(encoding="utf-8") == before
