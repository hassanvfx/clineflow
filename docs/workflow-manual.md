# ClineFlow Workflow Manual

This is the practical, end-to-end guide for working with ClineFlow in an
installed project. ClineFlow keeps engineering context beside the code so the
next person or agent can recover the contract, proof, and next safe action
without reconstructing an old chat.

## The main user flows

### 1. Install once, then verify

Ask a coding agent:

```text
Please install ClineFlow by following the instructions provided at https://github.com/hassanvfx/clineflow
```

Or install directly from the project root on macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/template/.clineflow/bin/install | bash
./.clineflow/bin/doctor
```

The installer adds a managed `.clineflow/` runtime, a `knowledge/` bundle, and
marker-delimited guidance to supported agent instruction files. It preserves
existing instructions outside those markers, user-authored knowledge, and
unrelated files. If Git is available, it can initialize a repository but never
creates a commit, remote, identity, or branch policy.

### 2. Start or resume a substantial task

Describe the desired outcome normally. For substantial work, the agent must:

1. Synchronize and read the five knowledge ledgers plus relevant journals.
2. Search current `knowledge/` and read `docs/journals/` only as legacy,
   read-only context.
3. Create a new tenant-scoped journal stream or explicitly resume one.
4. Write the task contract, execution boundary, handoff topology, existing
   approaches, and planned proof before implementing.

Useful prompt:

```text
Read AGENTS.md and knowledge/index.md, recover the relevant context, state the
task contract and next safe step, then propose the implementation plan.
```

For a routine, reversible edit, a full journal workflow is not necessary. The
agent should still follow local project rules and ask before changing an API,
ownership boundary, dependency, acceptance criterion, or other approved
contract term.

### 3. Choose the handoff topology before work starts

Every substantial plan chooses one of two shapes.

| Choose | When it fits | Required ownership |
| --- | --- | --- |
| **Single handoff** | One cohesive, independently verifiable slice with one owner and one integration boundary. | One owner records the boundary, proof, and next safe action. |
| **Milestone chain** | Two or more slices have separate contracts, consumers, proofs, ordering dependencies, or composition risk. | One named integrator accepts each milestone, composes them, and owns final end-to-end proof. |

Do not split work merely because it touches many files, is large, or involves
several agents. Split when the boundary itself is meaningful and testable.

For a milestone chain, each milestone records:

- Its owned and excluded boundary.
- Entry condition, inputs, and outputs.
- Local acceptance proof and factual result.
- Downstream consumer and dependencies.
- Responsible contributor, named integrator, and escalation or rollback
  condition.

Use independent, linked journal streams for concurrent milestones. Tenant
streams prevent authors from colliding; they do not automatically make a
journal a module or establish a parent/child data model. The integrator must
still prove that the completed components compose in the intended order.

### 4. Implement, verify, and hand off

Implement only the approved slice. Keep material decisions, discoveries,
failed approaches, interface changes, and verification evidence in the active
journal.

A contributor can hand off a milestone only with its declared evidence. The
integrator then verifies the stated inputs and local proof, runs the required
composition checks, records gaps, and closes the parent outcome only after the
end-to-end checks pass.

At any handoff, update the durable context with what changed, evidence,
remaining judgment, escalation conditions, and the next safe action. The
five-ledger views and timeline make this discoverable without reading a prior
conversation.

### 5. Commit the work and its explanation together

When ready, say:

```text
Please commit.
```

The agent updates the journal, publishes an immutable update record, rebuilds
the local views, runs the required validators and project checks, stages code
and knowledge together, verifies staged knowledge synchronization, and only
then creates a descriptive commit.

The minimum knowledge gates are:

```bash
./.clineflow/bin/knowledge sync
./.clineflow/bin/validate-okf
./.clineflow/bin/validate-knowledge-sync
git add <implementation-and-knowledge-files>
./.clineflow/bin/validate-knowledge-sync --staged
```

When a change affects installed behavior, persistent formats, managed
ownership, or required workflow rules, the release workflow also updates the
manifest, decides whether a migration is required, and runs the lifecycle
certification suite before delivery.

### 6. Maintain or inspect the installation intentionally

To update an installed project, say:

```text
Please update ClineFlow.
```

That authorizes the current remote bootstrap. Do not run an old local updater
first:

```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --yes
```

To remove ClineFlow, say:

```text
Please remove ClineFlow.
```

The agent must first run `./.clineflow/bin/uninstall --dry-run`, explain the
managed runtime and instruction blocks it would remove, and obtain explicit
confirmation. It preserves `knowledge/`, legacy journals, user-authored
documentation, text outside managed markers, and unrelated files.

To inspect the optional local report, say:

```text
Please show me the ClineFlow dashboard.
```

The Knowledge Visor is dormant until this explicit request. Its first use
shows its optional runtime and asset plan before any download or report
generation.

## The durable knowledge model

Start navigation at `knowledge/index.md`. The five local, regenerated ledgers
provide a compact project view:

| Ledger | Answers |
| --- | --- |
| `clineflow_goals.yml` | Why is this work important and what is success? |
| `clineflow_specification.yml` | What behavior, constraints, and open questions apply? |
| `clineflow_verification.yml` | What checks and evidence support completion? |
| `clineflow_last_session.yml` | What is true now and what should happen next? |
| `clineflow_timeline.yml` | How did the project reach its current state? |

The detailed record is an Engineering Journal under:

```text
knowledge/journals/<topic>/<stream-uuid>--<tenant-id>.md
```

It is `draft` while active and `stable` when complete. Every published
knowledge change also creates an immutable record under:

```text
knowledge/updates/<topic>/<record-uuid>--<tenant-id>.yml
```

That record captures the journal snapshot, stream, every ledger review, a
timeline summary, and a log summary. Never edit or delete a published record;
publish a corrective record instead.

## A complete milestone-chain example

Suppose a product needs a protected export capability.

1. **Planning:** identify three real boundaries: export format generation,
   authorization, and UI activation. Select a milestone chain because each has
   a distinct interface and proof.
2. **Milestone A — exporter:** own format generation and fixture tests; output
   a stable export interface. It does not decide permissions or UI placement.
3. **Milestone B — authorization:** own policy enforcement and denied-access
   tests; consume the export interface without changing its format contract.
4. **Milestone C — UI:** own the user interaction and client-side states;
   consume the protected export boundary.
5. **Integration:** the named integrator verifies each milestone's evidence,
   composes them in dependency order, tests allowed and denied end-to-end
   exports, records any limitations, and makes the final handoff.

If the work were only an internal formatting fix in the exporter with one
regression test, it would be a single handoff instead.

## Operating boundaries

ClineFlow gives an agent room to make reversible implementation choices inside
an approved contract. It does not authorize silent changes to requirements,
public behavior, authority, ownership, dependencies, or acceptance criteria.
The agent must surface those choices for direction.

Likewise, deterministic commands prove the rules they encode; they do not
prove that a product decision is correct or that all integration risks are
covered. Record both the evidence and the remaining judgment.

## Useful commands

| Need | Command |
| --- | --- |
| Check installation health | `./.clineflow/bin/doctor` |
| Rebuild local knowledge views | `./.clineflow/bin/knowledge sync` |
| List known topics | `./.clineflow/bin/knowledge topics` |
| Start a journal stream | `./.clineflow/bin/knowledge journal new --topic <slug> --title "<title>"` |
| Validate OKF structure | `./.clineflow/bin/validate-okf` |
| Validate knowledge synchronization | `./.clineflow/bin/validate-knowledge-sync` |
| Preview removal | `./.clineflow/bin/uninstall --dry-run` |
| Inspect dashboard state | `./.clineflow/bin/dashboard doctor` |

## What ClineFlow does not do

It does not replace review, testing, product judgment, or normal Git practice.
It does not host your project knowledge, require a particular coding agent, or
turn an unresolved assumption into a requirement. Its job is to make the
engineering context, proof, and next action durable and reviewable.

## Further reading

- [Installation and lifecycle](installation-and-lifecycle.md)
- [How ClineFlow works](how-clineflow-works.md)
- [OKF knowledge workflow](okf-knowledge-workflow.md)
- [Durable development methodology](durable-development-methodology.md)
- [Knowledge Visor](knowledge-visor.md)
- [Release process](releasing.md)
