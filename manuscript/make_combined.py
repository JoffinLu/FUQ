"""Merge the manuscript and its supplementary material into one PDF.

Reviewers and advisors often prefer a single file.  The merged PDF is a convenience
artifact; the two separate PDFs remain the submission units.

    python manuscript/make_combined.py

Output: manuscript/fuq-fairness_full.pdf.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent


def main() -> int:
    parts = [HERE / "main.pdf", HERE / "supplement.pdf"]
    for part in parts:
        if not part.exists():
            raise SystemExit(f"missing {part}; compile it first")
    out = pymupdf.open()
    for part in parts:
        out.insert_pdf(pymupdf.open(part))
    target = HERE / "fuq-fairness_full.pdf"
    out.save(target)
    print(f"wrote {target} ({out.page_count} pages, {target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
