"""Safe project-root and MCP workspace primitives."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .contracts import WORKSPACE

BEGIN = "# BEGIN CLINEFLOW MCP WORKSPACE"
END = "# END CLINEFLOW MCP WORKSPACE"


class WorkspaceError(ValueError):
    """A root or managed workspace was unsafe."""


def root_path(value: str) -> Path:
    path = Path(value)
    resolved = path.resolve()
    if not path.is_absolute() or path.is_symlink() or not path.is_dir() or path.absolute() != resolved:
        raise WorkspaceError("root must be an absolute, existing, non-symbolic-link directory")
    return resolved


def workspace(root: Path) -> Path:
    path = root / WORKSPACE
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise WorkspaceError(".clineflow-mcp must be a regular directory")
    return path


def status(root: Path) -> dict[str, object]:
    path = workspace(root)
    return {"status": "ready" if path.exists() else "missing", "workspace": str(path)}


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def ensure(root: Path) -> Path:
    path = workspace(root)
    install_ignore_marker(root)
    path.mkdir(mode=0o700, exist_ok=True)
    for relative in ("dashboard/runs", "exports", "operations", "locks"):
        (path / relative).mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = path / "state.json"
    if not marker.exists():
        _atomic_text(marker, json.dumps({"schema": 1}, sort_keys=True) + "\n")
    return path


def install_ignore_marker(root: Path) -> None:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"], text=True,
                            capture_output=True, check=False)
    if result.returncode:
        return
    exclude = Path(result.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    previous = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    begin_count = previous.count(BEGIN)
    end_count = previous.count(END)
    if begin_count == 1 and end_count == 1:
        managed = previous.split(BEGIN, 1)[1].split(END, 1)[0].strip()
        if managed != f"/{WORKSPACE}/":
            raise WorkspaceError(".git/info/exclude has malformed ClineFlow MCP workspace markers")
        return
    if begin_count or end_count:
        raise WorkspaceError(".git/info/exclude has malformed ClineFlow MCP workspace markers")
    _atomic_text(exclude, previous.rstrip() + f"\n\n{BEGIN}\n/{WORKSPACE}/\n{END}\n")


@contextmanager
def operation_lock(root: Path) -> Iterator[Path]:
    path = ensure(root) / "locks" / "operation.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        # A process crash can leave a lock behind. Reclaim only a regular lock
        # whose recorded PID is demonstrably gone; ambiguous locks remain busy.
        try:
            recorded = int(path.read_text(encoding="utf-8").strip())
            os.kill(recorded, 0)
            raise WorkspaceError("another ClineFlow MCP operation is already active for this root") from error
        except ProcessLookupError:
            if path.is_file() and not path.is_symlink():
                path.unlink()
                try:
                    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError as retry_error:
                    raise WorkspaceError("another ClineFlow MCP operation is already active for this root") from retry_error
            else:
                raise WorkspaceError("another ClineFlow MCP operation is already active for this root") from error
        except (OSError, ValueError):
            raise WorkspaceError("another ClineFlow MCP operation is already active for this root") from error
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield path
    finally:
        os.close(descriptor)
        path.unlink(missing_ok=True)
