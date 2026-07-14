from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_medline_record_converts_to_ris() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from nature_academic_search.conversion import convert_from_medline

        ris = convert_from_medline(
            "\n".join(
                [
                    "PMID- 12345678",
                    "TI  - A reproducible academic search workflow.",
                    "AU  - Wang P",
                    "DP  - 2026 Jul",
                    "LID - 10.1000/example [doi]",
                    "",
                ]
            ),
            "ris",
        )
    finally:
        sys.path.pop(0)

    assert "TY  - JOUR" in ris
    assert "TI  - A reproducible academic search workflow." in ris
    assert "DO  - 10.1000/example" in ris
    assert "AN  - PMID:12345678" in ris
    assert ris.endswith("ER  - \n")
