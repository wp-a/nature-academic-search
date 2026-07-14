"""Compatibility alias for :mod:`nature_academic_search.errors`."""

from __future__ import annotations

import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nature_academic_search import errors as _implementation


sys.modules[__name__] = _implementation
