# ClineFlow Procedures

## Operating principles

Use this loop for substantial work: recover context, specify the contract, define proof, execute an approved slice, record evidence, and hand off the next safe action.

1. **Intent guides code; code remains accountable.** Agents may produce code from intent, constraints, and specifications, but the resulting code remains a maintained artifact that needs review and verification. State observable success criteria and regression checks before implementation; review the resulting behavior and diff against that contract.
2. **Evidence makes knowledge compound.** Preserve reusable decisions, constraints, failed approaches, evidence, and next steps. Distinguish observations from hypotheses and unresolved questions. Record material learning in the tenant journal and immutable updates without copying chat transcripts.
3. **Autonomy operates within explicit boundaries.** Before a substantial slice, record its allowed scope, exclusions, affected interfaces, ownership, relevant side effects, and planned proof. When delegation is authorized, identify the integrator and the integration checks that remain.
4. **Minimize decisions entrusted to probabilistic reasoning.** Use agents for ambiguity and judgment; prefer established parsers, validators, calculations, permission controls, and execution commands for repeatable operations. State which checks are enforced and which conclusions still require judgment.
5. **Prefer established solutions when they fit.** For material architecture or dependency choices, investigate relevant project patterns and established approaches first. Record the option considered, why it fits or fails, and why a novel approach is warranted when chosen.

Choose reversible implementation details within the authorized contract. Ask before materially changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria; continue independent authorized work while awaiting direction.

Do not infer that generated code needs less accountability, isolated checks prove integration safety, deterministic checks prove the contract is correct or exhaustive, or every task requires exhaustive research, a dependency, or extensive documentation.

### Applying boundaries

- **Routine reversible choice:** choose an internal helper name or a local refactoring that preserves the approved behavior and checks; record the decision when it is material, without escalating it.
- **Contract-changing choice:** ask for direction before changing an external API, ownership boundary, dependency, acceptance criterion, or other authorized contract term.
- **Delegated slice:** document the delegated scope, its integrator, and the remaining integration checks. A delegated unit check is useful evidence, but the integrator still owns the end-to-end result.
- **Failed experiment:** record the attempted approach, factual result, reason it was rejected, and next safe action. Preserve the reusable learning rather than a chat transcript.

## Start or resume work

1. Run `./.clineflow/bin/knowledge sync`, then read `docs/durable-development-methodology.md`, `knowledge/index.md`, and all five generated `knowledge/clineflow_*.yml` views.
2. Follow relevant master-index references, then search `knowledge/` for related task journals, decisions, and references.
3. When present, search `docs/journals/` for relevant legacy context. Treat these files as read-only historical material.
4. Inspect `./.clineflow/bin/knowledge topics`, then create a topic-scoped journal with `knowledge journal new`; resume only a named stream that belongs to the pinned tenant.

## Specify, prove, and execute

1. In the active journal, state the intended outcome, success criteria, constraints, open questions, execution boundary, relevant existing approaches, and planned proof.
2. Work only within the authorized boundary. Keep material decisions, discoveries, failures, and integration gaps current in the journal.
3. Run the agreed deterministic checks and any required integration checks. Record factual outcomes separately from the planned proof, including failures and gaps.
4. Before handoff, make the next safe action, remaining judgment, and any escalation condition discoverable from the journal and five ledgers.

## Maintain OKF knowledge

- Keep every non-reserved Markdown document in `knowledge/` parseable with YAML frontmatter and a non-empty `type`.
- Reserve `index.md` for navigation and `log.md` for dated change history.
- Use Markdown links for relationships; broken links are acceptable when knowledge is not written yet.
- Record only factual provenance, verification, and lifecycle fields.
- Create one immutable `knowledge/updates/<topic>/<uuid>--<tenant>.yml` record for each published update. Every record explicitly reviews all five ledgers; unchanged ledgers are recorded as `unchanged` rather than rewritten. Run `knowledge sync` to rebuild local views.

## Commit

1. Update the active tenant journal and create an immutable update record.
2. Run `./.clineflow/bin/knowledge sync`, `./.clineflow/bin/validate-okf`, and `./.clineflow/bin/validate-knowledge-sync`.
3. Stage implementation, journals, and update records together, then run `./.clineflow/bin/validate-knowledge-sync --staged` before committing.

## Generate the optional Knowledge Visor

- Run `./.clineflow/bin/dashboard` only after an explicit user request for the ClineFlow dashboard or Knowledge Visor.
- First use previews and approval-gates all optional runtime and visual-asset downloads.
- Generated reports under `knowledge/dashboard/` are local presentation artifacts, not canonical OKF knowledge, and do not require five-ledger synchronization.
