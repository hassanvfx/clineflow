import asyncio
import json
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from clineflow_mcp import __version__
from clineflow_mcp.contracts import contract
from clineflow_mcp.server import okf_schema


def test_stdio_exposes_contract_resources() -> None:
    async def exercise() -> None:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "clineflow_mcp.server"],
        )
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                resources = await session.list_resources()
        assert {str(item.uri) for item in resources.resources} >= {
            "clineflow://contract/latest",
            "clineflow://schema/okf/v0.2",
            "clineflow://endpoints",
        }

    asyncio.run(exercise())


def test_contract_declares_every_supported_client_adapter() -> None:
    assert set(contract()["client_registry"]) == {
        "codex", "claude-code", "copilot", "cline", "cursor", "windsurf", "continue",
    }


def test_okf_schema_resource_declares_bundle_and_immutable_record_contract() -> None:
    schema = json.loads(okf_schema())
    assert schema["version"] == "0.2"
    assert "clineflow_specification.yml" in schema["required_bundle_files"]
    assert schema["updates"]["immutable"] is True
    assert schema["ownership"]["mcp_dashboard_workspace"] == ".clineflow-mcp"


def test_server_launcher_reports_the_package_version_without_starting_stdio() -> None:
    result = subprocess.run([sys.executable, "-m", "clineflow_mcp.server", "--version"], text=True,
                            capture_output=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip() == __version__
    assert result.stderr == ""
