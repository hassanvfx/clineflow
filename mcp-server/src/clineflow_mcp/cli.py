"""Administration CLI for the optional global ClineFlow MCP server."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .clients import apply, plan, remove
from .contracts import contract


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="clineflow-mcp")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup", help="inspect or configure detected MCP clients")
    setup.add_argument("--status", action="store_true")
    setup.add_argument("--apply", action="store_true")
    setup.add_argument("--yes", action="store_true")
    uninstall = sub.add_parser("uninstall", help="preview or remove exact owned client entries")
    uninstall.add_argument("--apply", action="store_true")
    uninstall.add_argument("--yes", action="store_true")
    sub.add_parser("contract", help="show bundled MCP contract")
    options = parser.parse_args(argv)
    if options.command == "contract":
        _emit(contract()); return
    if options.command == "setup":
        if options.apply and not options.yes:
            _emit({"status": "confirmation_required", "plans": plan()}); return
        try:
            planned = plan()
            unsafe = [item for item in planned if item["action"] == "skip"]
            if options.apply and unsafe:
                _emit({"status": "client_setup_blocked", "clients": planned,
                       "message": "A detected client has malformed, conflicting, or user-managed ClineFlow configuration."})
                raise SystemExit(2)
            result = apply() if options.apply else planned
        except ValueError as error:
            _emit({"status": "launcher_unavailable", "message": str(error)})
            raise SystemExit(2) from error
        detected = [item for item in result if item["action"] != "not_detected"]
        _emit({"status": "configured" if options.apply else "planned", "clients": result,
               "outcome": "installed_mcp_ready_no_client_detected" if not detected else "client_setup_complete"})
        return
    if options.apply and not options.yes:
        _emit({"status": "confirmation_required", "clients": remove()}); return
    _emit({"status": "removed" if options.apply else "planned", "clients": remove(apply_changes=options.apply)})


if __name__ == "__main__":
    main(sys.argv[1:])
