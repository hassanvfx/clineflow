---
type: Engineering Journal
title: "Git prerequisite bootstrap"
description: "Adds OS-aware, approval-gated prerequisite handling for ClineFlow installation."
tags: [engineering, installation, git, compatibility]
status: stable
generated:
  by: clineflow/2.1.0
  at: 2026-08-28T00:00:00Z
---

# Goal

Add deterministic, fail-safe Git and downloader prerequisite handling without changing Git identity or blocking core ClineFlow installation.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-08-28 - Implementation started

The existing installer assumes Git and a downloader exist, while the diagnostic checks only whether the current directory is a Git work tree. This task adds an approval-gated OS-specific preflight and native Windows entrypoint while retaining the hidden `.clineflow/` runtime layout.

## 2026-08-28 - Completed

Added the hidden prerequisite module, Windows PowerShell bootstrap, diagnostic checks, current-path documentation, and isolated package-manager tests. All installation-owned runtime additions remain under `.clineflow/`; prerequisite failures warn and allow core setup to continue.

# Decisions

- Manage Git and one downloader (preferring curl and accepting wget) in v1.
- Do not initialize repositories or write Git identity, credentials, remotes, or global configuration.
- Prerequisite failures are warnings during installation; doctor remains non-zero until requirements are satisfied.

# Testing

- `bash -n template/.clineflow/bin/{install,update,uninstall,validate-okf,doctor,prereqs} tests/test-installation-flow.sh tests/test-prerequisites.sh tests/test-okf-validator.sh` — passed.
- `./tests/test-installation-flow.sh` — passed, including ownership-safe installation and the prerequisite suite.
- `./tests/test-okf-validator.sh`, `./template/.clineflow/bin/validate-okf`, and `git diff --check` — passed.
- `./template/.clineflow/bin/validate-okf --strict` — unavailable because optional PyYAML is not installed; dependency-free structural validation passed.
- PowerShell was not available in the local test environment; the Windows bootstrap is covered by static intent assertions.

# Open Issues

PowerShell execution must be verified on a native Windows runner in a future CI expansion.

# References

- [Fresh installer and Claude Code support](fresh-installer-claude-code.md)
- [ClineFlow tooling encapsulation](encapsulate-tooling.md)
