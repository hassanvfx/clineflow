---
type: Engineering Journal
title: "Old-install update rescue path"
description: "Makes the permanent remote updater discoverable when stale installed instructions cannot interpret the natural-language update request."
tags: [engineering, documentation, updates]
status: draft
generated:
  by: clineflow/2.0.0
  at: 2026-09-03T20:34:40Z
---

# Goal

Give users of old ClineFlow installations a copyable, authoritative update command that does not depend on the installed agent rules or bundled updater being current.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-03 20:22 - Added the rescue path

Promoted the permanent macOS/Linux remote bootstrap in the README under an explicit old-install heading, added its PowerShell equivalent and final-version check, and expanded the lifecycle guide with project-root, downloader, network, verification, and rollback guidance. Added release-contract rejection coverage and prepared release `2026.09.03.21`; schema `1` remains valid because no persistent format changes.

## 2026-09-03 20:30 - Repaired the failing Windows lifecycle check

The public workflow API showed that the Linux certification job passed at commit `1f03ac5`, while `windows-lifecycle-smoke` failed during the Git Bash installation step. Moved the Windows smoke project out of the checked-out repository and into `RUNNER_TEMP`, normalized all Bash/Windows path boundaries with `cygpath`, let the installer exercise its own Git initialization, passed the resolved location to PowerShell and removal steps, upgraded checkout to its Node 24 generation, and changed the README badge to the workflow-file URL scoped to `main`.

## 2026-09-03 20:34 - Fixed checksum drift at Windows checkout

The signed-in hosted log identified the exact failure: `ERROR: checksum mismatch for .clineflow/JOURNAL_TEMPLATE.md`. The manifest contains LF-byte checksums, while Windows checkout was allowed to materialize Markdown and other text fixtures as CRLF. Added explicit LF attributes for every managed text extension and the extensionless dashboard manifest, plus release-contract coverage for the critical attribute rules. This preserves identical verified payload bytes on Linux, macOS, and Windows.

# Decisions

- The natural-language prompt stays the easiest default for current installations.
- The raw remote bootstrap is the compatibility escape hatch when stale agent instructions fail to recognize or correctly execute that prompt.
- The rescue command must run from the intended project root and must supersede any updater bundled in the old installation.
- Documentation must distinguish a network or unsupported-layout failure from a successful update and require checking `.clineflow/VERSION` afterward.

# Testing

- `./template/.clineflow/bin/validate-release` — passed for release `2026.09.03.21`, migration schema `1`.
- `./tests/test-release-contract.sh` — passed, including missing-heading and incomplete-command rejection cases.
- `./template/.clineflow/bin/validate-okf` — passed.
- `./template/.clineflow/bin/validate-knowledge-sync` — passed at the shared completion timestamp.
- `./tests/certify-release.sh` — passed the complete installation, dashboard, migration, uninstall, release, OKF, synchronization, and whitespace matrix.
- `git diff --check` — passed.
- The hosted Windows workflow result is pending the commit and push that can exercise `windows-latest`.

# Open Issues

- The existing deferred Knowledge Visor screenshot remains unrelated and blocked by the local browser capture policy.
- The badge will remain red until the corrected workflow is committed, pushed, and completes successfully on GitHub's Windows runner.

# References

- [Installation and lifecycle](../../docs/installation-and-lifecycle.md)
- [Durable development methodology](../../docs/durable-development-methodology.md)
- [Universal update migrations](universal-update-migrations.md)
