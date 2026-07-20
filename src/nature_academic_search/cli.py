"""Command-line entry point for the academic search package."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nature-academic-search",
        description="Search, verify, and export academic literature records.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve", help="Run the MCP server over stdio")
    subparsers.add_parser(
        "preflight",
        help="Check academic source connectivity",
    )
    subparsers.add_parser(
        "citation",
        help="Download and convert citations (nbib, ris, bib, enw)",
    )
    subparsers.add_parser(
        "install",
        help="Register the package with Codex, Claude Code, or both",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]

    if arguments and arguments[0] == "preflight":
        from .preflight import main as preflight_main

        return preflight_main(arguments[1:])
    if arguments and arguments[0] == "citation":
        from .citation import main as citation_main

        result = citation_main(arguments[1:])
        return int(result or 0)
    if arguments and arguments[0] == "install":
        from .installer import main as installer_main

        return installer_main(arguments[1:])

    args = build_parser().parse_args(arguments)
    if args.command == "serve":
        from .server import main as server_main

        server_main()
        return 0
    return 0
