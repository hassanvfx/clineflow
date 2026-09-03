---
type: Engineering Journal
title: "Portable line-one agent rule updates"
description: "Repairs the macOS updater failure when a managed agent block begins on the first line."
tags: [engineering, updates, migrations, macos, portability]
status: stable
generated:
  by: clineflow/2026.09.03.3
  at: 2026-09-03T10:12:33Z
---

# Goal

Make schema-0 and current-layout updates portable when an existing valid ClineFlow agent-rule block starts on line one, while retaining transactional rollback and preserving any text before or after the block.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-03 09:51 UTC - Failure diagnosed

Claude Code reported that a legacy flat updater replaced itself and left a mixed schema-0 layout. The authoritative transactional updater correctly detected the layout and rolled back, but failed while refreshing a valid agent block at line one because macOS BSD `head` rejects `head -n 0`. The existing migration matrix covered fingerprint adoption, unmarked custom rules, and malformed markers, but not a valid marker beginning on the first line.

## 2026-09-03 09:54 UTC - Portable refresh completed

Replaced the computed `head -n 0` call with an explicit empty-prefix branch and portable `sed` prefix extraction. Added schema-0 mixed-state cases for both a line-one block and a block surrounded by user-authored text. Released the managed updater fix as `2026.09.03.3` with schema `1`.

## 2026-09-03 10:12 UTC - Agent entrypoint hardened

The Claude transcript also showed the agent executing a stale local `bin/update` before consulting the authoritative entrypoint. Updated source and installed agent instructions to require the permanent remote bootstrap immediately and explicitly prohibit running any local updater first. Release validation and rejection tests now enforce both clauses.

# Decisions

- Replace the zero-line `head` operation with an explicit portable prefix writer that creates an empty prefix when the managed block starts on line one.
- Add regression cases for both a line-one managed block and a block preceded by user text.
- Keep migration schema `1`; this is a managed updater portability fix with no persistent-format change.
- Make the remote root bootstrap—not any installed legacy updater—the first executable update step for the canonical agent prompt.

# Testing

- The new regression failed before the fix on macOS with `head: illegal line count -- 0`, followed by a successful automatic rollback.
- `./tests/test-update-migrations.sh` passed after the fix, including line-one and prefixed managed blocks, user suffix/prefix preservation, schema-0 convergence, rollback, and idempotency.
- `./tests/certify-release.sh --against HEAD` passed the complete release, installation, dashboard-boundary, update, uninstall, release-contract, OKF, knowledge-sync, syntax, and whitespace gate for `2026.09.03.3`.
- `./tests/test-release-contract.sh` rejects missing remote-bootstrap instructions and any documentation that permits a local updater first.
- `./tests/certify-release.sh` passed again after the final shared-agent instruction and manifest checksum changes.

# Open Issues

The affected downstream project still needs to rerun the authoritative updater after this release is published.

# References

- [Universal update and migration system](universal-update-migrations.md)
- [Lifecycle migration matrix](../../tests/test-update-migrations.sh)
