# ClineFlow OKF Knowledge Workflow

ClineFlow stores persistent engineering context as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) v0.2 bundle. Markdown carries the human-readable narrative, YAML frontmatter carries concept metadata, normal links express relationships, and Git preserves reviewable history.

## Bundle layout

```text
knowledge/
├── index.md                         # Navigation; declares okf_version: "0.2"
├── clineflow_goals.yml              # Outcomes, priorities, and blockers
├── clineflow_specification.yml      # Requirements, constraints, and questions
├── clineflow_verification.yml       # Acceptance criteria and evidence
├── clineflow_last_session.yml       # Current handoff and next action
├── clineflow_timeline.yml           # Chronological project events
├── log.md                           # Dated knowledge change history
└── journals/
    ├── index.md                     # Progressive-disclosure task listing
    ├── TASK_TEMPLATE.md             # Engineering Journal template
    └── <task-name>.md               # Detailed task concepts
```

`index.md` files provide progressive disclosure. Agents start at `knowledge/index.md`, inspect the five small ledgers, and follow links only into the journals relevant to the current task.

## The five ledgers

| Ledger | Update it when | It should answer |
| --- | --- | --- |
| `clineflow_goals.yml` | Outcomes, priorities, success measures, or blockers change. | Why are we doing this, and what does success mean? |
| `clineflow_specification.yml` | Behavior, constraints, assumptions, non-goals, or open decisions change. | What have we agreed to build, preserve, or avoid? |
| `clineflow_verification.yml` | A check is defined, run, passed, failed, or blocked. | What proves completion, and where is the evidence? |
| `clineflow_last_session.yml` | A material change or handoff occurs. | What is true now, and what should happen next? |
| `clineflow_timeline.yml` | A relevant interaction, decision, repository event, or handoff occurs. | How did the project reach its current state? |

The ledgers are discovery and coordination indexes, not replacements for Engineering Journals. Keep summaries short and link to the detailed record.

## Engineering Journal concepts

Every substantial task creates or resumes `knowledge/journals/<task-name>.md`. A journal uses YAML frontmatter like:

```yaml
---
type: Engineering Journal
title: "Task title"
description: "Persistent context for the task."
tags: [engineering]
status: draft
generated:
  by: clineflow/<version>
  at: YYYY-MM-DDTHH:MM:SSZ
---
```

The Markdown body records the goal, status, chronological work log, decisions, testing, open issues, and references. Use `status: draft` while work is active and `status: stable` when the recorded task is complete. Add `verified` or `sources` metadata only when those claims are factual.

## The synchronization contract

Any Git change set that edits a journal, documentation, or the knowledge base must reconcile:

- The active Engineering Journal
- All five `knowledge/clineflow_*.yml` ledgers
- `knowledge/log.md`

Use one timestamp for every ledger's `updated_at`, the active journal's `generated.at`, and the newest timeline event. Every ledger must reference the active journal. Refresh the last-session handoff and append a matching timeline event. If goals, specification, or verification have no semantic change, updating only their timestamp records that the ledger was reviewed.

This is a change-set rule, not a requirement to rewrite every ledger after each file save. Generated files below `knowledge/dashboard/` are explicitly outside this synchronization contract.

## Validation

Before delivery:

```bash
./.clineflow/bin/validate-okf
./.clineflow/bin/validate-knowledge-sync
```

The default validator requires no Python package. It checks bundle structure, concept frontmatter, non-empty `type`, reserved files, root OKF version declaration, references, timestamps, and log ordering.

For full YAML parsing when Python and PyYAML are already available:

```bash
./.clineflow/bin/validate-okf --strict
```

Before a commit, stage code and durable knowledge together and run:

```bash
./.clineflow/bin/validate-knowledge-sync --staged
```

Pull-request CI runs the same synchronization contract against its base revision.

## Legacy journals

Projects may contain `docs/journals/` from earlier ClineFlow releases. Agents search it as read-only historical context, but:

- New work is written only to `knowledge/journals/`.
- Legacy files are never passed to `validate-okf`.
- Changes to `docs/journals/` are rejected by knowledge synchronization.
- Installation, update, and removal preserve the directory.

## Installation, update, and removal

Fresh installation creates missing OKF fixtures without replacing existing knowledge. The permanent remote updater migrates identified OKF-era layouts from `2026.08.15.0` onward, preserves user-authored knowledge, and rolls back failed migrations. Removal deletes managed tooling and instruction blocks while leaving the OKF bundle in place.

Read [How ClineFlow works](how-clineflow-works.md) for the agent loop and [Installation and Lifecycle](installation-and-lifecycle.md) for the operational commands.
