---
type: Engineering Journal
title: "Software citation and Zenodo preparation"
description: "Adds canonical Citation File Format metadata before ClineFlow's first Zenodo-archived GitHub release."
tags: [documentation, citation, zenodo, releases]
status: stable
generated:
  by: clineflow/2026.09.03.23
  at: 2026-09-03T23:16:14Z
---

# Goal

Make ClineFlow formally citable before its first Zenodo-triggering GitHub release by publishing valid, repository-native `CITATION.cff` metadata.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

## 2026-09-03 23:13 UTC - Citation metadata added

Added Citation File Format 1.2.0 metadata for ClineFlow release `2026.09.03.23`, naming Hassan Uriostegui as the author and describing the repository as software for persistent, Open Knowledge Format-based AI coding context. The metadata intentionally omits ORCID because the author confirmed none should be included, and omits DOI because Zenodo has not assigned one yet.

# Decisions

- Use the project's date-based `2026.09.03.23` release version rather than introducing a conflicting `v1.0.0` version.
- Use “ClineFlow: Persistent Context and Open Knowledge for AI Coding Agents” as the citable title.
- Treat `CITATION.cff` as repository-only release metadata; it does not alter installed files, persistent formats, ownership, or required runtime behavior, so no release-manifest change or migration is required.
- Add the Zenodo DOI only after the first GitHub release has been archived and Zenodo has assigned the identifier.

# Testing

- Ruby/Psych parsed `CITATION.cff` successfully and confirmed the required metadata, exact author name, and date-based version.
- `git diff --check -- CITATION.cff` passed.
- The dependency-free OKF validator and knowledge synchronization validator pass with the citation journal and all five ledgers reconciled.
- Release-contract validation passed for release `2026.09.03.23`, schema `1`; optional strict OKF validation was unavailable because PyYAML is not installed.
- `./tests/certify-release.sh` passed the complete installation, dashboard-boundary, historical-update, rollback, removal-safety, release-contract, OKF, knowledge-synchronization, and whitespace matrix.

# Open Issues

- Commit and push this metadata before creating GitHub release `2026.09.03.23`.
- After Zenodo archives the release, add the assigned DOI to the citation metadata and repository documentation in a follow-up change.

# References

- [Citation metadata](../../CITATION.cff)
- [Release procedure](../../docs/releasing.md)
- [Citation File Format 1.2.0 schema guide](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md)
- [Zenodo GitHub metadata guidance](https://help.zenodo.org/docs/github/describe-software/)
