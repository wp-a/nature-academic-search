"""Data source adapters for academic search."""

from .arxiv import ArxivSource
from .clinicaltrials import ClinicalTrialsSource
from .crossref import CrossRefSource
from .europe_pmc import EuropePmcSource
from .openalex import OpenAlexSource
from .pubmed import PubMedSource
from .semantic_scholar import SemanticScholarSource

__all__ = [
    "ArxivSource",
    "ClinicalTrialsSource",
    "CrossRefSource",
    "EuropePmcSource",
    "OpenAlexSource",
    "PubMedSource",
    "SemanticScholarSource",
]
