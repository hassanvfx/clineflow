# ClineFlow Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses date-based versioning: `YYYY.MM.DD.patch`

## [Unreleased]

### Added
- ClineFlow 3 tenant-scoped journals, opaque pinned tenant identity, separate work streams, immutable additive update records, and deterministic local ledger projections.
- Schema-2 migration that preserves schema-1 ledger views byte-for-byte under `knowledge/baseline/schema-1/` before rebuilding ClineFlow 3 projections.
- Five operational workflow principles covering accountable generated code, durable evidence, explicit autonomy boundaries, deterministic checks, and established engineering approaches. New journals now separate the task contract and planned proof from verification results.
- Handoff-topology planning that distinguishes a cohesive single handoff from a milestone chain with solid boundaries, local proof, dependency-aware composition, and one accountable integrator.

### Changed
- Release `2026.09.05.0` advances migration schema to `2` while retaining date-based release ordering and the permanent updater entrypoint.
- Release `2026.09.05.1` refreshes managed procedures, shared agent rules, and journal generation without a migration; schema `2` remains valid because persistent formats are unchanged.
- Release `2026.09.06.0` adds managed milestone-handoff guidance and journal prompts without a migration; schema `2` remains valid because persistent formats are unchanged.

### Fixed
- Windows removal now re-executes the uninstaller from a temporary external copy before moving `.clineflow/`, avoiding NTFS denial when the active script lives inside the runtime being transacted.
- PowerShell bootstrap and updater payloads now use regular-file mode instead of requiring POSIX executable semantics that Git Bash cannot represent for `.ps1` files on Windows.
- Windows lifecycle CI now preserves checksum-stable LF bytes for every manifest-managed text format and installs in the runner's temporary workspace through normalized cross-shell paths.
- Executive metrics now use the latest knowledge or Git activity rather than mistaking report generation for project activity.
- Replaced the remaining Decision Atlas graph with a calmer, source-bound Project Story, eliminating the graph library and its repetitive relationship UI.
- Decision Atlas and Timeline now normalize structured YAML records and common field aliases before rendering, preventing `[object Object]` evidence labels and empty event summaries.
- Time Spine now uses a short event title and compact kind label, keeping the full event note in an expandable, paragraph-formatted disclosure.
- Invoking the dashboard without an explicit subcommand now forwards the default `generate` command to the Python engine, preventing missing `argparse` attributes on first use.
- Decision Atlas now opens as a clean five-ledger system map and progressively reveals capped goal, constraint, evidence, or journal views with readable cards and a full-text details rail instead of an overlapping all-document force graph.
- Managed agent-rule refresh no longer calls BSD `head` with a zero line count when the ClineFlow block begins on the first line.
- Source-repository agent instructions now reference the runtime guides and validators under `template/.clineflow/`, and the legacy Cline compatibility template matches the canonical shared rules.

### Added
- A Zenodo DOI badge in the README plus concept and version DOI identifiers in CITATION.cff.
- Citation File Format 1.2.0 metadata for formal GitHub and Zenodo software citation.
- A prominent raw rescue-update command for installations whose older agent instructions do not recognize the natural-language update prompt.
- An installation-first README, focused lifecycle/workflow/Knowledge Visor guides, and a linked 30-minute tutorial with a local preview image.
- Canonical “Please commit.”, “Please remove ClineFlow.”, and “Please show me the ClineFlow dashboard.” prompts across distributed agent guidance.
- The optional, time-first ClineFlow Knowledge Visor with an inert bootstrap, approval-gated and checksum-verified assets, self-contained HTML reports plus adjacent JSON snapshots, sanitized exports, and dormant/activated boundary certification.
- A formal dashboard pipeline that collects normalized facts, derives source-bound narrative observations, and renders both JSON models into file-protocol-safe HTML; the replaceable `observe` stage is ready for a future CLI/LLM implementation.
- An agent-independent `validate-knowledge-sync` commit gate for journals, documentation, all five durable ledgers, and the knowledge log.
- A one-command lifecycle certification gate covering installation, historical updates, transactional removal, preservation, and rollback.
- Universal transactional updates for all OKF-era layouts from `2026.08.15.0` onward.
- A permanent remote `update.sh` bootstrap, installed PowerShell update wrapper, release manifest, migration state, automatic rollback, and release-contract validation.
- The canonical “Please update ClineFlow.” agent command for repository-authoritative, non-interactive updates.
- Native Open Knowledge Format (OKF) v0.2 knowledge bundles at `knowledge/` for new installations.
- `validate-okf`, a dependency-free Bash structural validator for OKF bundles.
- Optional `validate-okf --strict` validation that parses frontmatter with PyYAML when available.
- Read-only legacy discovery for pre-OKF `docs/journals/` histories.

### Changed
- Release `2026.09.03.23` makes transactional removal portable when Windows locks the running uninstaller path; migration schema `1` remains valid because persistent formats are unchanged.
- Release `2026.09.03.22` corrects Windows PowerShell payload modes; migration schema `1` remains valid because the transactional updater applies manifest modes without changing persistent formats.
- Release `2026.09.03.21` documents the permanent remote bootstrap as the old-install compatibility escape hatch; migration schema `1` remains valid because no persistent format changes.
- Release `2026.09.03.20` makes removal preview-first and confirmation-gated at the agent-instruction layer while preserving the existing transactional remover and schema `1`.
- Public documentation now explains the hidden runtime, OKF knowledge base, five ledgers, self-documenting commit loop, and dormant dashboard without duplicating implementation detail in the README.
- Knowledge Visor now leads with a source-linked Recent Story, defaults the Time Spine to useful recent moments, and exposes the whole chronology on demand; decorative chapter navigation has been removed.
- Knowledge Visor adopts ClineFlow’s public deep-navy and electric-blue visual language, editorial type scale, restrained geometry, and high-contrast navigation while retaining its offline embedded assets.
- Story navigation now names the Project Story directly; the managed Knowledge Visor release is `2026.09.03.8`.
- Knowledge Visor observations now include a validated `project_story` model for evolution, current importance, urgency, the next deliberate move, and selected milestones.
- Knowledge Visor now tells one progressive story across executive context, manager trajectory, engineering decisions, shared proof, and canonical source exploration; asset provenance remains in `manifest.json` instead of occupying a dashboard panel.
- Knowledge Explorer now parses YAML through the pinned optional runtime, presents guided structured sections instead of flattened source text, diagnoses malformed YAML, and provides non-mutating normalized YAML and JSON repair output.
- Executive, manager, and engineer narrative views now draw from the explicit `clineflow-dashboard-observations/v1` model embedded alongside normalized facts and preserved as `observations.json` in every run.
- Updated the managed Knowledge Visor release to `2026.09.03.6` with structured evidence, timeline normalization, and progressive Time Spine disclosure.
- All supported agent configurations now require five-ledger reconciliation for every journal, documentation, or knowledge-base change and a staged synchronization check before commit.
- Uninstall now requires confirmation (or `--yes`), validates ownership data before mutation, preserves edits to formerly owned agent files, and rolls back failures or handled interruptions.
- Standardized the installer, updater, and installed state on date-based versions, currently `2026.09.03.4`, with migration schema `1`.
- Installation-affecting features must now declare and test their migration impact.
- New task journals are Engineering Journal concepts in `knowledge/journals/`.
- Install, update, and uninstall flows preserve both `knowledge/` and legacy `docs/journals/` user content.

### Migration
- Root and visible `clineflow/bin/` OKF installations are migrated into `.clineflow/`; authored knowledge and ambiguous legacy files remain preserved.

### Removed
- The optional symlink-based reference-repository system, including its local configuration, setup script, generated workspace support, and reference documentation. Related projects now use the sibling-project folder convention.

## [2025.11.17.0] - 2025-11-17

### Added
- **Multi-Root Workspace Generation** - Complete fix for @ mention completion in Cline
  - `setup-refs.sh` now generates `.code-workspace` files automatically
  - Workspace files enable full VS Code indexing of all linked repositories
  - New `--workspace-only` flag to regenerate workspace without touching symlinks
  - Hybrid approach: symlinks for file browser + workspace for @ mentions
  
### Fixed
- **@ Mention Autocomplete** - Resolved issue where symlinked reference files didn't appear in Cline's @ mention suggestions
  - VS Code wasn't indexing symlinked directories
  - Multi-root workspace makes all repos first-class citizens
  - Full autocomplete now works for all linked repositories
  
### Changed
- Updated `template/.gitignore` to exclude `*.code-workspace` files (developer-specific paths)
- Enhanced reference system to be fully idempotent (safe to re-run anytime)
- Improved `setup-refs.sh` output with workspace file usage instructions

### Documentation
- Added "Troubleshooting: @ Mentions Not Working?" section to README.md
- Complete rewrite of `template/.clineflow/README.md` usage section
- Documented dual access model (workspace vs symlinks)
- Added workspace vs folder comparison
- Clear upgrade path for existing users

---

## [2025.11.12.0] - 2025-11-12

### Added
- **SOP-008: Feature Branch Management** - New procedure ensuring all development happens on feature branches
  - Automatic branch checking before starting tasks
  - Standard Git Flow branch naming conventions (feature/, fix/, docs/, refactor/)
  - Integration with existing SOPs for complete workflow
  - Protects main branch from direct commits
  
- **Update System** - Complete update mechanism for existing installations
  - `update.sh` script for safe, selective updates
  - Preserves user customizations (.clinerules, .clineflow.local, journals)
  - `--dry-run` option to preview updates
  - `--yes` flag for automated updates
  - Smart file comparison to detect actual changes
  
- **Version Tracking** - Date-based semantic versioning
  - `VERSION` file tracks current installation
  - Format: YYYY.MM.DD.patch (e.g., 2025.11.12.0)
  - Displayed during updates for clear tracking

### Changed
- Updated "Before Starting Any Task" checklist to include branch verification
- Enhanced PROCEDURES.md with comprehensive branch management guidance
- All template files now include version-aware update system

### Documentation
- Added complete branch management workflows for solo developers and teams
- Documented integration between SOP-008 and existing procedures
- Created this CHANGELOG for tracking all future updates

---

## [Previous Releases]

### [2025.11.11.0] - 2025-11-11
- AI-assisted installation as primary method
- Agent-agnostic support (Cline, Cursor, Copilot, Windsurf)
- Updated README with prominent AI installation option

### [2025.11.10.0] - 2025-11-10
- Viral README enhancement with ASCII art and Mermaid diagrams
- Real dogfooding proof with development journal link
- "Senior VibeCoding" branding
- Complete visual storytelling

### [2025.11.09.0] - 2025-11-09
- Multi-line git commit safety (SOP-007)
- Heredoc pattern for reliable commits
- Document Driven Development (DDD) positioning
- Comprehensive uninstall system

### [2025.11.08.0] - 2025-11-08
- Initial ClineFlow release (rebranded from llm-refs)
- Intelligent commit workflow (SOP-005)
- Task journal management (SOP-006)
- Reference system with symlink safety
- Auto-configured .gitignore

---

## Update Instructions

### For Existing Users

To update your ClineFlow installation to the latest version:

```bash
# Download and run update script
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash

# Or if you already have it
./update.sh
```

**What gets updated:**
- Template documentation files (clineflow/*)
- Setup scripts (setup-refs.sh)
- Configuration examples (.clineflow.example)

**What stays protected:**
- Your custom rules (.clinerules)
- Your local config (.clineflow.local)
- All your journals (docs/journals/*)

### Preview Before Updating

```bash
# See what would change without modifying anything
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/update.sh | bash -s -- --dry-run
```

### Version Check

```bash
# Check your current version
cat VERSION

# Latest version available
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/VERSION
```

---

## Versioning Scheme

ClineFlow uses **date-based versioning** with semantic patches:

- `YYYY.MM.DD.patch`
- Example: `2025.11.12.0`
- Patch increments for same-day releases
- Major changes update date

**Benefits:**
- Clear chronological tracking
- Easy to see update frequency
- Semantic patch number for hotfixes

---

## Breaking Changes Policy

We strive to maintain backward compatibility. When breaking changes are necessary:

1. **Major version bump** - Date changes significantly (e.g., monthly release)
2. **Migration guide** - Detailed steps in changelog entry
3. **Deprecation warnings** - At least one release cycle notice
4. **Update script handles** - Automatic migration when possible

---

## Support

- **Issues**: [GitHub Issues](https://github.com/hassanvfx/clineflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hassanvfx/clineflow/discussions)
- **Updates**: Watch this repository for release notifications

---

## Contributing

Found a bug? Have a feature request? 

1. Check [existing issues](https://github.com/hassanvfx/clineflow/issues)
2. Open a new issue with details
3. Use ClineFlow to document your contribution!

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) principles.*
