---
type: Engineering Journal
title: "Native OKF knowledge workflow"
description: "Implementation record for ClineFlow's transition to native OKF task knowledge."
tags: [clineflow, okf, knowledge]
status: stable
generated:
  by: clineflow/2.0.0
  at: 2026-08-15T00:00:00Z
---

# Goal

Adopt an OKF v0.2 knowledge bundle while preserving `docs/journals/` as read-only legacy context.

# Decisions

- New task journals are Engineering Journal concepts under `knowledge/journals/`.
- Legacy journals are searched for context but are not converted or validated.
- `validate-okf` is a dependency-free Bash CLI that validates the structural OKF contract.

# Testing

Validated with `bash validate-okf` and `bash tests/test-okf-validator.sh`.
