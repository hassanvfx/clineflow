# Installation and Lifecycle

ClineFlow installs a project-local durable development workflow. It does not require an account, hosted memory service, or always-running process.

## Agentic installation

Open the target project in a coding agent and ask:

```text
Please install ClineFlow by following the instructions provided at https://github.com/hassanvfx/clineflow
```

The repository is the source of truth for the current commands. The agent should inspect these instructions, show any prerequisite work, run the appropriate installer, and finish with the doctor diagnostic.

## Direct installation

From the project directory on macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/template/.clineflow/bin/install | bash
```

From the project directory in Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/hassanvfx/clineflow/main/template/.clineflow/bin/bootstrap.ps1 | iex
```

The installer stages the release manifest, downloads every declared payload, verifies its checksum, and only then writes project files.

## Prerequisites and Git initialization

ClineFlow requires Git and either `curl` or `wget`. The installer prints an operating-system-specific prerequisite plan before installing missing tools. Automated prerequisite installation requires interactive approval or a previously authorized `--yes` invocation.

Supported package-manager paths include Homebrew on macOS; `apt-get`, `dnf`, `pacman`, `zypper`, and `apk` on Linux; and `winget` on Windows.

When Git is available and the target is not already inside a work tree, the installer runs `git init`. It does not create a commit, configure identity, add a remote, or impose a branch policy. A Git initialization failure produces a warning and does not erase the installed ClineFlow files.

## What the installer adds

The installed files fall into three ownership classes:

1. **Managed runtime:** `.clineflow/` contains versioned commands, release state, checksums, diagnostics, validators, operating procedures, and agent-specific guides. Updates may replace these files after verification.
2. **User fixtures:** `knowledge/` and `docs/durable-development-methodology.md` are created only when missing. Installation, forced refresh, update, and removal preserve user-authored content.
3. **Agent instructions:** ClineFlow adds one marker-delimited workflow block to `.clinerules`, `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and `.windsurf/rules/clineflow.md`. Existing text outside that block is preserved.

The ownership record at `.clineflow/.owned-agent-files` tells the remover whether ClineFlow originally created an instruction file or merged into an existing one.

| Command | Purpose |
| --- | --- |
| `./.clineflow/bin/doctor` | Diagnose the runtime, agent instructions, Git, and knowledge bundle. |
| `./.clineflow/bin/update` | Update a current hidden-layout installation. |
| `./.clineflow/bin/uninstall` | Preview or transactionally remove managed tooling. |
| `./.clineflow/bin/validate-okf` | Validate the structural OKF bundle. |
| `./.clineflow/bin/validate-knowledge-sync` | Validate journal and five-ledger synchronization. |
| `./.clineflow/bin/dashboard` | Inspect or explicitly activate the optional Knowledge Visor. |

`validate-release` and installer/bootstrap helpers are also distributed for release and platform workflows.

## Verify the installation

```bash
./.clineflow/bin/doctor
```

The default doctor and validator use the Bash baseline. If Python and PyYAML are already available, strict YAML parsing is optional:

```bash
./.clineflow/bin/doctor --strict
./.clineflow/bin/validate-okf --strict
```

## Installation options

```bash
./.clineflow/bin/install --dry-run   # Verify and show the plan
./.clineflow/bin/install --force     # Refresh managed files and rule blocks
./.clineflow/bin/install --help
```

`--force` does not replace user-owned knowledge, documentation, or text outside ClineFlow markers.

## Update ClineFlow

Ask an installed agent:

```text
Please update ClineFlow.
```

This request authorizes the agent to read the current repository instructions and immediately use the permanent remote bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes
```

Do not run any existing local updater first; legacy updater copies can overwrite themselves before the current transactional updater takes control.

For a human-driven update without prior non-interactive authorization:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash
```

Windows PowerShell:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/hassanvfx/clineflow/main/template/.clineflow/bin/update.ps1))) -Yes
```

The updater supports identified OKF-era installations from `2026.08.15.0` onward. It stages and verifies the new release, backs up changed paths, preserves user knowledge and ambiguous legacy content, applies sequential migrations when required, verifies the result, and automatically rolls back a failed transaction. Unsupported or malformed layouts stop before mutation.

```bash
./.clineflow/bin/update --dry-run
./.clineflow/bin/update --yes
./.clineflow/bin/update --help
cat .clineflow/VERSION
```

## Remove ClineFlow

Ask an agent:

```text
Please remove ClineFlow.
```

The shared agent contract requires a preview before removal:

```bash
./.clineflow/bin/uninstall --dry-run
```

The agent explains the plan and asks for explicit confirmation. After confirmation it runs the interactive remover, or `--yes` only when that final removal has been explicitly authorized.

Removal deletes the `.clineflow/` runtime and removes the managed ClineFlow block from supported agent files. An agent file is deleted only when no user-authored content remains. Removal preserves:

- `knowledge/`, including generated dashboard reports
- `docs/journals/` legacy history
- User-authored documentation
- Text outside managed instruction markers
- Unrelated project files

The remover validates trusted ownership paths and marker structure before mutation. It quarantines changed files during the transaction and restores the previous installation after a handled failure or interruption.

```bash
./.clineflow/bin/uninstall --dry-run
./.clineflow/bin/uninstall          # Show the plan and ask for confirmation
./.clineflow/bin/uninstall --yes    # Only after removal is explicitly authorized
./.clineflow/bin/uninstall --help
```

## Troubleshooting

- Run `./.clineflow/bin/doctor` first. It reports missing prerequisites, missing knowledge files, and incomplete agent configuration without installing anything.
- If installation reports an existing ClineFlow layout, use the permanent remote updater instead of forcing a fresh install.
- If an update fails, read the reported rollback result. Recovery evidence is retained under `.clineflow/backups/` when available.
- If removal rejects malformed markers or unsafe ownership data, restore a valid managed block or inspect `.clineflow/.owned-agent-files`, then preview again.
- The optional dashboard has its own diagnostic: `./.clineflow/bin/dashboard doctor`.

See [How ClineFlow works](how-clineflow-works.md), the [OKF knowledge workflow](okf-knowledge-workflow.md), and the [release process](releasing.md) for the contracts behind these commands.
