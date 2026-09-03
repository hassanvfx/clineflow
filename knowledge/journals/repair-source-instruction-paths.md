---
type: Engineering Journal
title: "Repair source instruction paths"
description: "Corrects source-repository agent instructions that referenced installed paths absent from the distribution checkout."
tags: [engineering, documentation, agents, validation]
status: stable
generated:
  by: clineflow/2026.09.03.1
  at: 2026-09-03T09:30:27Z
---

# Goal

Ensure every repository-native agent instruction points to files and commands that exist in the ClineFlow distribution checkout, while preserving `.clineflow/` paths in instructions installed into downstream projects.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-03 08:40 UTC - Audit and repair completed

Confirmed that the root `AGENTS.md` referenced a Codex guide and validators under a nonexistent root `.clineflow/` directory. The root `.clinerules` also referenced the retired root-level validator and omitted the current five-ledger contract. Updated both source-repository instruction files to use `template/.clineflow/`, synchronized the legacy `template/.clinerules` compatibility copy with the canonical installed rules, and added release-contract regression assertions.

# Decisions

- Keep installed-project instructions unchanged because `.clineflow/` is their correct runtime location.
- Use `template/.clineflow/` only in source-repository agent instructions.
- Keep migration schema `1` and release version `2026.09.03.1` because no manifest-managed payload, installed persistent format, ownership behavior, or migration behavior changed.
- Retain `template/.clinerules` for documented backward compatibility, but eliminate its behavioral drift by matching the canonical rules template.

# Testing

- `tests/test-release-contract.sh` checks the source Codex guide and validator paths and requires the compatibility Cline template to match canonical shared rules.
- `./tests/test-release-contract.sh` passed its current contract and source-instruction assertions plus all release rejection cases.
- `./template/.clineflow/bin/validate-okf` passed structural OKF validation.
- `./template/.clineflow/bin/validate-knowledge-sync` passed at the shared task timestamp.
- `./tests/certify-release.sh` passed the complete installation, historical migration, rollback, uninstall safety, release-contract, OKF, knowledge synchronization, syntax, and whitespace gate for release `2026.09.03.1`.
- `git diff --check` passed.

# Open Issues

None.

# References

- [Universal five-ledger synchronization](universal-five-ledger-synchronization.md)
- [ClineFlow tooling encapsulation](encapsulate-tooling.md)
- [Source Codex instructions](../../AGENTS.md)
- [Installable Codex guide](../../template/.clineflow/WORKING_WITH_CODEX.md)
