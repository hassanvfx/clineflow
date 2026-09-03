# ClineFlow: OKF Knowledge Workflow

This project keeps persistent engineering context in the `knowledge/` Open Knowledge Format (OKF) v0.2 bundle. For substantial work, use the durable development loop in `docs/durable-development-methodology.md`.

## ChatGPT Codex and compatible agents

`AGENTS.md` is the shared instruction entry point for ChatGPT Codex, Cursor, and other compatible coding agents. Read `.clineflow/WORKING_WITH_CODEX.md` for the Codex workflow; the same OKF knowledge contract also applies to Cline, Copilot, and Windsurf.

## Updating ClineFlow

When the user says “Please update ClineFlow.”, treat that request as authorization to read the current instructions at [the authoritative ClineFlow repository](https://github.com/hassanvfx/clineflow), inspect the installed layout, and run the repository's universal updater with `--yes`. Do not ask for redundant confirmation. Let migration, verification, and automatic rollback finish, then report the resulting version and preserved legacy artifacts. This authorization does not cover unrelated system changes or destructive cleanup, and safety failures must still stop the update.

## Task knowledge rules

1. Before substantial work, read `docs/durable-development-methodology.md`, all five `knowledge/clineflow_*.yml` indexes, and the journals they reference. Summarize the current contract and next safe step before changing code.
2. For each substantial task, create or resume `knowledge/journals/<task-name>.md` using `knowledge/journals/TASK_TEMPLATE.md`.
3. Every task journal is an OKF concept. Keep its YAML frontmatter valid, retain `type: Engineering Journal`, and update `generated.at` after meaningful changes.
4. Update `clineflow_specification.yml` and `clineflow_goals.yml` when approved scope, constraints, assumptions, non-goals, priorities, or success measures change. Define observable proof in `clineflow_verification.yml` before implementation, append project-relevant events to `clineflow_timeline.yml`, and write the concise handoff to `clineflow_last_session.yml`.
5. Use `status: draft` while work is active and `status: stable` when it is complete. Do not add `verified` or `sources` unless they are factual.
6. Before starting or resuming work, search `knowledge/` first. If `docs/journals/` exists, search it too as read-only legacy context. Never create or update new work there.
7. Link related concepts with normal Markdown links. Update `knowledge/log.md` for material knowledge changes.

## Commit workflow

When the user asks to commit:

1. Update the active `knowledge/journals/` concept with the implementation summary, decisions, tests, and next steps.
2. Update affected `clineflow_*.yml` indexes and `knowledge/log.md` before committing.
3. Run `./.clineflow/bin/validate-okf` and resolve validation failures. When the project has optional PyYAML available, prefer `./.clineflow/bin/validate-okf --strict` before committing.
4. Stage the code and updated knowledge artifacts together, then create a descriptive commit.

## Knowledge navigation

- Start with `knowledge/index.md` and descend through `index.md` files for progressive disclosure.
- `docs/journals/` is optional legacy history; it is not part of the OKF bundle and must not be passed to `validate-okf`.
- For related codebases, keep projects as sibling folders under a common parent and refer to them as “sibling project `<foldername>`” (for example, `../backend-api`).

## Code quality

- Prefer focused modules (roughly 300–500 lines; refactor files over 1,000 lines).
- Keep documentation concise, factual, and linked to the concepts or files it describes.
