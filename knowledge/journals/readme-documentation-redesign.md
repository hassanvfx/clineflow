---
type: Engineering Journal
title: "Installation-first README and documentation redesign"
description: "Reframes ClineFlow around installation, durable commits, lifecycle prompts, and the Knowledge Visor."
tags: [documentation, readme, installation, agents, dashboard]
status: draft
generated:
  by: clineflow/2026.09.03.20
  at: 2026-09-03T20:16:12Z
---

# Goal

Create a concise, installation-first README supported by focused reference guides, a local tutorial preview, and consistent natural-language agent commands for committing, updating, removal, and the Knowledge Visor. Preserve a deterministic dashboard capture as an explicit follow-up when the local report can be captured through an allowed browser surface.

# Status

- [x] Planned
- [x] In progress
- [ ] Complete

# Work Log

## 2026-09-03 19:46 UTC - Implementation started

Recovered the durable development contract, audited the existing README, release payload, lifecycle scripts, agent-rule templates, and dashboard fixtures, and reviewed the public ClineFlow site for its concise installation-first messaging. The approved implementation replaces duplicated and stale README material with a focused landing page, moves depth into linked guides, formalizes preview-before-removal agent behavior, and adds deterministic dashboard and tutorial visuals.

## 2026-09-03 20:16 UTC - Documentation and lifecycle contract delivered

Replaced the 831-line README with a concise installation-first guide; added focused installation/lifecycle, workflow, and Knowledge Visor references; expanded the OKF reference; added the verified Vimeo tutorial poster; and distributed canonical commit, update, preview-before-removal, and dashboard prompts across agent guidance. Preserved the newer agent-insights dashboard pipeline found in release `.19` and advanced the managed release to `2026.09.03.20` with migration schema `1`.

The deterministic comprehensive dashboard fixture rendered successfully in an isolated temporary installation. The in-app browser rejected local `file://` navigation under its security policy, so no dashboard screenshot was committed and no broken image reference remains in the README.

# Decisions

- Keep the agentic installation prompt as the primary call to action and retain terminal commands as secondary paths.
- Treat “Please remove ClineFlow.” as authorization to preview removal, not to bypass final confirmation.
- Capture the dashboard sample from deterministic comprehensive fixtures so no personal or live repository data enters the image.
- Keep migration schema `1`; the installed rule and guide changes require a release bump but no persistent-format migration.
- Ship the complete non-broken documentation set now and keep the dashboard capture as an explicit follow-up requiring an allowed capture surface or user-provided image.

# Testing

- `./template/.clineflow/bin/validate-release` — passed for release `2026.09.03.20`, schema `1`.
- `./tests/test-release-contract.sh` — passed lifecycle prompt and release rejection coverage.
- `./tests/test-installation-flow.sh` — passed agent-rule propagation, user-content preservation, doctor, update, and removal flows.
- Vimeo poster inspected at 1280×720 and confirmed to contain the intended ClineFlow tutorial artwork.
- `./tests/certify-release.sh` — passed the complete lifecycle certification against the synchronized knowledge state.

# Open Issues

- Capture a representative 1600×1000 Knowledge Visor image from the deterministic comprehensive fixture when an allowed local browser capture surface or user-supplied screenshot is available.

# References

- [Project README](../../README.md)
- [Durable development methodology](../../docs/durable-development-methodology.md)
- [Universal five-ledger synchronization](universal-five-ledger-synchronization.md)
- [Knowledge Visor](knowledge-dashboard.md)
