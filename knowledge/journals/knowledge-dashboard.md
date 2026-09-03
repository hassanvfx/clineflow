---
type: Engineering Journal
title: "ClineFlow Knowledge Visor"
description: "Implements an isolated, time-first dashboard for navigating durable project knowledge."
tags: [engineering, knowledge, dashboard, observability, visualization]
status: stable
generated:
  by: clineflow/2026.09.03.9
  at: 2026-09-03T12:28:25Z
---

# Goal

Add an explicitly invoked ClineFlow Knowledge Visor that visualizes OKF knowledge and Git history without changing normal installation, validation, or daily operation.

# Status

- [x] Planned
- [x] In progress
- [x] Complete
- [x] Visual defect reproduced
- [x] Project Story redesign complete

# Work Log

## 2026-09-03 09:03 UTC - Implementation started

Recovered the five-ledger contract and the existing source-instruction repair. The approved boundary permits only an inert installed bootstrap and component manifest before invocation; optional runtimes, visual assets, reports, and Git exclusions are created transactionally on first approved use.

## 2026-09-03 09:30 UTC - Visor completed and boundary-tested

Added the inert command, pinned optional-component manifest, isolated Python renderer, time-first visual shell, structured snapshots, report comparisons, source-linked insights, sanitized export, optional-runtime diagnostics, transactional refresh/removal behavior, and an exact knowledge-dashboard synchronization exemption. Tightened first-use rollback so a failure after activation also returns the project to its dormant boundary.

## 2026-09-03 10:22 UTC - Decision Atlas visual defect reproduced

The initial Atlas put every canonical document and every ledger relationship into one force-directed canvas. Because synchronization intentionally references the same journals from multiple ledgers, the resulting graph was densely connected, its long labels overlapped, and its default view had no useful information hierarchy. The repair will replace the all-at-once graph with focused, capped views and a full-text details rail.

## 2026-09-03 10:25 UTC - Progressive Atlas completed

Replaced the force graph with a deterministic overview centered on ClineFlow and its five ledgers. Goals, constraints, evidence, and journals now open as separate focused views with at most ten visible card nodes, full text in a details rail, keyboard-accessible companion controls, and direct journal navigation into the Knowledge Explorer. Responsive styling keeps the graph and detail surface separate on narrow screens.

## 2026-09-03 10:27 UTC - Default invocation repaired

Reproduced the first-use crash caused by the shell wrapper resolving `generate` only for its own branching while forwarding an empty argument list to the Python engine. The wrapper now backfills the resolved command after global-option parsing, so the `generate` subparser installs its `insights`, `compare`, and `no_open` attributes before execution.

## 2026-09-03 10:31 UTC - Multi-audience story hierarchy added

Removed the visible asset inventory panel while retaining complete asset provenance in each report manifest. Reframed the dashboard as five linked chapters: an executive brief for current intent and next action, manager-facing trajectory and change, engineering decisions, shared verification and risk, and direct canonical source exploration. Added a sticky story navigator, concise executive narrative cards, chapter transitions, and responsive stacking.

## 2026-09-03 10:44 UTC - Structured facts and narrative observation pipeline completed

Rebuilt the Knowledge Explorer around parsed YAML objects, guided sections, chronological event cards, source and JSON tabs, parser diagnostics, and copyable normalized YAML repair output. Split generation into explicit `collect`, `observe`, and `render` stages: `snapshot.json` now contains only normalized facts, `observations.json` contains a source-hash-bound executive/manager/engineer narrative, and the self-contained HTML embeds exact copies of both for `file://` use. The deterministic observer is a formal replaceable boundary for a future CLI/LLM command. Atlas overview cards now lead into their focused decision surfaces instead of ending at static descriptions.

## 2026-09-03 11:19 UTC - Structured evidence and timeline normalization repaired

Reproduced `[object Object]` labels in the Evidence Atlas and blank timeline descriptions when projects provide richer YAML records instead of legacy strings. The collector now normalizes timeline aliases (`timestamp`, `occurred_at`, `category`, `description`, `references`, and related forms) into a canonical report event while preserving the raw source record. The viewer now selects meaningful statement fields (`summary`, `text`, `title`, `criterion`, and related forms), shows remaining metadata in the details rail, and retains compatibility with older snapshots. Added direct regressions for structured evidence, structured observation text, and aliased timeline records.

## 2026-09-03 11:33 UTC - Time Spine disclosure refined

Reworked each Time Spine row into a short kind pill, a concise supplied or derived title, and a collapsed “Read event note” disclosure. Long `event:` strings are now interpreted as the narrative note rather than the lane type; their first clause becomes a bounded, scan-friendly title. Expanded notes retain their paragraph boundaries, while concise events remain compact without an unnecessary disclosure.

## 2026-09-03 11:38 UTC - YAML prose scalar repair

Inspection of the generated fact model caught two prose list entries containing an unquoted colon. YAML correctly interpreted those entries as mappings, which is not the intended canonical shape. Quoted the entries so the facts model retains scalar strings. This confirms the structured renderer is working as intended and prevents malformed prose from leaking into executive observations or visual labels.

## 2026-09-03 11:49 UTC - Project Story replaced the Atlas

Removed the remaining graph-based Decision Atlas after it continued to make the report feel repetitive and less narrative than the underlying durable record. The renderer now derives a formal `project_story` object from normalized facts: evolution, what matters now, attention required, next deliberate move, and a compact milestone arc. The viewer renders those source-linked claims as navigable cards that open their canonical supporting record. Cytoscape is no longer part of the optional asset manifest, release validation, report bytes, or visual system.

## 2026-09-03 11:53 UTC - Executive signal correction

The hero originally derived “latest activity” from the combined display timeline, which includes dashboard reports. That can make the report appear to be the newest project activity. It now selects the newest knowledge event or Git commit and labels the metric accordingly. The sticky chapter navigation calls the third section “Story,” matching the Project Story content rather than the removed graph metaphor.

## 2026-09-03 12:28 UTC - ClineFlow visual language alignment

Reviewed the public ClineFlow landing page as a visual reference. Its deep navy base, electric-blue emphasis, Inter-like editorial hierarchy, restrained corner geometry, and quiet navigation are more cohesive than the visor’s former green grid aesthetic. Rebuilt the visor’s CSS tokens and supporting components around those principles, including a navy document explorer and blue story treatment. No landing-page media, code, copy, or remote assets were reused; the report remains self-contained.

# Decisions

- Keep migration schema `1`; the visor adds managed behavior but does not change the OKF persistent format.
- Derive Git and footprint metrics into report snapshots rather than canonical timeline entries.
- Fetch pinned visual assets only after invocation, verify them before activation, and embed them so generated reports perform no browser-time network access.
- Preserve all generated reports during uninstall and exclude only `knowledge/dashboard/**` from knowledge synchronization.
- Keep the report's verified CDN and font bytes embedded. `manifest.json` records their source URLs and `snapshot.json` mirrors the structured data embedded in `index.html`, avoiding any browser-time dependency fetch.
- Keep schema `1`; release `2026.09.03.2` changes managed installed files but no persistent OKF structure.
- Treat ledger-wide journal references as synchronization metadata rather than useful graph edges; progressive semantic views provide the navigable information hierarchy.
- Bump the managed release and optional component to `2026.09.03.4`; migration schema remains `1` because no persistent format changed.
- Default the command in the shell wrapper, which owns global-option normalization and forwards arguments to the engine; no migration is required for this managed payload update.
- Keep asset checksums, versions, source URLs, and licenses in structured manifests, but remove their low-value visual inventory from the main story.
- Use audience-aware chapters as progressive disclosure without duplicating separate dashboards or hiding canonical evidence.
- Make `snapshot.json` the renderer's only factual input and keep narrative interpretation in the separately validated `clineflow-dashboard-observations/v1` artifact.
- Embed both JSON artifacts in inert `application/json` script blocks so direct local-file viewing never requires fetch access; preserve adjacent copies for inspection and automation.
- Keep YAML repair non-mutating: the pinned PyYAML runtime emits diagnostics and normalized copy output, while canonical source changes remain an explicit user action outside the dashboard boundary.
- Normalize flexible timeline records only in report facts, preserving each original object under `raw`; do not impose a new persistent ledger schema.
- Prefer named statement fields when rendering structured evidence or decisions, and expose all remaining fields in the readable detail surface rather than serializing objects into labels.
- Treat Time Spine labels as event kinds and titles as the scan layer; retain full event narration only in explicit disclosure.
- Quote prose list items containing a colon followed by whitespace in canonical YAML when they are intended to be scalar statements.
- Replace the graph Atlas rather than repeatedly restyling it. A small narrative surface better matches the decision-making job and avoids accidental relationship semantics from ledger synchronization metadata.
- Validate every Project Story card and milestone in supplied observations against known canonical document IDs. This keeps the future CLI/LLM observation boundary source-bound.
- Bump the managed release and optional component to `2026.09.03.7`; no migration is required because this changes only isolated managed runtime and asset behavior, not the OKF persistent schema.
- Bump release `2026.09.03.8` without a migration: this is a contained narrative-quality correction in managed viewer code.
- Use the public ClineFlow visual system as a principle-level reference only. Preserve the dashboard’s own semantic content, embedded assets, and offline CSP boundary.
- Bump release `2026.09.03.9` without a migration for the managed visor style update.

# Testing

- `tests/test-dashboard.sh` proves dormant installation, non-mutating decline, exact activated boundaries, self-contained HTML/snapshot equality, offline cache reuse, post-verification rollback, sanitized export, and report-preserving uninstall.
- Release-contract, installation, knowledge-sync, and historical migration suites pass with the optional subsystem dormant.
- A real first activation downloaded uv, Python 3.12, locked Python packages, JavaScript libraries, and font files; verified every pinned asset; and generated a local report.
- Static JavaScript, Python, shell, CSP, and whitespace checks pass. The Codex in-app browser rejected direct local-file navigation by policy, so no browser-policy bypass was attempted.
- Atlas regression coverage requires all five view controls, the ten-node cap, and removal of the old COSE force layout. Focused dashboard boundary tests and the release contract pass for `2026.09.03.4`.
- `./tests/test-dashboard.sh` passes the exact first-use form `./.clineflow/bin/dashboard --yes`, report generation, explicit subcommands, offline reuse, rollback, export, and removal.
- `./tests/certify-release.sh` passes the complete release `2026.09.03.4` lifecycle after the wrapper fix, including installation, dashboard boundaries, historical updates, rollback, uninstall safety, release-contract rejection cases, OKF validation, knowledge synchronization, and whitespace checks.
- Dashboard tests require the executive/manager/engineering/source story markers, absence of the visible asset panel, and retention of complete asset provenance in `manifest.json`.
- Dashboard boundary tests pass the independent facts → observations → render commands, assert exact embedded/adjacent JSON equality, bind observations to the facts source hash, require all three audience narratives, and verify structured YAML plus normalized repair output.
- Structured-record regressions prove evidence labels never coerce to `[object Object]`, narrative observations choose a human-readable statement, and timeline aliases normalize into time, type, summary, references, and raw provenance.
- Time Spine regression coverage verifies long `event:` notes derive a concise title, retain the full note, and expose the progressive disclosure control.
- Dashboard boundary tests pass for release `2026.09.03.7`, including deterministic mock-fact Project Story derivation, embedded story JSON, source-id validation, graph-asset removal, offline reuse, rollback, export, and uninstall preservation.
- Dashboard tests assert that the narrative navigation names the Project Story and that executive activity ignores generated report runs.
- Static CSS review confirms deep navy and electric-blue tokens replace the prior green dashboard palette; focused dashboard boundary tests remain the behavior proof.

# Open Issues

None.

# References

- [Universal update system](universal-update-migrations.md)
- [Universal knowledge synchronization](universal-five-ledger-synchronization.md)
- [Durable development methodology](../../docs/durable-development-methodology.md)
