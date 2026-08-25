---
type: Engineering Journal
title: "Encapsulate ClineFlow tooling"
description: "Moves ClineFlow-owned tooling into clineflow while preserving user-owned agent configuration and knowledge."
tags: [engineering, installation, compatibility]
status: stable
generated:
  by: clineflow/2.0.0
  at: 2026-08-25T04:42:00Z
---

# Goal

Move ClineFlow tooling into `clineflow/` and preserve existing agent configuration and knowledge during install, update, and uninstall.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-08-24 - Initial context

Root tooling currently includes the installer, updater, uninstaller, validator, diagnostic, and version file. Ordinary installation preserves existing agent configuration, but `--force` overwrites it; the refactor introduces an ownership manifest to make config handling safe.

## 2026-08-24 - Completed

Moved the ClineFlow executable interface to `template/.clineflow/bin/`, which installs to `.clineflow/bin/`. The installer merges one marker-delimited ClineFlow block into existing native agent configurations and records whether it owns the full file or only that block. Force refreshes only ClineFlow tooling and the managed block; uninstall removes only manifest-owned files or blocks.

# Decisions

- New public tooling lives under `template/.clineflow/bin/` and installs to `.clineflow/bin/`.
- Root script entry points are intentionally removed.
- `--force` refreshes only ClineFlow-owned files; agent configs and knowledge are always preserved.

# Testing

- `bash -n template/.clineflow/bin/* tests/test-installation-flow.sh tests/test-okf-validator.sh` — passed.
- `./tests/test-installation-flow.sh` — passed; verifies normal and forced installation preserve existing agent config and knowledge, then verifies ownership-aware uninstall.
- `./tests/test-okf-validator.sh` — passed.
- `./template/.clineflow/bin/validate-okf` and `git diff --check` — passed.

# Open Issues

None.

# References

- [Agent-agnostic support history](../../docs/journals/agent-agnostic-support.md)
