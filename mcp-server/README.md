# ClineFlow MCP

`clineflow-mcp` is the optional, local stdio orchestrator for ClineFlow. It
accepts an explicit project root for every operation. It reads canonical
ClineFlow knowledge but stores all MCP and dashboard output only in that
project's `.clineflow-mcp/` workspace.

Use `clineflow-mcp setup --status` to inspect detected agent clients and
`clineflow-mcp setup --apply --yes` to merge only the owned `clineflow` entry.
Run `clineflow-mcp-server` from an MCP client; do not use its current directory
as a project selector.

Client setup recognizes only documented client locations. Cline uses detected
runtime settings (not `.cline/mcp.json`), and Continue uses a marker-delimited
block in `config.yaml`; an existing user-managed Continue `mcpServers` section
is reported and left unchanged. Restart or reload the client after setup.

To inspect or remove a globally installed runtime when this source checkout is
not available, use the authoritative standalone scripts. Removal always starts
with a preview and never touches project workspaces:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/mcp-server/install.sh | bash -s -- --status
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/mcp-server/uninstall.sh | bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/mcp-server/uninstall.sh | bash -s -- --yes
```
