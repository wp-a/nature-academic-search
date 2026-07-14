"""Compatibility alias for :mod:`nature_academic_search.sources.arxiv`."""

from __future__ import annotations

import sys

from nature_academic_search.sources import arxiv as _implementation


sys.modules[__name__] = _implementation
