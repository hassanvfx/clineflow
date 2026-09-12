# Knowledge Visor: staged development plan

Status: execution in progress, 2026-09-12. M0–M3 are implemented and locally
verified; M4–M5 remain staged work. No public launch is claimed by this document.
Decisions and evidence live in the linked
[Engineering Journal](../../knowledge/journals/knowledge-visor-atlas/90ace635-d5f1-44ba-8cb1-4a337aae028f--t-0e3938282b92b9ed23e44b822569ea4a.md).

Read the [scientific brochure brief](knowledge-visor-brief.md) first. It governs
fixed project identity and snapshot metadata, one information hierarchy, four
publication-like chapters, and evidence-serving visuals. This refinement supersedes
earlier suggestions that tabs should have independent visual personalities or
that a graph must dominate Workspace.

## Product thesis

Make a project's engineering memory explorable: what happened, why it changed,
what was learned, and which records support those conclusions. Attention on
Hacker News is a possible outcome, not an acceptance criterion or a promise.

Initial users are developers returning to an agent-assisted project and
maintainers reviewing its decisions. The initial input is ClineFlow/OKF knowledge,
not arbitrary repositories with no recorded history. Explain this prerequisite
at first use. Git activity alone does not reconstruct intent.

| Developer job | Useful outcome | Proposed study task |
| --- | --- | --- |
| Resume work | Recover current intent, constraints, and unresolved decisions | Identify the next recorded action and its source |
| Understand a change | Trace the original decision and recorded replacement | Explain why a decision changed, with evidence |
| Avoid repeating mistakes | Find a bounded, reusable Spark | Locate a relevant learning and a limitation |
| Review or hand off | Inspect proof and share a frozen report | Distinguish verified, claimed, and unrecorded outcomes |

## Evidence and lessons from the existing product

- The [earlier dashboard journal](../../knowledge/journals/knowledge-dashboard.md)
  records dense graph labels, misleading ledger-reference connections, and the
  eventual removal of the Atlas. Do not repeat that all-nodes overview.
- The current collector excludes generated additive ledgers while some downstream
  consumers still expect legacy goal fields. Reconcile the intake and presentation
  paths before treating empty sections as absent knowledge.
- The frozen Ad Crush sample contains captured projections and committed journals;
  its manifest distinguishes those origins. It is not a pure commit snapshot.
- Existing source hashes and separate facts/observations/presentation artifacts
  are useful foundations. Hashes prove byte identity, not claim correctness.
- Existing PDF output is a text-oriented companion, not faithful browser printing
  of the HTML. Export fidelity remains a planned deliverable.

## Experience contract

The shared masthead shows project title, generated date/time and timezone, full
report range, captured revision, latest captured commit, and snapshot condition.
The brief defines provenance, missing/redacted states, and generation/capture/
commit/event dates. Never use live host metadata for a frozen sibling fixture.

Tab order: **Workspace → Sparks → Activity → Evidence**.

| Surface | First read | Progressive detail |
| --- | --- | --- |
| Workspace | Compact five-ledger context, current brief, workstreams | Focused graph/list, one-hop relationships, journal access |
| Sparks | A small ranked collection of source-bound project learnings | Origin, development, counterevidence, limits, related records |
| Activity | Spacious Story chronology with chapters and event-specific cards | Explore time lanes, range filtering, recorded change chains |
| Evidence | Claims, support, unknowns, artifacts, source provenance | Exact passages, verification records, white-paper preview/download |

One main surface plus one reusable read-only reader. Modal breadcrumbs, Back,
Escape, focus restoration, search, and deep links retain context. No nested
modal stack. Journals remain reachable without traversing a graph. Story is
the default timeline; Explore is for time comparison, with equivalent list access.

Visual language: warm paper/ink light theme, deliberately designed charcoal dark
theme, restrained cobalt/indigo gradients, consistent SVG icons, fine rules, and
generous spacing. Labels and shapes supplement color. Short transitions explain
selection and then settle; reduced-motion preferences are respected. No idle
force animation. Snippets, diffs, and causal arrows require captured evidence.

## Data and observations harness

Pipeline: immutable capture → normalized facts/typed graph → agent observations
and candidate Sparks → structural validation and semantic review → presentation
→ offline HTML and report artifacts.

1. Separate stable entity IDs from revision hashes. Preserve source path, exact
   passage locator, captured bytes/hash, recorded time, event time when known,
   capture time, parser version, and observation generation metadata.
2. Distinguish recorded relations, rule-derived relations, and interpretations.
   Reuse explicit update `revises`, `retracts`, and `resolves` metadata; generic
   synchronization links are not meaningful dependency or causality edges.
3. Require origin/overall/recent/synthesis journal observations, or an explicit
   unavailable reason. Coverage includes every journal without forcing a Spark.
4. A Spark contains learning, scope/limits, origins, development, supporting and
   challenging passages, related records, synthesis time, and evidence state:
   emerging, supported, contested, or superseded. No invented confidence scores.
5. Validate schemas, source identity, exact locators, relation endpoints, coverage,
   chronology consistency, duplicate IDs, and source/observation separation.
   Evidence adequacy and generalization remain semantic judgments, not JSON proof.
6. Return structured errors with field path, rule, reason, and repair guidance.
   Proposed limit: two repair attempts; unresolved candidates are withheld and
   reported as incomplete. Do not conceal failure or require a minimum Spark count.
7. Treat journal content as untrusted data, never instructions. Test prompt
   injection, HTML/script payloads, unsafe links, false overrides, missing dates,
   contradictory evidence, valid-but-irrelevant citations, and stale source hashes.
8. Cache accepted observations against exact inputs and generator versions.
   Deterministic rendering does not imply repeatable LLM generation. Direct CLI
   generation remains an honest facts-only fallback without an agent provider.

Keep graph and observation schemas report-owned. No canonical graph database,
background agent, provider credential requirement, live backend, or automatic
write-back to journals. Future reuse by agents consumes the same cited artifact;
accepting a lesson into canonical knowledge is a separate authorized action.

## Milestone chain

Planning delivery is one documentation handoff. Future implementation is a
milestone chain: M0 → M1 → M2 → M3 → M4 → M5. The implementing primary agent is
the integrator and contributor for M0–M4 unless explicitly reassigned; the user
owns public release permission and human-facing launch participation in M5.

| Stage / owned boundary | Entry and inputs → output / consumer | Local proof | Stop or rollback |
| --- | --- | --- | --- |
| M0: factual intake and report identity; no UI redesign | Existing fixtures + source records → reconciled snapshot, metadata contract, baseline tasks for M1 | Production/fixture agreement; metadata traces to captured sources; deduplicated journals/events; missing fields diagnosed | Retain prior fixture and report; stop if source ownership is unclear |
| M1: graph/Sparks contracts; no new canonical schema | M0 snapshot → typed graph, observation schema, reviewed reference cases for M2 | Positive and adversarial validator tests; every visible citation resolves; human review distinguishes support from irrelevant citation | Withhold invalid interpretations; preserve facts-only report |
| M2: publication shell and one journey; no full-product expansion | M0 metadata + M1 cases → shared masthead/tokens/components, Story chapter, Spark, purposeful figure, reader for M3 | Metadata/browser assertions, coherent light/dark screenshots, keyboard reader, no-network run; measured renderer comparison | Keep list/story if graph fails readability; gate dependencies before installation |
| M3: compose four tabs; no external integrations | M2 interaction contract → connected search/filter/deep-link state and all source readers for M4 | Back/forward, filter persistence, modal restoration, sparse/empty/conflicting examples; full tour regression | Revert affected presentation slice without altering captured sources |
| M4: release hardening; no publication | M3 candidate → portable report, faithful PDF, sanitized candidate, benchmark evidence for M5 | Offline/file viewing, export link integrity, PDF visual/Unicode checks, license/checksum review, release and lifecycle certification | Fail closed on privacy/export corruption; preserve previous completed report |
| M5: launch readiness; user permission required | M4 evidence + approved public dataset → no-signup playable demo, tutorial, factual technical notes | New-user study and manual public-artifact review; user approves exact content and destination | Do not publish private fixture, recruit, or post without explicit authorization |

Before changing installed payloads, update release/component manifests and
record/test migration applicability. Refactor oversized renderer modules along
pipeline boundaries while retaining their tested CLI contracts. Existing dirty
worktree changes must be preserved. Full end-to-end acceptance belongs to the
integrator after composition, not to individual stage tests.

## Executable stage checklist

Each stage starts after its predecessor's inputs and local proof are accepted.
The primary agent records outputs, commands/results, remaining judgment and next
action in the journal. These checks supplement the ownership, exclusions,
consumers and rollback boundaries above.

### M0 — Establish a truthful report model

- Trace the real collector and fixture importer into the same normalized contract;
  support additive ledger items and explicitly preserve unresolved alternatives.
- Define identity, generation/capture time, coverage categories/limits, captured
  HEAD/baseline, latest captured commit, and snapshot condition per the brief.
- Freeze relevant update relationships without counting historical journal copies
  as new journals. Separate source spans, stable IDs and revision hashes.
- Test missing metadata, no Git, detached HEAD, dirty/unknown state, mixed origins,
  redaction, partial history and absent dates. Assert no host metadata leakage.
- Handoff: normalized fixtures, documented field contract and passing intake tests.

### M1 — Build the observations and Sparks harness

- Define report-owned graph, journal observation, Spark and diagnostic contracts.
- Require origin/overall/recent/synthesis fields or explicit unknowns; do not infer
  coworkers from tenant IDs or override chains from chronology alone.
- Implement deterministic validation and the bounded repair protocol, reviewed
  semantic reference cases and a facts-only fallback.
- Handoff: accepted/rejected examples and citation/coverage/injection tests.
  Passing structural validation is never labeled semantic verification.

### M2 — Build the brochure shell and prove one journey

- Establish shared tokens, masthead, metadata strip, tabs, section headings,
  source links, status labels, figure captions and one reader.
- Render metadata from M0; project identity never depends on selected events.
  Show absolute dates/timezone and preserve unknown/redacted labels.
- Render one real chapter and linked Spark using reusable content components;
  trial visual adapters only where a relationship needs explanation.
- Test long titles, narrow screens, 200% zoom, both themes, keyboard-only reading,
  Escape/Back/focus return and masthead values against the captured fixture.
- Handoff: coherent screenshots plus a working claim-to-source journey. Review
  before expanding across every tab; a list remains available without the graph.

### M3 — Complete the four connected chapters

Implemented in the local frozen-record experience: compact Workspace and Sparks
surfaces, grouped and collapsible Activity, source-first readers, direct source
coverage, deep links, theme toggle, and on-demand search. Browser review and
fixture regression are recorded in the M3 journal; PDF fidelity remains M4 work.

- Workspace: abstract, read-only context, journals/workstreams and focused figures.
- Sparks: consistent learning cards, evidence states, scope and source reader.
- Activity: Story first, Explore lanes where useful, dates, filters and collapsed
  routine details; event grouping is not an assertion of causality.
- Evidence: claim/source matrix, verification, unknowns, method and provenance.
- Complete cross-tab selection, search, deep links, browser history, empty states,
  source readers and optional replayable tour with the same component set.
- Handoff: browser tests, full-fixture journey and sparse/conflict regressions.
  Tour or graph failures cannot prevent direct journal access.

### M4 — Export, harden and certify

- Build print HTML from the same prepared model and render a faithful PDF after
  resolving any dependency gate. Full report scope stays distinct from UI filters.
- Check downloads, source/hash binding and artifact manifests. Visually inspect
  typography, Unicode, figures, captions, tables, page breaks, references and
  masthead metadata. Signature-only PDF tests are insufficient.
- Run accessibility checks and manual keyboard/screen-reader review, documented
  benchmarks and actual no-network/file-protocol tests with valid pinned assets,
  not placeholder fonts or marker-only assertions.
- Update release/component manifests and test migration applicability. Observe
  dashboard tests and full lifecycle certification through completion; record
  failed or unexecuted checks explicitly.
- Handoff: local report and evidence log. Publication remains separately gated.

### M5 — Optional public release preparation

Requires user approval of dataset, destination and external participation. Use
the privacy and usability gates below. M5 is not required to call the local
scientific brochure implementation complete.

## SOLID implementation boundaries

Use small cohesive modules rather than introducing a framework for its own sake.

| Responsibility | Contract and boundary |
| --- | --- |
| Source collection/normalization | Captured files/Git records → facts; no prose generation or DOM concerns |
| Observation validation | Facts + candidates → accepted data/diagnostics; no source mutation or UI |
| Presentation assembly | Pure mapping into shared metadata/chapter/reader models; no Git/filesystem access |
| Browser shell/state | Navigation, filters, focus, theme and reader lifecycle; no independent factual inference |
| Visualization adapters | Narrow render/select/destroy interface and equivalent list; replacements preserve IDs and selection semantics |
| Artifact generation | Same prepared model → HTML/PDF; cannot change observations or canonical facts |

Apply single responsibility, extension through adapters, substitutable renderers
with contract tests, narrow interfaces, and dependency inversion around normalized
data. Prefer roughly 300–500-line modules; split oversized files as their owned
boundaries are touched. Preserve tested CLI entry points and offline behavior.

## Stage-level execution loop

Recover contract → simulate edge cases → write failing proof → implement bounded
slice → run local proof → inspect integrated output → record evidence → hand off.
One correction pass follows the M2 design review; further changes address a named
defect or unmet acceptance criterion. Simulation is planning, not empirical proof.

## Visualization selection gate

Prototype custom HTML/CSS/SVG for Story; compare vis-timeline for Explore and
Cytoscape.js for focused relationships. Reuse ECharts only for useful quantitative
views. These are candidates, not approved new dependencies. Measure local-file
compatibility, payload size, labeling, keyboard fallback, print behavior, licenses,
and pinned-asset lifecycle before selecting. A simpler SVG view may win at the
visible neighborhood size; the full graph need not be drawn at once.

References: [vis-timeline examples](https://visjs.github.io/vis-timeline/examples/timeline/),
[Cytoscape.js](https://js.cytoscape.org/),
[ECharts renderers](https://echarts.apache.org/handbook/en/best-practices/canvas-vs-svg/).

## Tour and real-user proof

Build a skippable, replayable tour with four anchored stops, not a blocking
onboarding overlay. Every stop operates on the actual captured records:

1. Workspace: understand the project's current work and choose one question.
2. Sparks: inspect a useful learning with its limitations clearly visible.
3. Activity: follow its documented origin and subsequent development.
4. Evidence: open the exact passage and verification; optionally export the report.

Pick the actual story after M0/M1 review. Do not script a cache-fix narrative or
decision reversal merely because it would make a good demonstration. Empty or
incomplete data disables the relevant tour stop with an explanation.

Proposed formative study, subject to user approval: five developers unfamiliar
with the sample, three tasks (resume, explain change, inspect Spark evidence),
counterbalanced against reading/searching the same journals. Capture correctness,
completion time, assistance, and misunderstandings locally with consent. Proposed
go/no-go: at least four of five complete each task without help within two minutes,
and no observed confusion between interpretation and recorded fact. This is a
small usability signal, not statistical proof or a public speedup claim.

Benchmark 100/1,000/10,000-event fixtures with bounded visible neighborhoods.
Proposed engineering targets: first useful view within two seconds on the named
reference machine for the 1,000-event fixture; p95 local selection/filter response
under 200 ms; readable fallback at 10,000. Record machine, browser, bytes, and test
method; no scale claims until measured. Test narrow layouts, 200% zoom, contrast,
keyboard-only navigation, reduced motion, focus, and screen-reader alternatives.

## Simulated execution review and stop conditions

- Attractive demo, incorrect ledger intake: M0 reconciliation precedes styling.
- Spark cites a real but irrelevant passage: semantic reference cases complement
  deterministic citation checks; visible label never says validator-proven truth.
- Dense graph recreates the prior failed Atlas: M2 requires focused neighborhoods
  and a successful task, with Story/list retained as the fallback.
- Missing historic records create invented evolution: show missing coverage and
  distinguish synthesis date from the dates of its evidence.
- Local fixture leaks into public demo: M5 has a separate publication gate;
  stripping author metadata alone is insufficient. Inspect raw embedded JSON,
  source prose, paths, HTML, PDF, snippets, and linked/downloadable artifacts.
- Endless polish prevents learning: stop at the M2 journey for review, then
  refine once from task evidence before broadening. Do not call simulation testing.
- Library or PDF engine expands installation boundary: document options and obtain
  dependency approval before changing downloads or invoking new services.

## Hacker News readiness

The technical story is transparent, inspectable project memory: local artifacts,
source-linked synthesis, visible uncertainty, and useful navigation. A short
screen recording can show the journey, but the submission should lead to something
people can actually try. Document supported input, generation steps, limitations,
data flow, and the validation model alongside the example.

Show HN asks for a usable project with low barriers rather than a landing page;
it prohibits soliciting votes/comments. HN also prohibits generated or AI-edited
discussion text. The user should write the submission and responses personally;
this plan supplies technical preparation, not ready-to-post prose. See
[Show HN guidelines](https://news.ycombinator.com/showhn.html) and
[HN guidelines](https://news.ycombinator.com/newsguidelines.html).

Track observed task success and voluntary reports of real-project usefulness;
stars and traffic are secondary. Do not add analytics or recruitment without
permission. Virality cannot be guaranteed.

## Pending decisions

| ID / owner | Impact and options | Evidence / next action |
| --- | --- | --- |
| PD-1 / user | Public example: reviewed/redacted Ad Crush or a separately licensed public sample; blocks M5 only | Current fixture is authorized locally, not for publication; review every export and approve exact dataset/destination |
| PD-2 / user with implementing agent recommendation | New visualization/PDF dependencies versus existing assets/custom SVG; blocks dependency installation only | M2 comparison and M4 PDF fidelity requirements inform a pinned, licensed choice |
| PD-3 / user | Proposed study participants, consent and success thresholds; blocks recruitment/public performance claims only | Run internal tasks first, then approve a small external study without hidden telemetry |

Next safe implementation slice, after authorization: M0 source reconciliation
and a source-grounded reference story. This planning delivery does not activate
the dashboard, install dependencies, publish anything, or change runtime code.
