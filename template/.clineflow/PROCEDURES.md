# ClineFlow Procedures

## Start or resume work

1. Read `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five `knowledge/clineflow_*.yml` master indexes.
2. Follow relevant master-index references, then search `knowledge/` for related task journals, decisions, and references.
3. When present, search `docs/journals/` for relevant legacy context. Treat these files as read-only historical material.
4. Create or resume `knowledge/journals/<task-name>.md` from `knowledge/journals/TASK_TEMPLATE.md` for substantial work.

## Maintain OKF knowledge

- Keep every non-reserved Markdown document in `knowledge/` parseable with YAML frontmatter and a non-empty `type`.
- Reserve `index.md` for navigation and `log.md` for dated change history.
- Use Markdown links for relationships; broken links are acceptable when knowledge is not written yet.
- Record only factual provenance, verification, and lifecycle fields.
- For every journal, documentation, or knowledge-base change, reconcile all five master indexes with one timestamp, reference the active journal from each, append a matching timeline event, refresh the handoff, and update `knowledge/log.md`. A timestamp-only update means the ledger was reviewed with no semantic change.

## Commit

1. Update the active Engineering Journal with outcomes, decisions, tests, and follow-up work.
2. Reconcile all five ledgers and add a dated entry to `knowledge/log.md`.
3. Run `./.clineflow/bin/validate-okf` and `./.clineflow/bin/validate-knowledge-sync`.
4. Stage implementation and knowledge together, run `./.clineflow/bin/validate-knowledge-sync --staged`, and commit only when it passes.

## Generate the optional Knowledge Visor

- Run `./.clineflow/bin/dashboard` only after an explicit user request for the ClineFlow dashboard or Knowledge Visor.
- First use previews and approval-gates all optional runtime and visual-asset downloads.
- Generated reports under `knowledge/dashboard/` are local presentation artifacts, not canonical OKF knowledge, and do not require five-ledger synchronization.
