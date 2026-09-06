# ClineFlow: OKF Knowledge Workflow

This project keeps persistent engineering context in the `knowledge/` Open Knowledge Format (OKF) v0.2 bundle. For substantial work, use the durable development loop in `docs/durable-development-methodology.md`.

## ChatGPT Codex and compatible agents

`AGENTS.md` is the shared instruction entry point for ChatGPT Codex, Cursor, and other compatible coding agents. In this distribution repository, read `template/.clineflow/PROCEDURES.md` as the operational workflow and `template/.clineflow/WORKING_WITH_CODEX.md` for the Codex workflow; installed projects receive the same guides at `.clineflow/`. The same OKF knowledge contract also applies to Cline, Claude Code, Copilot, and Windsurf.

## Updating ClineFlow

When the user says “Please update ClineFlow.”, treat that request as authorization to read the current instructions at [the authoritative ClineFlow repository](https://github.com/hassanvfx/clineflow), inspect the installed layout, and immediately run the permanent remote bootstrap with `--yes`:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes
```

Do not run any existing local updater first; legacy copies can overwrite themselves. Do not ask for redundant confirmation. Let migration, verification, and automatic rollback finish, then report the resulting version and preserved legacy artifacts. This authorization does not cover unrelated system changes or destructive cleanup, and safety failures must still stop the update.

## Removing ClineFlow

When the user says “Please remove ClineFlow.”, first run `./.clineflow/bin/uninstall --dry-run`, explain which managed files and rule blocks would be removed and which project knowledge and user content would be preserved, and ask for explicit confirmation. Only after that confirmation may you run the remover, using `--yes` only when the user has authorized the final removal. Do not treat the initial phrase as authorization to bypass this preview and confirmation.

## Knowledge Visor

Only when the user explicitly says “Please show me the ClineFlow dashboard.” or otherwise directly requests the ClineFlow dashboard or Knowledge Visor, invoke the installed project's `./.clineflow/bin/dashboard`. Never activate the optional runtime proactively during normal development, installation, validation, or commit preparation.

## Task knowledge rules

1. Before substantial work, run `./template/.clineflow/bin/knowledge sync`, then read `docs/durable-development-methodology.md`, all five generated `knowledge/clineflow_*.yml` views, and their linked journals. Summarize the current contract and next safe step before changing code.
2. For each substantial task, inspect `./template/.clineflow/bin/knowledge topics`, then create a topic-scoped stream with `knowledge journal new` or explicitly resume a known stream.
3. Every task journal is an OKF concept. Keep its YAML frontmatter valid, retain `type: Engineering Journal`, and update `generated.at` after meaningful changes.
4. Every published knowledge change creates an immutable `knowledge/updates/<topic>/<uuid>--<tenant>.yml` record. It names the tenant journal, explicitly reviews every ledger, and records unchanged ledgers as `unchanged`; run `knowledge sync` to rebuild local views. Never modify or delete a published update record.
5. Use `status: draft` while work is active and `status: stable` when it is complete. Do not add `verified` or `sources` unless they are factual.
6. Before starting or resuming work, search `knowledge/` first. If `docs/journals/` exists, search it too as read-only legacy context. Never create or update new work there.
7. Link related concepts with normal Markdown links. Update `knowledge/log.md` for material knowledge changes.
8. Follow the operating principles in `template/.clineflow/PROCEDURES.md`: state the task contract, execution boundary, handoff topology, relevant existing approaches, and planned proof before a substantial slice. Choose a single handoff only for one cohesive, independently verifiable slice; otherwise plan a milestone chain with explicit boundaries, local proof, dependencies, and one integrator responsible for composition and final end-to-end proof. Choose reversible details inside the authorized contract; ask before materially changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria. Record evidence and remaining judgment separately from planned proof.

## Commit workflow

When the user says “Please commit.” or otherwise asks to commit:

1. Update the active tenant journal with the implementation summary, decisions, tests, and next steps, then create an immutable update record.
2. Run `./template/.clineflow/bin/knowledge sync`, `./template/.clineflow/bin/validate-okf`, and `./template/.clineflow/bin/validate-knowledge-sync`, resolving all failures.
4. Stage the code and knowledge artifacts together, run `./template/.clineflow/bin/validate-knowledge-sync --staged`, then create a descriptive commit.

For changes to installed files, persistent formats, ownership, or required behavior, update the ClineFlow release manifest and either add the next migration or record and test that no migration is required. Run `./tests/certify-release.sh` before delivery.

## Knowledge navigation

- Start with `knowledge/index.md` and descend through `index.md` files for progressive disclosure.
- `docs/journals/` is optional legacy history; it is not part of the OKF bundle and must not be passed to `validate-okf`.
- For related codebases, keep projects as sibling folders under a common parent and refer to them as “sibling project `<foldername>`” (for example, `../backend-api`).

## Code quality

- Prefer focused modules (roughly 300–500 lines; refactor files over 1,000 lines).
- Keep documentation concise, factual, and linked to the concepts or files it describes.
