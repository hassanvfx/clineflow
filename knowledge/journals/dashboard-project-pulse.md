---
type: Engineering Journal
title: "Dashboard Project Pulse and delivery scenarios"
description: "Adds commit-and-footprint trajectory context plus agent-authored delivery planning estimates to the Knowledge Visor."
tags: [engineering, dashboard, observability, planning, estimates]
status: stable
generated:
  by: clineflow/2026.09.03.19
  at: 2026-09-03T19:37:45Z
---

# Goal

Add a self-contained Project Pulse and source-bound delivery-scenario planning model without manufacturing labor telemetry, productivity scores, or browser-time dependencies.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-03 - Implementation started

The dashboard already collects committed numstat and tracked-tree footprint facts and isolates agent interpretation in the `observe` stage. The approved slice will expose those facts as a narrative Trajectory surface and accept an optional agent-supplied delivery estimate with explicit constants, validation, calculated outputs, and local-only report rendering.

## 2026-09-03 - Implementation completed

Added an ECharts Project Pulse with committed insertions/deletions and tracked/knowledge footprint ribbons, readable summary/detail fallback, and a separately labeled working-tree snapshot. Extended the existing agent insights contract with `clineflow-dashboard-delivery-estimate/v1`; validation requires explicit agent context, source IDs, currency, rate, baseline hours, direct costs, and positive scenario multipliers. Python calculates all scenario hours, costs, and deltas before presentation rendering. The report presents the transparent inputs, agent perspective, a two-dimensional comparison, and an instruction-only revision modal. Sanitized exports remove the estimate and model metadata. Release `2026.09.03.14` retains migration schema `1`.

## 2026-09-03 - Explorer status correction

The fixture-review browser exposed an over-stretched `Source ready` status badge in the Knowledge Explorer. Aligned the document header to the top and made the badge non-growing, non-wrapping, and compact. The correction is visual only; release `2026.09.03.15` keeps schema `1`.

## 2026-09-03 - Read-only compact presentation refinement

Removed the dashboard's browser-local source edit-request and Pending edits controls. The observer/presentation stage now builds compact titles, summaries, structured field rows, and retained full detail for evidence, decision records, and every structured source document before HTML is rendered. The browser only renders that prepared representation and exposes full source prose through deliberate expansion or raw-source view. Estimate-free reports omit Delivery Scenarios entirely; supplied estimates retain their source-bound, agent-authored model. Release `2026.09.03.16` keeps migration schema `1` and the self-contained `file://` contract.

## 2026-09-03 - Update execution contract

Strengthened the managed agent rule for “Please update ClineFlow.” so it explicitly prohibits release-only checks and requires the permanent remote bootstrap plus post-command `.clineflow/VERSION` evidence. Added the fixture-installed Claude Code command `/update-clineflow` with the same contract. Release `2026.09.03.17` keeps schema `1`.

## 2026-09-03 - Headline normalization

The Agentic Analytics report exposed a raw timestamped event being used as the hero heading. Headline normalization now removes ISO timestamps and `(see path)` metadata before splitting the first supporting clause. The same full event remains available in the report data and disclosure surfaces. Release `2026.09.03.18` keeps schema `1`.

## 2026-09-03 - Agent dashboard pipeline

The natural-language dashboard contract now directs agents through `collect → insights → observe → render`, so agent-authored, source-linked narrative and delivery estimates can enter the report. Direct CLI generation remains intentionally insight-free. A delivery estimate still requires explicit constants rather than inferred labor or cost. Release `2026.09.03.19` keeps schema `1`.

# Decisions

- The invoking agent supplies the optional estimate through the existing insights input; ClineFlow does not call an AI provider or infer model configuration.
- Engineering-hours estimates, not elapsed Git timeline duration, anchor the scenarios.
- Browser controls show revision instructions only; they never edit planning assumptions or canonical source files.
- Source inspection is read-only; no dashboard interaction creates local drafts, stores browser state, or presents a source-edit handoff.
- Long prose belongs in presentation detail, never as a hero heading, proof title, or guided-source field value.
- Sanitized exports exclude delivery estimates and agent metadata.

# Testing

- `./tests/test-dashboard.sh` passed dormancy, activation, local-file rendering, embedded JSON equality, comprehensive/minimal/empty fixtures, valid delivery scenarios, invalid estimate rejection, export redaction, retention, rollback, and uninstall preservation.
- `./template/.clineflow/bin/validate-release` and `./tests/test-release-contract.sh` passed for `2026.09.03.14`, schema `1`.
- `./tests/certify-release.sh` passed the combined installation, updater, removal, dashboard-boundary, OKF, synchronization, syntax, and whitespace lifecycle gate.
- `./tests/test-dashboard.sh` passed after removing edit controls, omitting estimate-free panels, and rendering prepared compact source/evidence records.

# Open Issues

No estimate appears until an invoking agent explicitly supplies one.

# References

- [Knowledge Visor](knowledge-dashboard.md)
- [Dashboard boundary suite](../../tests/test-dashboard.sh)
