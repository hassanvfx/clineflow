# Releasing ClineFlow

ClineFlow releases must keep fresh installation and upgrades from every supported OKF-era layout equivalent.

## Installation-impact decision

For each change to installed files, persistent formats, ownership, or required workflow behavior, record one decision in the active Engineering Journal:

- **No migration required:** add or update the manifest payload, bump the date-based release version, and prove an existing installation receives the change.
- **Migration required:** bump the release version and migration schema, add the next sequential migration, and add historical-fixture and rollback coverage.

Repository-only documentation and development infrastructure do not require a migration unless they affect installed behavior.

## Release sequence

1. Implement the feature and record its migration decision.
2. Update `template/.clineflow/VERSION` using `YYYY.MM.DD.patch`.
3. Update managed payloads and regenerate their checksums in `template/.clineflow/release-manifest`. For an MCP release, build the versioned wheel, record its SHA-256 in `mcp-server/release-manifest`, and publish that exact artifact before advertising the release.
4. Run `./tests/certify-release.sh`; on a pull request, use `./tests/certify-release.sh --against <base-ref>`.
5. Update `CHANGELOG.md` and the durable knowledge indexes, then publish the release atomically.

The root `update.sh` URL is permanent compatibility infrastructure and must not be removed or repurposed.

The certification entrypoint is also permanent release infrastructure. Release validation fails if installation, historical-update, removal-safety, or OKF coverage is removed from it, or if CI stops invoking it.

## Publishing the optional MCP server

The separately versioned MCP wheel is published only through the manual
`Publish ClineFlow MCP` GitHub Actions workflow. Before dispatching it, confirm
that the ordinary Linux and Windows test workflow passed for the accepted
commit. Dispatch with the exact confirmation text `publish-mcp`; the workflow
reruns Linux certification, rebuilds the wheel, compares its filename and
SHA-256 with `mcp-server/release-manifest`, and creates the matching immutable
`mcp-v<version>` GitHub release. It refuses to overwrite an existing release.
