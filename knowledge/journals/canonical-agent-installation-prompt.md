---
type: Engineering Journal
title: "Canonical agent installation prompt"
description: "Standardizes the ClineFlow installation request shown to coding-agent users."
tags: [engineering, documentation, installation]
status: stable
generated:
  by: clineflow/2.1.0
  at: 2026-08-30T00:00:00Z
---

# Goal

Present one authoritative ClineFlow installation prompt wherever users are asked to delegate installation to a coding agent.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-08-30 - Completed

Replaced both README agent-installation prompts and added the same wording to the durable development methodology and its installable template. The legacy `docs/journals/` record was intentionally left unchanged because it is read-only historical context.

# Decisions

- Use the exact requested prompt and a Markdown link to the authoritative ClineFlow repository.
- Keep the durable methodology template synchronized with its source copy so configured projects receive the same guidance.

# Testing

- Confirmed the exact requested prompt appears twice in `README.md` and once in each durable methodology copy.
- `./template/.clineflow/bin/validate-okf` — passed.
- `git diff --check` — passed.

# Open Issues

None.

# References

- [Durable development methodology](../../docs/durable-development-methodology.md)
