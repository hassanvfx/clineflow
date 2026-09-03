---
type: Engineering Journal
title: "Numeric release-version ordering"
description: "Repairs lexicographic release ordering in the transactional ClineFlow updater."
tags: [engineering, updates, releases, regression]
status: stable
generated:
  by: clineflow/2026.09.03.13
  at: 2026-09-03T18:09:03Z
---

# Goal

Ensure date-based ClineFlow versions compare each of their four numeric segments, so a valid upgrade from `2026.09.03.5` to `2026.09.03.10` is never mistaken for a downgrade.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-03 18:07 UTC - Comparator repair completed

The updater used Bash string operators for both the minimum-supported version and downgrade checks. That made the patch segment lexicographic: `.5` sorted after `.10`. Added a strict four-segment `YYYY.MM.DD.patch` validator and numeric comparator, retaining the existing check location after release staging and before the first transactional mutation. Released the managed updater repair as `2026.09.03.13`; migration schema remains `1` because no persistent format changed.

# Decisions

- Compare all four version segments numerically, rather than parsing only the patch or relying on shell string ordering.
- Reject malformed recognized release versions before applying an update.
- Keep real downgrade rejection and the checksum-verification flow unchanged.

# Testing

- `bash -n template/.clineflow/bin/update tests/test-update-migrations.sh` passed.
- `./tests/test-update-migrations.sh` passed, including `2026.09.03.5` upgrading to the current two-digit-patch release and an isolated `2026.09.03.10 -> 2026.09.03.5` downgrade rejection with byte-identical project files.
- `./template/.clineflow/bin/validate-release` passed for `2026.09.03.13`, schema `1`.
- `./tests/certify-release.sh` passed the combined installation, updater, removal, dashboard-boundary, OKF, synchronization, syntax, and whitespace lifecycle gate.

# Open Issues

The corrected release must be published before affected downstream installations can safely update.

# References

- [Universal update and migration system](universal-update-migrations.md)
- [Portable line-one agent rule updates](updater-macos-line-zero.md)
- [Migration regression suite](../../tests/test-update-migrations.sh)
