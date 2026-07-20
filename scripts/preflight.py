#!/usr/bin/env python3
"""Compatibility wrapper for the packaged seven-source preflight command."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nature_academic_search.preflight import (  # noqa: E402
    ENDPOINTS,
    check_endpoints,
    check_single,
    main,
    print_report,
)

__all__ = ["ENDPOINTS", "check_endpoints", "check_single", "main", "print_report"]


if __name__ == "__main__":
    raise SystemExit(main())
