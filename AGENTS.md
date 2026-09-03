# ClineFlow: OKF Knowledge Workflow

This project keeps persistent engineering context in the `knowledge/` Open Knowledge Format (OKF) v0.2 bundle. For substantial work, use the durable development loop in `docs/durable-development-methodology.md`.

## ChatGPT Codex and compatible agents

`AGENTS.md` is the shared instruction entry point for ChatGPT Codex, Cursor, and other compatible coding agents. In this distribution repository, read `template/.clineflow/WORKING_WITH_CODEX.md` for the Codex workflow; installed projects receive the same guide at `.clineflow/WORKING_WITH_CODEX.md`. The same OKF knowledge contract also applies to Cline, Claude Code, Copilot, and Windsurf.

## Updating ClineFlow

When the user says “Please update ClineFlow.”, treat that request as authorization to read the current instructions at [the authoritative ClineFlow repository](https://github.com/hassanvfx/clineflow), inspect the installed layout, and immediately run the permanent remote bootstrap with `--yes`:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes
```

Do not run any existing local updater first; legacy copies can overwrite themselves. Do not ask for redundant confirmation. Let migration, verification, and automatic rollback finish, then report the resulting version and preserved legacy artifacts. This authorization does not cover unrelated system changes or destructive cleanup, and safety failures must still stop the update.

## Knowledge Visor

Only when the user explicitly requests the ClineFlow dashboard or Knowledge Visor, invoke the installed project's `./.clineflow/bin/dashboard`. Never activate the optional runtime proactively during normal development, installation, validation, or commit preparation.

## Task knowledge rules

1. Before substantial work, read `docs/durable-development-methodology.md`, all five `knowledge/clineflow_*.yml` indexes, and their linked journals. Summarize the current contract and next safe step before changing code.
2. For each substantial task, create or resume `knowledge/journals/<task-name>.md` using `knowledge/journals/TASK_TEMPLATE.md`.
3. Every task journal is an OKF concept. Keep its YAML frontmatter valid, retain `type: Engineering Journal`, and update `generated.at` after meaningful changes.
4. Every change set that edits a journal, documentation, or the knowledge base must reconcile all five `knowledge/clineflow_*.yml` ledgers with one shared `updated_at` timestamp, update the active journal's `generated.at` to that timestamp, reference the active journal from every ledger, append a matching timeline event, refresh last-session context, and update `knowledge/log.md`. A timestamp-only goals, specification, or verification edit explicitly records that the ledger was reviewed and had no semantic change.
5. Use `status: draft` while work is active and `status: stable` when it is complete. Do not add `verified` or `sources` unless they are factual.
6. Before starting or resuming work, search `knowledge/` first. If `docs/journals/` exists, search it too as read-only legacy context. Never create or update new work there.
7. Link related concepts with normal Markdown links. Update `knowledge/log.md` for material knowledge changes.

## Commit workflow

When the user asks to commit:

1. Update the active `knowledge/journals/` concept with the implementation summary, decisions, tests, and next steps.
2. Reconcile all five `knowledge/clineflow_*.yml` ledgers and update `knowledge/log.md`.
3. Run `./template/.clineflow/bin/validate-okf` and `./template/.clineflow/bin/validate-knowledge-sync`, resolving all failures. When optional PyYAML is available, prefer `./template/.clineflow/bin/validate-okf --strict`.
4. Stage the code and knowledge artifacts together, run `./template/.clineflow/bin/validate-knowledge-sync --staged`, then create a descriptive commit.

For changes to installed files, persistent formats, ownership, or required behavior, update the ClineFlow release manifest and either add the next migration or record and test that no migration is required. Run `./tests/certify-release.sh` before delivery.

## Knowledge navigation

- Start with `knowledge/index.md` and descend through `index.md` files for progressive disclosure.
- `docs/journals/` is optional legacy history; it is not part of the OKF bundle and must not be passed to `validate-okf`.
- For related codebases, keep projects as sibling folders under a common parent and refer to them as “sibling project `<foldername>`” (for example, `../backend-api`).

## Code quality

- Prefer focused modules (roughly 300–500 lines; refactor files over 1,000 lines).
- Keep documentation concise, factual, and linked to the concepts or files it describes.
