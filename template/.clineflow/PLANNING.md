# Adaptive Planning and Handoffs

Use this guide for plans and Engineering Journals. The journal is the
canonical plan for substantial work. Create a separate `docs/plans/` document
only when the plan is long-lived, externally shareable, or unusually large;
link it from the journal and keep decisions, work log, and verification in the
journal.

## Plan at the smallest useful depth

Every substantial plan records the following core, in the Engineering Journal:

1. **Goal and task contract.** State the intended outcome, observable success
   criteria, constraints, non-goals, and known assumptions.
2. **Execution boundary.** State what is authorized, affected interfaces or
   owners, relevant side effects, and escalation conditions.
3. **Handoff topology.** Choose a single handoff for one cohesive,
   independently verifiable slice. Otherwise use a milestone chain with a
   named integrator responsible for composition and final end-to-end proof.
4. **Existing approaches and planned proof.** Ground material choices in the
   project or established evidence; distinguish deterministic checks,
   integration checks, and remaining judgment.
5. **Decisions, pending decisions, verification results, open issues, and
   references.** Keep each category separate so a later agent can recover what
   is settled, blocked, observed, and still required.

A single-handoff plan needs one owned and excluded boundary, entry condition,
inputs and outputs, local acceptance proof, downstream next action, and
rollback or escalation condition. Do not add milestones merely because a task
has several files or agents.

For a milestone chain, give every independently testable stage that same
contract plus its dependency and downstream consumer. Add a dependency graph
only when ordering or composition is not clear in prose. The integrator
accepts local proof before composition and records separate end-to-end proof.

## Add detail only when it prevents a mistake

For long-lived or high-risk work, add the applicable modules below. Omit them
for a cohesive small change.

- **Context and evidence:** the observed problem, source links, prior attempts,
  and what is inferred rather than established.
- **Locked decisions:** material choices, alternatives, rationale, and
  consequences.
- **Architecture or data flow:** interfaces, ownership, dependencies,
  compatibility, and rollback boundaries.
- **Stage cards:** responsibilities, contracts, changes, dependencies,
  consumers, proof, and rollback for each milestone.
- **Execution guide:** safe ordering, spend or authority gates, simulation or
  rollout phases, and explicit stop conditions.

Line-number anchors, exhaustive file inventories, estimates, research
citations, budgets, and diagrams are optional evidence. Use them when they
make a material contract, implementation boundary, or proof executable; never
use them as decorative plan bulk.

## Decision gates

Resolve discoverable facts before treating anything as a decision. For a
routine reversible implementation detail inside the authorized contract, make
the choice and record it when material.

For an unresolved choice that changes requirements, external behavior,
authority, ownership, dependencies, acceptance criteria, or a dependent
handoff, add a **Pending Decision**. Include:

- a stable identifier and the exact decision needed;
- why it matters and the handoff or scope it blocks;
- the responsible user, owner, or authorized delegate;
- viable options with available evidence; and
- the next action and whether unrelated work may proceed.

Do not silently turn an assumption or a delegated research result into an
approved requirement. A delegate may investigate or recommend when authorized;
only the assigned decision owner resolves the gate. Pause the dependent work,
not independent authorized work.

Use **Decisions** only for resolved material choices. Use **Open Issues** for
factual blockers, risks, failures, and follow-up work; do not hide a pending
approval there. Use **Verification Results** only for commands, observations,
and known coverage gaps after checks run.

## Journal lifecycle

Before implementation, write the core plan and any applicable detail modules.
During work, append factual work-log entries and update decisions, pending
decisions, and open issues as their state changes. Keep planned proof separate
from its outcomes. At handoff, record the next safe action, remaining judgment,
and evidence needed by the next owner. Publish knowledge updates and rebuild
the ledgers according to the normal ClineFlow workflow.
