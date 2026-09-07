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
3. **Plan handoff topology.** Choose one handoff for a cohesive slice, or linked milestones with solid boundaries and one integrator for composition.
4. **Define proof.** State observable acceptance criteria and regression checks before claiming completion.
5. **Execute the agreed slice.** Keep decisions, discoveries, and failures in the active journal.
6. **Verify.** Run relevant checks and record factual outcomes.
7. **Handoff.** Refresh the current-session summary, timeline, and next safe step.
8. **Commit context with work.** Keep implementation and its current explanation in the same Git change set.

The practical reference is the [Workflow Manual](workflow-manual.md); the
[Durable Development Methodology](durable-development-methodology.md) defines
the underlying operating model.

## Engineering Journals

Substantial work receives a tenant-scoped stream under
`knowledge/journals/<topic>/<stream-uuid>--<tenant-id>.md`, created with
`knowledge journal new`. Its YAML frontmatter identifies it as
`type: Engineering Journal` and records its title, description, tags,
lifecycle status, tenant, topic, stream, and generation metadata.

The Markdown body records the goal, chronological work log, decisions, testing, open issues, and related concepts. The journal is `draft` while work is active and `stable` after the recorded task is complete.

## What “Please commit” means

When the user says:

```text
Please commit.
```

the shared agent contract requires more than running `git commit`:

1. Update the active journal with the implementation summary, decisions, tests, and next steps.
2. Publish an immutable update record that explicitly reviews all five ledgers.
3. Run knowledge sync, OKF, knowledge-sync, project-specific, and whitespace checks.
4. Stage code and durable knowledge together.
5. Run `./.clineflow/bin/validate-knowledge-sync --staged`.
6. Create a descriptive commit only after those checks pass.

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

The synchronization validator applies when a change set edits a journal, documentation, or the knowledge base. Code-only changes do not manufacture a knowledge update. Optional MCP dashboard reports are generated views and do not participate in the five-ledger synchronization gate.

For day-to-day instructions and handoff examples, read the [Workflow
Manual](workflow-manual.md). For field-level details, legacy compatibility,
and validation commands, read the [OKF knowledge workflow](okf-knowledge-workflow.md).
