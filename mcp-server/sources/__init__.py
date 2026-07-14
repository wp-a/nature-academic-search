"""Compatibility package for the pre-PyPI server layout."""

from __future__ import annotations

import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nature_academic_search.sources import ArxivSource, CrossRefSource, PubMedSource

__all__ = ["ArxivSource", "CrossRefSource", "PubMedSource"]
