# Knowledge Visor — scientific brochure brief

Design direction confirmed by the user, 2026-09-11. The M0–M2 foundation is now
implemented locally; this brief continues to govern presentation as M3–M5 are
completed. The
[development plan](knowledge-atlas.md) governs stage boundaries and acceptance.

## Purpose

Produce a coherent, information-focused scientific brochure for a software
project: its identity, current recorded context, development history, accumulated
learning, and evidence. The interactive HTML and downloadable white paper are
two presentations of the same frozen knowledge record.

Scientific describes editorial discipline: provenance, explicit method, precise
labels, limitations, and cited findings. It does not imply peer review,
completeness, causal proof, or that agent interpretation is established fact.

Primary readers are developers returning to a project, maintainers reviewing
decisions, and collaborators receiving a handoff. Help them answer: What is this
project? What does this snapshot include? What changed? What did we learn? What
supports that conclusion?

## Fixed page hierarchy

1. **Project masthead:** project title, short factual description, report identity.
2. **Snapshot metadata:** generation date, coverage range, captured revision,
   latest captured commit, and snapshot condition.
3. **Utility controls:** search, explicit Light/Dark switch, Download white paper.
4. **Tabs:** Workspace, Sparks, Activity, Evidence, in that order.
5. **Section content:** consistent title, one-sentence purpose, local filters,
   primary information, supporting figures, and source links.
6. **Reader:** one shared modal for exact sources and deeper explanation.

The project name is always the page title, never replaced by a recent event,
Spark, generated slogan, or commit message. The masthead uses the same layout
across tabs; no promotional hero or oversized empty heading area. On small
screens it wraps in the same reading order without losing metadata.

## Metadata contract

| Field | Visible meaning and source rule |
| --- | --- |
| Project title | Recorded project identity; deterministic repository-name fallback, never agent-invented branding |
| Description | Recorded description or a clearly labeled cited summary; omit if unavailable |
| Generated | Absolute report-generation date/time with timezone; fixed at generation, never the browser clock |
| Coverage | Earliest/latest included dated records, with source categories and capture/history limits explained |
| Snapshot revision | Captured Git HEAD or fixture baseline, short SHA in masthead and full SHA in reader; label fixture baseline as such |
| Latest captured commit | Short SHA, subject, committed timestamp from captured history; independent of generation date or newest journal event |
| Snapshot condition | Recorded clean/working-tree-modified/unknown condition; frozen sample and mixed committed/projection provenance explicitly labeled |
| Report provenance | Report ID, source capture time, schema/generator versions, source/observation hashes in Evidence and report colophon |

Unknown, not captured, redacted, and not applicable are distinct states. An absent
Git value must not become a fabricated clean status. A frozen fixture must never
inherit the host repository's title, commit, branch, or dirty state. Detached HEAD,
empty Git history, mixed source origins, missing dates, and truncated history all
have explicit fixtures. Optional branch information is labeled as captured.

Dates remain stable in offline reports. Coverage bounds do not claim uninterrupted
coverage. Selected Activity ranges are labeled as view filters; they do not change
the masthead's full-report range or the existing PDF download's scope.

## Four chapters, one design system

| Tab | Required information | Permitted visual forms |
| --- | --- | --- |
| Workspace | Project abstract, five read-only ledger summaries, workstreams, journals, current intent and unknowns | Structured sections, definition lists, focused relationship figure with equivalent list |
| Sparks | Learning, scope, evidence state, origin/development, limitations and sources | Consistent learning cards; development trail when supported |
| Activity | Dated events grouped by workstream/chapter; source and recorded status | Spacious vertical Story; optional Explore lanes; evidenced comparisons/snippets |
| Evidence | Claim/source mapping, verification, gaps, method, provenance and artifacts | Tables, source excerpts, restrained status labels, captioned figures |

Static global context is reference information, not disabled form fields. Journals
are directly discoverable in Workspace and search. No source editing, live status
indicators, WebSockets, polling, or automatic source write-back.

## Editorial and visual rules

- One grid, spacing scale, type hierarchy, icon family, border treatment, and
  semantic palette across all tabs and the reader. No unrelated panel styles.
- Paper/ink light theme by default; charcoal dark theme with separately checked
  contrast. Restrained cobalt/indigo accent and subtle contextual gradients.
  Print uses a dedicated light treatment regardless of screen theme.
- Strong titles, readable body text, quiet metadata, monospaced identifiers/code.
  Long titles wrap; full text is available without hover. No raw JSON as labels.
- Every visualization answers a named question and has a title, caption, source,
  and text/list alternative. Axes, units, edge meanings and dates are explicit.
  Omit decorative charts, arbitrary KPIs, invented progress, random icons, and
  graphs created merely to occupy space.
- Evidence statuses use words plus shape/icon, not color alone. Never convert
  activity counts into quality, productivity, completion, or confidence scores.
- Hover is supplementary; keyboard/touch navigation works. Respect reduced
  motion; no perpetual animation or force layout.
- Two disclosure layers: main surface and one reader. Source navigation stays
  inside the reader with breadcrumbs/history and correct focus restoration.

## White-paper contract

Include cover metadata, abstract, recorded project context, Sparks, development
chronology, evidence, limitations/method, and references. Use the same approved
observations and facts as the web view. Include generation date, full coverage
range, captured revision, page numbers, figure captions, and report provenance.
Long journals may live in an appendix; enumerate included/excluded sources and
avoid claiming a complete archive when truncated.

Download white paper refers to a generated artifact with date and full scope
visible. Faithful HTML-to-PDF export must preserve Unicode, diagrams, tables,
references, and sensible page breaks. A PDF-engine dependency remains an explicit
implementation decision; the current text-only companion does not satisfy this
visual acceptance gate.

## Done means

A reader can identify the project and snapshot immediately, find a journal,
understand a learning, and inspect its source without losing context. All four
tabs feel like chapters of one publication. No misleading metadata, unsupported
claims, decorative visual clutter, or dead-end interactions. Browser, source,
accessibility, offline, and PDF checks in the development plan must pass.

Public-demo preparation and Hacker News are downstream activities. They do not
change this hierarchy or justify compromising source fidelity.
