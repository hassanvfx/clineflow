# Durable Development Methodology

Durable development keeps the decisions, evidence, and next action needed to continue work inside the project rather than inside a temporary conversation. It is a manual for people and coding agents, independent of language, framework, editor, or provider.

## The durable development loop

1. **Recover context.** Read this manual, the five `knowledge/clineflow_*.yml` indexes, and their relevant journal links before proposing or changing work.
2. **Ground intent.** Create or resume an Engineering Journal. Distinguish confirmed requirements from assumptions, constraints, non-goals, edge cases, and unanswered questions. Do not turn an unanswered question into an implementation choice.
3. **Define proof.** State observable success criteria and regression checks before implementation. A claim that something “works” is not evidence.
4. **Execute the approved slice.** Implement only what the current contract supports. Capture material decisions, discoveries, failures, and changes in the journal.
5. **Verify and record evidence.** Run the agreed checks. Record factual outcomes, including failures and gaps, and link the evidence from the verification index.
6. **Handoff deliberately.** Update the current-session summary and timeline so a new person or agent can recover the contract, evidence, and next safe step without reading an old chat.
7. **Commit context with work.** Update journals and indexes before validation and commit, so the repository carries code and the explanation for it together.

## Master indexes

The YAML files under `knowledge/` are the front door to project context. They are concise and referential; Engineering Journals hold the detailed narrative and evidence.

| File | Update it when | It should answer |
| --- | --- | --- |
| `clineflow_specification.yml` | Behavior, constraints, assumptions, non-goals, or open questions change. | What have we agreed to build, preserve, or avoid? |
| `clineflow_verification.yml` | A check is defined, run, passed, failed, or blocked. | What proves completion, and what evidence exists? |
| `clineflow_goals.yml` | Outcomes, priorities, measures, or blockers change. | Why are we doing this work now, and what is success? |
| `clineflow_last_session.yml` | A material change or handoff occurs. | What changed last, what is true now, and what should happen next? |
| `clineflow_timeline.yml` | A project-relevant agent interaction, decision, repository event, or handoff occurs. | How did the project reach its current state? |

Use repository-relative paths in `journal_refs`, `evidence_refs`, `next_step_refs`, and timeline `refs`. Keep index summaries short enough to scan; put explanation, rationale, and detailed test output in the linked journal.

## Operating rules for agents

Before substantial work, an agent must read the indexes and linked journals, summarize the current contract and next safe step, and identify ambiguity. During work it updates the active journal first, then the affected indexes. At handoff it updates `clineflow_last_session.yml` and appends a timeline event. At commit it updates the journal, indexes, and `knowledge/log.md`, validates the bundle, and commits the code and durable context together.

If a requested decision is not covered by the specification, the agent stops implementation and asks for direction. It may document options, but it must not silently promote an assumption into an approved requirement.

## Evidence-first examples

### Product capability

A team wants to add an export option. The specification records supported formats, permission boundaries, excluded formats, and unresolved retention rules. Verification defines example exports, access checks, and regression coverage for existing downloads. The journal explains why the format boundary exists; the indexes link to it. A fresh agent can extend the work without treating a UI preference as a change to the data contract.

### Production defect

A service intermittently returns duplicate notifications. The journal records the reproduction, hypothesis, chosen fix, and rollback consideration. Verification names the regression test and production signal that confirm the repair. The timeline links the incident, fix, test result, and deployment handoff. A later agent can understand both the symptom and the evidence without reconstructing chat history.

### Dependency or platform migration

A project must move to a new runtime. Goals describe the migration outcome and compatibility deadline; specification preserves public behavior and states non-goals such as unrelated feature work. Verification lists build, test, deployment, and rollback criteria. The last-session index gives the next migration step and links to the detailed journal.

## Usage and cost ledger

Timeline events may include a `usage` object only when a provider, agent, API, or export explicitly supplies exact values. Record provider, model, input/output/reasoning tokens, cost, currency, source, and capture time. Otherwise set `usage_capture: unavailable` and omit the `usage` object. Never estimate tokens or prices.

This rule is provider-neutral: Codex, Claude Code, Cline, Cursor, Copilot, Windsurf, and future agents can participate even when they expose different telemetry. Usage data is observational metadata, never proof of completion or a required workflow gate.

## Maintenance standard

Prefer a concise current state over a transcript. Preserve historical detail in journals and timeline events. Keep all claims factual, link evidence, and make the next recommended step specific enough for another person or agent to act safely.

Source inspiration: *ClineFlow Canonical Technical Session - Script & Demo Runbook* (internal presentation source, 2026). This manual intentionally generalizes its lessons and does not reproduce its presentation script or implementation examples.
