# Knowledge Visor

The ClineFlow Knowledge Visor turns the project's existing OKF knowledge and Git history into a private, time-first local report. It is optional and dormant until explicitly requested.

## Open the dashboard

Ask an installed coding agent:

```text
Please show me the ClineFlow dashboard.
```

Or invoke it directly:

```bash
./.clineflow/bin/dashboard
```

The first invocation displays the exact optional runtime and visual assets it intends to install. It waits for approval before downloading or generating anything. Ordinary installation, development, validation, update, and commit preparation do not activate the dashboard.

## What first use creates

After approval, the launcher installs pinned optional components under `.clineflow/optional/` and creates a report under `knowledge/dashboard/runs/<run-id>/`.

| File | Purpose |
| --- | --- |
| `index.html` | Self-contained narrative report. |
| `snapshot.json` | Normalized `clineflow-dashboard/v1` facts. |
| `observations.json` | Source-bound narrative observations. |
| `presentation.json` | Prepared view model consumed by the browser. |
| `manifest.json` | Report schema and component provenance. |
| `knowledge/dashboard/blog/<project>/index.json` | Durable, machine-readable archive of release engineering articles. |
| `knowledge/dashboard/blog/<project>/articles/<release>/index.html` | Stable local permalink for one source-bound release article. |

The HTML embeds exact inert copies of its facts and observations, CSS, fonts, and the reader code. Unused chart and animation libraries are not embedded. Opening it through `file://` requires no local server and makes no browser-time network connection.

## Report chronology

Each new report looks for the immediately preceding complete local dashboard run
by its recorded generation time, then reads that run's frozen `snapshot.json`
and `observations.json`. The Workspace **Report chronology** disclosure compares
source membership, normalized dated events, unresolved-record count, and the
source-bound Spark lifecycle. It does not infer effort, causality, or support
from repeated rendering. When no predecessor is available, the report clearly
labels itself as the baseline for the next comparison.

## Follow-up dates

Recorded follow-ups show their source date in the review list and in the reader.
When an item names an immutable update record, the visor labels that date **Last
updated**. Otherwise it uses the dated latest-session ledger and labels it
**Ledger snapshot**; it never fabricates an individual event date.

The dashboard deliberately has no generated PDF or white-paper artifact. Its
source-bound observations, dated activity, evidence, and reader views remain
the primary product. This prevents a thin or unsupported narrative from being
repackaged as an executive document.

## Bounded agent observations

An agent never writes the dashboard, its HTML, a PDF, Spark identities, or a
complete observations document. The deterministic observer always fills the
required narrative model: the three audience views; origin, overall, recent,
and digest narratives; journal coverage; relationship uncertainty; project
story; and reconciled Sparks. An agent may optionally contribute only a
source-cited executive summary or an explicitly-assumed delivery estimate.

Use the facts-specific contract to give an agent the exact permitted input
shape and source register:

```bash
./.clineflow/bin/dashboard collect --output ./facts.json
./.clineflow/bin/dashboard contract --facts ./facts.json > ./agent-contract.json
./.clineflow/bin/dashboard observe --facts ./facts.json --insights ./agent-insights.json \
  --output ./observations.json --json-errors
./.clineflow/bin/dashboard render --facts ./facts.json --observations ./observations.json --no-open
```

The contract names the immutable facts `source_hash` and permitted `source_ids`.
The agent input has exactly two optional fields: `executive_summary` (non-empty
`text` plus one or more known `source_ids`) and `delivery_estimate` (the
separate explicit-assumptions schema). Unsupported fields and uncited text are
rejected. With `--json-errors`, a failure produces one structured diagnostic
with the named problem and a retry instruction. Correct that one field and
retry once; if it cannot be grounded in the source register, omit the optional
agent input and use the deterministic baseline.

## Engineering Blog and public discovery

Every changed frozen source bundle creates one first-person engineering post in
a project-scoped local Engineering Blog. A report with unchanged facts publishes
nothing: it explicitly says so and links to the last post, without rewriting it
or presenting it as new. The article's
topic, subtopics, source register, and release metadata are deterministically
derived only from that report's frozen facts and observations. The dashboard's **Blog** tab links to the latest post,
the browsable HTML archive, and its `index.json` history. Each HTML article has
an adjacent `article.json` link for agents, so the human reader and the
machine-readable source stay available together. Each article lives at a
durable local permalink under `knowledge/dashboard/blog/<project>/articles/`;
report retention does not prune this archive.

For a public repository or static deployment, set
`CLINEFLOW_DASHBOARD_PUBLIC_BASE_URL` to the actual HTTPS site origin before
generating a report, for example `https://example.com`. The renderer then
writes a project `robots.txt` and standards-compliant `sitemap.xml` containing
the archive and every article permalink. It deliberately does not fabricate a
public domain when that value is absent.

## What the report shows

- **Workspace**: latest recorded change, dated follow-ups, and searchable journals. Activity metrics, role perspectives and ledgers are secondary disclosures.
- **Sparks**: extracted decisions and learning notes with source passages, scope and limitations. Each run compares candidates with the preceding report; an unchanged candidate stays unchanged and does not acquire supporting evidence merely by appearing again.
- **Activity**: filterable normalized event chronology with source-linked detail
- **Evidence**: searchable, paginated verification and decision records, including additive-ledger entries. Project narratives and raw ledgers are available on demand.
- **Learning**: project-derived reading content, source links, and copyable assistant questions.
- **Blog**: durable source-bound release articles, archive and JSON history.
- One reusable read-only reader modal for canonical sources and event detail
- A Light/Dark reader switch; no source editing or live connection

The report order is **Workspace, Sparks, Activity, Evidence, Learning, Blog**. The
Learning tab keeps the stable `#onboarding` route for saved links. Use
Ctrl/Cmd+K to search source contents, learning notes and activity. Arrow keys
move between tabs; reader Back returns to the preceding record and Escape closes
the reader. Theme preference persists locally when browser storage is available.
Source links missing from the frozen snapshot identify the missing reference.

The dashboard does not infer a current priority from alphabetical ledger order.
When no next step is designated it offers the recorded follow-ups for review.
Source coverage counts do not certify that a claim is true; supported Sparks need
an additional evidence reference beyond their origins.

The dashboard does not infer contributor productivity, silently invent delivery estimates, or edit the source knowledge. It reports a decision chain or coworker interaction only when the canonical source explicitly records that relationship; otherwise it presents an unknown for human review. Canonical records remain ordinary repository files.

## Frozen canonical sample

The dashboard boundary suite includes `tests/fixtures/dashboard/adcrush-frozen/`,
a frozen operational snapshot of the sibling project `ad-crush`. It contains the
five generated ledgers, five active journals, and timeline captured at the
manifested sibling revision and content hashes. Regenerate it deliberately with
`tests/build-adcrush-dashboard-fixture.py`; it never reads the sibling project
while tests run.

## Privacy and ownership

- Reports are generated locally from the current repository.
- There are no analytics, remote iframes, browser-time API calls, or background dashboard process.
- The optional runtime stays isolated under `.clineflow/optional/`.
- Reports stay under `knowledge/dashboard/` and are preserved when ClineFlow tooling is removed.
- Sanitized exports omit agent metadata and delivery estimates.

## Commands

```bash
./.clineflow/bin/dashboard doctor              # Inspect dormant or active state
./.clineflow/bin/dashboard                     # Generate and open a report
./.clineflow/bin/dashboard generate --no-open  # Generate without opening a browser
./.clineflow/bin/dashboard contract --facts ./facts.json  # Print the bounded agent input contract
./.clineflow/bin/dashboard settings --show     # Inspect report retention
./.clineflow/bin/dashboard settings --retain 5
./.clineflow/bin/dashboard export --run latest --output ./dashboard-export
```

Retention defaults to the three newest complete reports. A positive configured number changes the limit; `unlimited` retains every completed run. Pruning applies only after successful report replacement and leaves settings or malformed directories untouched.

## README tutorial image

The quick-tutorial preview at `assets/clineflow-tutorial-thumbnail.jpg` is derived from the public poster metadata for the project's [Vimeo masterclass](https://vimeo.com/1220645170?fl=pl&fe=cm).

For the underlying knowledge model, see the [OKF knowledge workflow](okf-knowledge-workflow.md). For installation and removal boundaries, see [Installation and Lifecycle](installation-and-lifecycle.md).
