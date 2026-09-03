---
type: Engineering Journal
title: "Universal update and migration system"
description: "Builds the transactional OKF-era updater and the release contract that keeps future migrations current."
tags: [engineering, installation, updates, migrations, releases]
status: stable
generated:
  by: clineflow/2026.09.03.0
  at: 2026-09-03T07:40:19Z
---

# Goal

Provide one stable ClineFlow update command that migrates every OKF-era layout from `2026.08.15.0` onward, preserves user-authored content, rolls back failed upgrades, and makes future installation-affecting changes prove their upgrade path.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-02 - Implementation started

Repository history contains three installed runtime layouts: root commands, `clineflow/bin/`, and `.clineflow/bin/`. The historical root updater URL was removed during encapsulation, and current version identifiers disagree. The approved implementation restores that entrypoint, introduces a manifest-driven transactional updater, and standardizes date-based releases.

## 2026-09-03 - Implementation completed

Added the permanent bootstrap, manifest-driven fresh installer, transactional updater, PowerShell wrapper, installed release state, enhanced doctor, release-contract validator, historical migration fixtures, rollback tests, CI gates, contributor documentation, and canonical agent update prompt. The updater fingerprints stock legacy files, preserves ambiguous content, creates missing OKF fixtures only, and retains transaction evidence under `.clineflow/backups/`.

## 2026-09-03 - Lifecycle certification started

The installer and updater already have broad matrix coverage, but the uninstaller still trusts ownership-manifest paths, deletes a file recorded as owned even after user edits, and can leave a partial removal after failure. This slice will make uninstall confirmation-gated and transactional, reject unsafe ownership data before mutation, preserve edited agent files by removing only their managed block, and add one release-certification command required by CI.

## 2026-09-03 - Lifecycle certification completed

Added `tests/certify-release.sh` as the required release gate, made release validation enforce its install/update/uninstall coverage and CI wiring, and added an adversarial removal suite. The uninstaller now validates a fixed ownership-path allowlist and well-formed markers before mutation, displays a plan, requires confirmation unless `--yes` is supplied, quarantines the runtime, preserves user text outside managed blocks, and restores the pre-removal state after failures and handled signals. Release `2026.09.03.0` keeps schema `1`; existing installations receive the behavior through the managed manifest without a data migration.

# Decisions

- Support automatic migration for OKF-era installations beginning with `2026.08.15.0`; reject older or unidentified layouts without mutation.
- Treat “Please update ClineFlow” as authorization for an agent to consult the authoritative repository and run the updater with `--yes`.
- Preserve user knowledge, legacy journals, authored documentation, retired reference artifacts, and ambiguous legacy files.
- Back up every changed path and automatically roll back failed migrations.
- Require installation-affecting features to update or explicitly validate the migration contract.
- Keep migration schema `1` because lifecycle certification changes managed runtime behavior without changing installed persistent formats; existing installations receive it through the release manifest.

# Testing

Lifecycle proof:

- A single certification command runs syntax, release-contract, install, update/migration, uninstall, prerequisite, and OKF suites.
- Uninstall dry-run and rejected confirmation are byte-for-byte non-mutating.
- Unsafe ownership paths, malformed markers, and symlinked runtime layouts abort before changes.
- Edited agent files retain user text while exact owned files are removed.
- Injected removal failure and termination restore the complete pre-uninstall state.
- Knowledge, legacy journals, unrelated files, and retired reference artifacts survive removal unchanged.
- `./tests/certify-release.sh` passed the complete release, installation, historical migration, transactional removal, release-contract rejection, prerequisite, OKF, syntax, and whitespace gate.
- `./tests/certify-release.sh --against HEAD` passed after the final version, manifest, PowerShell wrapper, and CI changes.
- The same `./tests/certify-release.sh --against HEAD` gate passed again immediately before commit.
- The first certification run correctly rejected a hard-coded prior release in the migration test; the assertion now derives the expected version from the release manifest, and the complete rerun passed.
- CI now includes a native Windows smoke job for installation through Git Bash, the PowerShell updater wrapper, doctor, and transactional removal; execution evidence will be available when GitHub Actions runs.

- `bash -n` passed for every runtime and test shell script.
- `./template/.clineflow/bin/validate-release` passed for release `2026.09.02.0`, schema `1`.
- `./tests/test-installation-flow.sh` passed.
- `./tests/test-update-migrations.sh` passed root, visible, hidden, partial, idempotency, preservation, confirmation, integrity, unsupported-layout, and rollback scenarios.
- `./tests/test-release-contract.sh` passed its positive case and rejection cases for unmanaged files, stale checksums, missing prompts, missing migrations, and absent version bumps.
- `./tests/test-okf-validator.sh`, `./template/.clineflow/bin/validate-okf`, and `git diff --check` passed.
- `./template/.clineflow/bin/validate-okf --strict` could not run because optional PyYAML is not installed in this environment; dependency-free validation passed.

# Open Issues

The PowerShell update wrapper is configured for native Windows CI but has not executed in this local macOS environment.

# References

- [Tooling encapsulation](encapsulate-tooling.md)
- [Native OKF adoption](okf-adoption.md)
- [Durable development indexes](durable-development-master-indexes.md)
