from pathlib import Path
from hashlib import sha256
import json

from clineflow_mcp.lifecycle import compatibility, consult, fix, health, run
from clineflow_mcp.workspace import ensure


def test_consult_and_repair_do_not_rewrite_knowledge(tmp_path: Path) -> None:
    (tmp_path / "knowledge").mkdir()
    journal = tmp_path / "knowledge" / "journal.md"
    journal.write_text("user authored\n", encoding="utf-8")
    assert consult(tmp_path)["compatibility"]["status"] == "not_installed"
    assert fix(tmp_path)["status"] == "plan"
    assert journal.read_text(encoding="utf-8") == "user authored\n"
    assert fix(tmp_path, apply=True, authorized=True)["status"] == "repaired"
    assert health(tmp_path)["checks"]["workspace"]["status"] == "ready"


def test_unsupported_schema_cannot_mutate(tmp_path: Path) -> None:
    runtime = tmp_path / ".clineflow/bin"
    runtime.mkdir(parents=True)
    (tmp_path / ".clineflow/state").write_text("release_version=2099.01.01.0\nmigration_schema=99\n", encoding="utf-8")
    command = runtime / "update"
    command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    command.chmod(0o755)
    assert compatibility(tmp_path)["status"] == "unsupported"
    assert run(tmp_path, "update", True)["status"] == "unsupported"


def test_fix_requires_authorization_and_refuses_corrupt_dashboard(tmp_path: Path) -> None:
    (tmp_path / "knowledge").mkdir()
    workspace = ensure(tmp_path)
    dashboard = workspace / "dashboard"
    (dashboard / "runs").rmdir()
    dashboard.rmdir()
    dashboard.write_text("user data", encoding="utf-8")
    plan = fix(tmp_path)
    assert plan["status"] == "plan"
    assert fix(tmp_path, apply=True, authorized=True)["status"] == "action_required"
    assert dashboard.read_text(encoding="utf-8") == "user data"


def test_consult_reports_offline_latest_without_creating_workspace(tmp_path: Path) -> None:
    before = list(tmp_path.iterdir())
    response = consult(tmp_path, latest=True)
    assert response["latest_contract"]["provenance"] == "offline"
    assert list(tmp_path.iterdir()) == before


def test_consult_accepts_only_checksum_verified_latest_cache(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    state.mkdir()
    payload = {"schema": "0.2"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (state / "latest-contract.json").write_text(json.dumps({"contract": payload, "sha256": sha256(canonical).hexdigest(),
                                                               "fetched_at": "2026-09-07T00:00:00Z"}), encoding="utf-8")
    monkeypatch.setenv("CLINEFLOW_MCP_HOME", str(state))
    assert consult(tmp_path, latest=True)["latest_contract"]["provenance"] == "cached"
    (state / "latest-contract.json").write_text('{"contract": {}, "sha256": "wrong"}', encoding="utf-8")
    assert consult(tmp_path, latest=True)["latest_contract"]["verified"] is False


def test_remove_preview_without_runtime_is_actionable_not_an_exception(tmp_path: Path) -> None:
    assert run(tmp_path, "remove")["status"] == "action_required"
