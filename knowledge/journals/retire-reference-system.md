---
type: Engineering Journal
title: "Retire reference-repository system"
description: "Removes ClineFlow's symlink-based reference feature and adopts sibling-project guidance."
tags: [engineering, maintenance, documentation]
status: stable
generated:
  by: clineflow/2.0.0
  at: 2026-08-25T04:28:57Z
---

# Goal

Remove the shipped symlink-based reference system without affecting ClineFlow's normal installation, knowledge, validation, or agent workflows. Recommend sibling projects under a common parent instead.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-08-24 - Initial context

The reference feature is isolated to its setup script, local config, installer/update/uninstaller branches, documentation, and dedicated end-to-end test phases. Historical material in `docs/journals/` remains read-only.

## 2026-08-24 - Completed

Removed the shipped setup script, configuration example, and reference documentation. Installer, updater, uninstaller, generated agent rules, and tests now exclude the retired system while preserving the ordinary workflow and the generic VS Code workspace ignore rule.

# Decisions

- Hard-remove the feature from new releases without automatically modifying existing installations.
- Retain the generic `*.code-workspace` ignore rule to avoid unrelated VS Code Git noise.
- Use “sibling project `<foldername>`” as the documented cross-project convention.

# Testing

- `bash -n install.sh update.sh uninstall.sh create-remaining-files.sh tests/test-installation-flow.sh` — passed.
- `./tests/test-installation-flow.sh` — passed (13 tests), including fresh-install absence checks for retired artifacts.
- `./validate-okf` — passed.
- `git diff --check` — passed.
- `./validate-okf --strict` remains unavailable because optional PyYAML is not installed; the installation suite verifies the expected optional-validator fallback.

# Open Issues

None.

# References

- [Legacy symlink safety journal](../../docs/journals/symlink-git-safety.md)
