"""Compatibility alias for :mod:`nature_academic_search.sources.crossref`."""

from __future__ import annotations

import sys

from nature_academic_search.sources import crossref as _implementation


sys.modules[__name__] = _implementation
