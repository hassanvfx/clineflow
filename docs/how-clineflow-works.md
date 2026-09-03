# How ClineFlow Works

ClineFlow makes project context durable by connecting native agent instructions, a Git-versioned Open Knowledge Format bundle, and a synchronized commit workflow.

## The instruction hook

Different coding agents read different project instruction files. ClineFlow installs the same marker-delimited workflow into each supported location:

| Agent | Project instruction file |
| --- | --- |
| Cline | `.clinerules` |
| ChatGPT Codex and compatible agents | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Cursor | `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Windsurf | `.windsurf/rules/clineflow.md` |

The block tells an agent where durable context lives, what to read before substantial work, how to maintain an Engineering Journal, what evidence is required, and how to close a task. Existing instructions outside ClineFlow's markers remain under project ownership.

## The durable development loop

1. **Recover context.** Read the five concise ledgers and follow their relevant journal links.
2. **Ground intent.** Create or resume an Engineering Journal and separate confirmed requirements from assumptions and open questions.
3. **Define proof.** State observable acceptance criteria and regression checks before claiming completion.
4. **Execute the agreed slice.** Keep decisions, discoveries, and failures in the active journal.
5. **Verify.** Run relevant checks and record factual outcomes.
6. **Handoff.** Refresh the current-session summary, timeline, and next safe step.
7. **Commit context with work.** Keep implementation and its current explanation in the same Git change set.

The complete operating manual is [Durable Development Methodology](durable-development-methodology.md).

## Engineering Journals

Substantial work receives a concept under `knowledge/journals/<task-name>.md`, created from `knowledge/journals/TASK_TEMPLATE.md`. Its YAML frontmatter identifies it as `type: Engineering Journal` and records its title, description, tags, lifecycle status, and generation metadata.

The Markdown body records the goal, chronological work log, decisions, testing, open issues, and related concepts. The journal is `draft` while work is active and `stable` after the recorded task is complete.

## What “Please commit” means

When the user says:

```text
Please commit.
```

the shared agent contract requires more than running `git commit`:

1. Update the active journal with the implementation summary, decisions, tests, and next steps.
2. Reconcile the goals, specification, verification, last-session, and timeline ledgers.
3. Give all five ledgers, the active journal, and the newest timeline event one shared timestamp.
4. Reference the active journal from every ledger and update `knowledge/log.md`.
5. Run OKF, knowledge-sync, project-specific, and whitespace checks.
6. Stage code and durable knowledge together.
7. Run `./.clineflow/bin/validate-knowledge-sync --staged`.
8. Create a descriptive commit only after those checks pass.

This makes the repository itself the handoff. Another person or agent can recover the goal, constraints, evidence, and next action without reconstructing an old chat.

## Why five ledgers and journals both exist

Journals contain detail. The five YAML ledgers remain deliberately compact so a new agent can orient itself without loading the full project history:

- Goals explain the current outcomes and priorities.
- Specification records agreed behavior, assumptions, constraints, and open decisions.
- Verification records proof and outstanding checks.
- Last session records the current state and next safe step.
- Timeline preserves how the project reached that state.

Normal Markdown links connect these indexes to journals and evidence. There is no proprietary database or embedding service in the default workflow.

## Self-documentation without invented certainty

ClineFlow does not treat a chat transcript as documentation and does not allow an unanswered question to silently become a requirement. The agent records concise decisions and factual test outcomes, keeps unresolved issues visible, and asks the user when a choice would materially change the contract.

The synchronization validator applies when a change set edits a journal, documentation, or the knowledge base. Code-only changes do not manufacture a knowledge update. Optional dashboard reports are generated views and do not participate in the five-ledger synchronization gate.

For field-level details, legacy compatibility, and validation commands, read the [OKF knowledge workflow](okf-knowledge-workflow.md). For Codex-specific prompts, read [Working with ChatGPT Codex](../template/.clineflow/WORKING_WITH_CODEX.md).
