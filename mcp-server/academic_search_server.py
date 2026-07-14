"""Compatibility entry point for the packaged MCP server."""

from __future__ import annotations

import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nature_academic_search.server import (  # noqa: E402
    _format_basic_citation,
    _resolve_id_type,
    detect_id_type,
    get_citation,
    get_paper_by_id,
    lookup_mesh,
    main,
    mcp,
    search_papers,
)


_detect_id_type = detect_id_type


if __name__ == "__main__":
    main()
