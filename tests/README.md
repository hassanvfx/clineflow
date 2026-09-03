# ClineFlow Test Suite

The test suite verifies fresh installation, every supported OKF-era migration layout, rollback, release integrity, and OKF validation. All project fixtures are created in temporary directories and removed automatically.

## Run all checks

```bash
./tests/certify-release.sh
```

`certify-release.sh` is the required release gate and can take `--against GIT_REF` on pull requests. It runs shell syntax, release integrity, fresh installation, historical updates, transactional removal, rollback, prerequisite, OKF, and whitespace checks. `test-uninstall-safety.sh` specifically covers dry-run, confirmation, unsafe ownership data, malformed markers, edited agent files, symlink rejection, failure rollback, and signal rollback.

When an installed file or persistent contract changes, add or update its manifest record and decide whether the migration schema must advance. See [the release process](../docs/releasing.md).
