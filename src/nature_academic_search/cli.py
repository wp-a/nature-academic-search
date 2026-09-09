"""Command-line entry point for the academic search package."""

from __future__ import annotations

import argparse
import json
import sys
from argparse import Namespace
from collections.abc import Sequence
from typing import Any

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nature-academic-search",
        description="Search, verify, and export academic literature records.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve", help="Run the MCP server over stdio")
    search_parser = subparsers.add_parser(
        "search",
        help="Search publications or trial registrations",
    )
    search_parser.add_argument("query", help="Search keywords or query string")
    search_parser.add_argument("--rows", type=int, default=5, help="Results per source")
    search_parser.add_argument(
        "--sources",
        help="Comma-separated source names; defaults follow entity type",
    )
    search_parser.add_argument(
        "--entity-type",
        default="publication",
        choices=("publication", "trial"),
    )
    search_parser.add_argument(
        "--ranking",
        default="relevance",
        choices=("relevance", "none"),
    )
    search_parser.add_argument(
        "--enrich",
        help="Comma-separated enrichers, currently semantic_scholar",
    )
    verify_parser = subparsers.add_parser(
        "verify",
        help="Resolve an identifier and compare expected metadata",
    )
    verify_parser.add_argument("id", help="DOI, PMID, PMCID, arXiv, OpenAlex, NCT, or URL")
    verify_parser.add_argument("--id-type", default="auto")
    verify_parser.add_argument("--expected-title")
    verify_parser.add_argument("--expected-year", type=int)
    verify_parser.add_argument("--expected-journal")
    verify_parser.add_argument("--expected-authors", help="Comma-separated author names")
    verify_parser.add_argument("--expected-doi")
    verify_parser.add_argument("--expected-pmid")
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
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Run a local declarative research workflow",
    )
    workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command", required=True)
    workflow_run = workflow_subparsers.add_parser("run", help="Run a YAML workflow")
    workflow_run.add_argument("--file", required=True, help="Workflow YAML path")
    workflow_run.add_argument(
        "--output",
        default="workflow-artifacts",
        help="Artifact directory (default: workflow-artifacts)",
    )
    workflow_run.add_argument(
        "--approve",
        action="store_true",
        help="Approve the plan and allow source retrieval",
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
    if args.command == "search":
        from .server import search_papers

        return _print_json(
            search_papers(
                args.query,
                sources=_csv(args.sources),
                rows=args.rows,
                entity_type=args.entity_type,
                enrich=_csv(args.enrich),
                ranking=args.ranking,
            )
        )
    if args.command == "verify":
        from .server import get_paper_by_id

        return _print_json(
            get_paper_by_id(
                args.id,
                id_type=args.id_type,
                expected=_expected_metadata(args) or None,
            )
        )
    if args.command == "workflow" and args.workflow_command == "run":
        from .relay import OpenAICompatibleRelay
        from .workflow import WorkflowRunner, WorkflowSpec

        try:
            workflow = WorkflowSpec.from_yaml(args.file)
            result = WorkflowRunner(provider=OpenAICompatibleRelay.from_env()).run(
                workflow,
                args.output,
                approve=args.approve,
            )
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    return 0


def _csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _expected_metadata(args: Namespace) -> dict[str, Any]:
    expected: dict[str, Any] = {}
    if args.expected_title:
        expected["title"] = args.expected_title
    if args.expected_year is not None:
        expected["year"] = args.expected_year
    if args.expected_journal:
        expected["journal"] = args.expected_journal
    if args.expected_authors:
        expected["authors"] = [
            item.strip() for item in args.expected_authors.split(",") if item.strip()
        ]
    if args.expected_doi:
        expected["doi"] = args.expected_doi
    if args.expected_pmid:
        expected["pmid"] = args.expected_pmid
    return expected


def _print_json(payload: str) -> int:
    print(payload)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return 1
    if isinstance(data, dict) and data.get("error"):
        return 1
    return 0
