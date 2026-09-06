# ClineFlow Procedures

## Start or resume work

1. Run `./.clineflow/bin/knowledge sync`, then read `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five generated `knowledge/clineflow_*.yml` views.
2. Follow relevant master-index references, then search `knowledge/` for related task journals, decisions, and references.
3. When present, search `docs/journals/` for relevant legacy context. Treat these files as read-only historical material.
4. Inspect `./.clineflow/bin/knowledge topics`, then create a topic-scoped journal with `knowledge journal new`; resume only a named stream that belongs to the pinned tenant.

## Maintain OKF knowledge

- Keep every non-reserved Markdown document in `knowledge/` parseable with YAML frontmatter and a non-empty `type`.
- Reserve `index.md` for navigation and `log.md` for dated change history.
- Use Markdown links for relationships; broken links are acceptable when knowledge is not written yet.
- Record only factual provenance, verification, and lifecycle fields.
- Create one immutable `knowledge/updates/<topic>/<uuid>--<tenant>.yml` record for each published update. Every record explicitly reviews all five ledgers; unchanged ledgers are recorded as `unchanged` rather than rewritten. Run `knowledge sync` to rebuild local views.

## Commit

1. Update the active tenant journal and create an immutable update record.
2. Run `./.clineflow/bin/knowledge sync`, `./.clineflow/bin/validate-okf`, and `./.clineflow/bin/validate-knowledge-sync`.
3. Stage implementation, journals, and update records together, then run `./.clineflow/bin/validate-knowledge-sync --staged` before committing.

## Generate the optional Knowledge Visor

- Run `./.clineflow/bin/dashboard` only after an explicit user request for the ClineFlow dashboard or Knowledge Visor.
- First use previews and approval-gates all optional runtime and visual-asset downloads.
- Generated reports under `knowledge/dashboard/` are local presentation artifacts, not canonical OKF knowledge, and do not require five-ledger synchronization.
