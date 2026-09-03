# Working with ClineFlow

ClineFlow stores new persistent context as an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) v0.2 bundle in `knowledge/`.

## Daily workflow

1. Ask the agent to inspect `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five `knowledge/clineflow_*.yml` indexes before starting work.
2. For a substantial task, create `knowledge/journals/<task-name>.md` from `knowledge/journals/TASK_TEMPLATE.md`.
3. Keep decisions, testing evidence, progress, and next steps in that concept. Any journal, documentation, or knowledge-base change must reconcile all five ledgers, link the active journal from each, and use one shared timestamp even when a ledger has no semantic change.
4. At commit time, update `knowledge/log.md`, run `./.clineflow/bin/validate-okf` and `./.clineflow/bin/validate-knowledge-sync`, stage code plus knowledge together, and require `./.clineflow/bin/validate-knowledge-sync --staged` to pass before committing.

## Legacy journal discovery

Projects may have pre-OKF journals in `docs/journals/`. ClineFlow searches these files for historical context when they exist, but does not modify, migrate, or validate them. All new task documentation belongs in `knowledge/journals/`.

## Update ClineFlow

Tell your agent: “Please update ClineFlow.” The agent reads the current instructions from the authoritative repository and runs the universal updater with `--yes` without asking again. It reports the installed version and any preserved legacy artifacts after verification or rollback completes.

## Related projects

Keep related codebases as sibling folders beneath one common parent directory. When cross-project context is needed, ask the agent to inspect “sibling project `<foldername>`” (for example, `../backend-api`). This convention needs no ClineFlow configuration, symlinks, or generated workspace file.
