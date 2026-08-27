---
type: Engineering Journal
title: "Fresh installer and Claude Code support"
description: "Repairs the fresh-install exit path and adds ownership-safe Claude Code instructions."
tags: [engineering, installation, compatibility, claude-code]
status: stable
generated:
  by: clineflow/2.1.0
  at: 2026-08-27T01:48:30Z
---

# Goal

Allow ClineFlow to install cleanly in fresh repositories and provide ownership-safe project instructions for Claude Code.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-08-27 - Implementation started

The installer aborted on a fresh repository because `migrate_legacy_runtime` returned the failed legacy-directory test under `set -e`. The repair makes that no-op path return success. Claude Code is added as a managed `CLAUDE.md` target, reusing the existing marker and ownership manifest behavior.

## 2026-08-27 - Completed

Added Claude Code to the installer, documentation, ownership-aware uninstall coverage, and diagnostics. Fresh projects now bypass absent legacy runtime directories successfully without requiring a workaround.

# Decisions

- Treat Claude Code as a first-class supported agent and use its root `CLAUDE.md` project-instructions file.
- Keep backward compatibility by allowing `doctor` to accept either `AGENTS.md` or `CLAUDE.md`.

# Testing

- `bash -n template/.clineflow/bin/* tests/test-installation-flow.sh tests/test-okf-validator.sh` — passed.
- `./tests/test-installation-flow.sh` — passed; verifies fresh installation, safe `CLAUDE.md` merge and refresh, Claude-only diagnostic support, and ownership-aware uninstall.
- `./tests/test-okf-validator.sh` — passed.
- `./template/.clineflow/bin/validate-okf` and `git diff --check` — passed.
- The source checkout's `./template/.clineflow/bin/doctor` intentionally reports a missing installed validator because this repository is the distribution template; the installed-fixture doctor passes in the installation-flow suite.
- `./template/.clineflow/bin/validate-okf --strict` — unavailable because optional PyYAML is not installed; the dependency-free structural validator passed.

# Open Issues

None.

# References

- [ClineFlow tooling encapsulation](encapsulate-tooling.md)
- [Anthropic Claude Code memory documentation](https://docs.anthropic.com/en/docs/claude-code/memory)
