# ClineFlow OKF Knowledge Workflow

ClineFlow stores new persistent engineering context as an Open Knowledge Format bundle, following [Google Cloud's introduction to OKF](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) and targeting the [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). The format keeps knowledge portable, human-readable, agent-readable, and reviewable in Git.

## Bundle layout

```text
knowledge/
├── index.md                    # Bundle navigation; declares okf_version: "0.2"
├── log.md                      # Dated bundle change history
└── journals/
    ├── index.md                # Progressive-disclosure task listing
    └── <task>.md               # Engineering Journal concepts
```

Every non-reserved Markdown document is a concept with YAML frontmatter and a non-empty `type`. ClineFlow task concepts use `type: Engineering Journal` and carry a title, description, tags, lifecycle status, and generation metadata. Their Markdown bodies capture the goal, decisions, work log, tests, open issues, and links to related knowledge.

`index.md` files provide progressive disclosure. `log.md` files preserve dated change history. Normal Markdown links connect concepts into a knowledge graph without adding a proprietary runtime.

## Legacy journals

Projects may already have `docs/journals/`. ClineFlow searches that directory when it exists so earlier context remains available, but treats it as read-only historical material:

- New tasks are written only to `knowledge/journals/`.
- Legacy files are never migrated, rewritten, or passed to the OKF validator.
- Install, update, and uninstall flows preserve both `knowledge/` and `docs/journals/`.

## Validation

Run the default structural validator before committing:

```bash
./.clineflow/bin/validate-okf
```

It has no dependencies beyond ClineFlow’s Bash baseline. It checks the bundle directory, required concept frontmatter framing, non-empty `type`, OKF reserved-file conventions, root OKF version declaration, and chronological log ordering.

For full YAML parsing, use optional strict mode in an environment with Python and PyYAML:

```bash
python3 -m pip install PyYAML
./.clineflow/bin/validate-okf --strict
```

Strict mode parses every concept frontmatter block with PyYAML in addition to the structural checks. It is intentionally optional: ClineFlow does not require Python or PyYAML for installation or normal use.

## Upgrade and removal

Fresh installations create the native `knowledge/` bundle and manifest-managed runtime. The permanent `update.sh` entrypoint migrates OKF-era installations from `2026.08.15.0` onward, while preserving authored knowledge and legacy journals. It stages and verifies the full release, backs up affected paths, and rolls back failed migrations automatically. Pre-OKF projects are not automatically migrated. The uninstaller removes ClineFlow-managed tooling but preserves both knowledge locations for manual retention or removal.
