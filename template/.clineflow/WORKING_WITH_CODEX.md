# Working with ChatGPT Codex

ClineFlow gives ChatGPT Codex persistent project context through the repository's shared `AGENTS.md` instructions and the native OKF bundle in `knowledge/`. It does not require a Codex plugin, SDK, or runtime.

## Start or resume a task

1. Read `AGENTS.md`, `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five `knowledge/clineflow_*.yml` indexes.
2. Follow the indexes' relevant journal references, then search `knowledge/` for related concepts. When present, search `docs/journals/` as read-only legacy context too.
3. Summarize the relevant context before changing code. For a substantial change, propose a concise implementation plan first.
4. Create or resume `knowledge/journals/<task-name>.md` from `knowledge/journals/TASK_TEMPLATE.md`.

## Work and deliver

- Keep the active Engineering Journal current with decisions, implementation notes, verification evidence, issues, and next steps. For every journal, documentation, or knowledge-base change, reconcile all five ledgers with the journal and one shared timestamp, even when a ledger has no semantic change.
- Link the active journal from every ledger and update `knowledge/log.md`.
- Before delivery, run `./.clineflow/bin/validate-okf`, `./.clineflow/bin/validate-knowledge-sync`, the relevant project tests, and `git diff --check`.
- When the user asks to commit, stage code and knowledge together, require `./.clineflow/bin/validate-knowledge-sync --staged` to pass, then commit.

## Useful prompts for Codex

**Start work**

> Read `AGENTS.md` and `knowledge/index.md`, search relevant journals, summarize the current context, and propose the next safe step.

**Resume work**

> Find the active Engineering Journal in `knowledge/journals/`, inspect its next steps and related knowledge, then continue from the documented state.

**Close a task**

> Update the active Engineering Journal, reconcile all five ledgers and `knowledge/log.md`, run the OKF and knowledge-sync validators plus relevant tests, then show me the delivery summary.

**Update ClineFlow**

> Please update ClineFlow.

This prompt authorizes Codex to read the current repository instructions and invoke the universal updater with `--yes` immediately. Codex must wait for verification or rollback to finish and report the outcome; it must still stop on safety failures or requests for unrelated system changes.

## Diagnose the setup

Run `./.clineflow/bin/doctor` after installation or when Codex does not appear to have project context. It checks the shared instructions, required OKF files, Git repository, and structural validation without installing anything.
