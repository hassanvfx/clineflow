# ClineFlow: OKF Knowledge Workflow

This project keeps persistent engineering context in the `knowledge/` Open Knowledge Format (OKF) v0.2 bundle. For substantial work, use the durable development loop in `docs/durable-development-methodology.md`.

## ChatGPT Codex and compatible agents

`AGENTS.md` is the shared instruction entry point for ChatGPT Codex, Cursor, and other compatible coding agents. Read `.clineflow/WORKING_WITH_CODEX.md` for the Codex workflow; the same OKF knowledge contract also applies to Cline, Copilot, and Windsurf.

## Updating ClineFlow

When the user says “Please update ClineFlow.”, this is an execution request, not a request to check for releases. Before any version lookup, explanation, or response, immediately run `curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes`. Do not run any existing local updater first; legacy copies can overwrite themselves. Do not substitute a GitHub release/tag check, cached result, or a claim that the installation is current. Do not ask for redundant confirmation. A successful response must report the command outcome and the value read from `.clineflow/VERSION` after the command finishes. If command execution is blocked by permission, network, or a safety failure, report that exact blocker; never claim the installation is up to date. Let migration, verification, and automatic rollback finish, then report the resulting version and preserved legacy artifacts. This authorization does not cover unrelated system changes or destructive cleanup, and safety failures must still stop the update. Claude Code users may invoke the deterministic project command `/update-clineflow` instead of typing the phrase.

## Removing ClineFlow

When the user says “Please remove ClineFlow.”, first run `./.clineflow/bin/uninstall --dry-run`, explain exactly which managed files and rule blocks would be removed and which project knowledge and user content would be preserved, and ask for explicit confirmation. Only after that confirmation may you run the remover; use `--yes` only when the user has authorized the final removal. The initial phrase does not authorize bypassing the preview or confirmation.

## Knowledge Visor

Only when the user explicitly says “Please show me the ClineFlow dashboard.” or directly requests the Knowledge Visor, generate the report. For an agent-handled natural-language request, use the formal pipeline: collect facts to temporary storage, read those facts, write a validated source-linked insights JSON when the agent can ground narrative observations or delivery assumptions, then run `dashboard observe` and `dashboard render`. A delivery estimate must contain explicit agent context, currency, loaded rate, baseline hours, direct costs, scenario multipliers, rationale, and valid source IDs; label it as an estimate and never invent financial constants. If those inputs are unavailable, render without an estimate and say so. Direct `./.clineflow/bin/dashboard` remains the intentional no-insights fallback. The command previews and approval-gates its optional first-use runtime. Never activate or generate the dashboard proactively during ordinary work, installation, validation, or commit preparation.

## Task knowledge rules

1. Before substantial work, read `docs/durable-development-methodology.md`, all five `knowledge/clineflow_*.yml` indexes, and the journals they reference. Summarize the current contract and next safe step before changing code.
2. For each substantial task, create or resume `knowledge/journals/<task-name>.md` using `knowledge/journals/TASK_TEMPLATE.md`.
3. Every task journal is an OKF concept. Keep its YAML frontmatter valid, retain `type: Engineering Journal`, and update `generated.at` after meaningful changes.
4. Every change set that edits a journal, documentation, or the knowledge base must reconcile all five `knowledge/clineflow_*.yml` ledgers with one shared `updated_at` timestamp, update the active journal's `generated.at` to that timestamp, reference the active journal from every ledger, append a matching timeline event, refresh last-session context, and update `knowledge/log.md`. A timestamp-only goals, specification, or verification edit explicitly records that the ledger was reviewed and had no semantic change.
5. Use `status: draft` while work is active and `status: stable` when it is complete. Do not add `verified` or `sources` unless they are factual.
6. Before starting or resuming work, search `knowledge/` first. If `docs/journals/` exists, search it too as read-only legacy context. Never create or update new work there.
7. Link related concepts with normal Markdown links. Update `knowledge/log.md` for material knowledge changes.

## Commit workflow

When the user says “Please commit.” or otherwise asks to commit:

1. Update the active `knowledge/journals/` concept with the implementation summary, decisions, tests, and next steps.
2. Reconcile all five `knowledge/clineflow_*.yml` ledgers and update `knowledge/log.md`.
3. Run `./.clineflow/bin/validate-okf` and `./.clineflow/bin/validate-knowledge-sync`, resolving all failures. When optional PyYAML is available, prefer `./.clineflow/bin/validate-okf --strict`.
4. Stage the code and knowledge artifacts together, run `./.clineflow/bin/validate-knowledge-sync --staged`, then create a descriptive commit.

## Knowledge navigation

- Start with `knowledge/index.md` and descend through `index.md` files for progressive disclosure.
- `docs/journals/` is optional legacy history; it is not part of the OKF bundle and must not be passed to `validate-okf`.
- For related codebases, keep projects as sibling folders under a common parent and refer to them as “sibling project `<foldername>`” (for example, `../backend-api`).

## Code quality

- Prefer focused modules (roughly 300–500 lines; refactor files over 1,000 lines).
- Keep documentation concise, factual, and linked to the concepts or files it describes.
