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

The HTML embeds exact inert copies of its facts and observations, CSS, fonts, and visual libraries. Opening it through `file://` requires no local server and makes no browser-time network connection.

## What the report shows

- The current goal, decision boundary, next action, and verification state
- A concise project story and recent events
- An expandable audit timeline
- Structured decisions, proof, and open questions
- Project Pulse views derived from Git and knowledge facts
- A read-only explorer for canonical Markdown and YAML sources
- Optional source-bound delivery scenarios when an invoking agent explicitly provides their assumptions

The dashboard does not infer contributor productivity, silently invent delivery estimates, or edit the source knowledge. Canonical records remain ordinary repository files.

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
./.clineflow/bin/dashboard settings --show     # Inspect report retention
./.clineflow/bin/dashboard settings --retain 5
./.clineflow/bin/dashboard export --run latest --output ./dashboard-export
```

Retention defaults to the three newest complete reports. A positive configured number changes the limit; `unlimited` retains every completed run. Pruning applies only after successful report replacement and leaves settings or malformed directories untouched.

## README tutorial image

The quick-tutorial preview at `assets/clineflow-tutorial-thumbnail.jpg` is derived from the public poster metadata for the project's [Vimeo masterclass](https://vimeo.com/1220645170?fl=pl&fe=cm).

For the underlying knowledge model, see the [OKF knowledge workflow](okf-knowledge-workflow.md). For installation and removal boundaries, see [Installation and Lifecycle](installation-and-lifecycle.md).
