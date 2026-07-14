"""Compatibility imports for the packaged citation converters."""

from __future__ import annotations

import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nature_academic_search.conversion.converters import *  # noqa: F403
