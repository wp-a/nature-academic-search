"""Data source adapters for academic search."""

from .arxiv import ArxivSource
from .crossref import CrossRefSource
from .europe_pmc import EuropePmcSource
from .openalex import OpenAlexSource
from .pubmed import PubMedSource

__all__ = [
    "ArxivSource",
    "CrossRefSource",
    "EuropePmcSource",
    "OpenAlexSource",
    "PubMedSource",
]
