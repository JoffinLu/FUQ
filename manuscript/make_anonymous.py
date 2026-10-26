"""Create the double-blind version of the manuscript (main_anonymous.pdf).

Copies main.tex, replaces the author block by "Anonymous Authors", and compiles
with the bundled Tectonic binary.  The anonymous PDF is not part of the
submission zip; submit it separately when the journal requires double-blind
review.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TECTONIC = ROOT.parent / "tools" / "tectonic" / "tectonic.exe"

SOURCE = HERE / "main.tex"
TARGET = HERE / "main_anonymous.tex"


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    start_marker = "% ==AUTHOR-BLOCK-START=="
    end_marker = "% ==AUTHOR-BLOCK-END=="
    if start_marker not in text or end_marker not in text:
        raise SystemExit("author-block markers not found in main.tex")
    start = text.index(start_marker)
    end = text.index(end_marker)
    text = text[:start] + start_marker + "\n\\author{Anonymous Authors}\n" + text[end:]
    TARGET.write_text(text, encoding="utf-8")
    print("wrote", TARGET.name)

    if not TECTONIC.exists():
        raise SystemExit(f"tectonic not found at {TECTONIC}")
    proc = subprocess.run([str(TECTONIC), TARGET.name], cwd=HERE, capture_output=True, text=True, errors="ignore")
    print("compile:", "OK" if proc.returncode == 0 else f"FAIL({proc.returncode})")
    if proc.returncode != 0:
        print(proc.stderr[-600:])
        return proc.returncode

    pdf = HERE / "main_anonymous.pdf"
    import fitz

    pages = fitz.open(pdf)
    head = pages[0].get_text()
    ok = "Anonymous Authors" in head and "TODO" not in head
    print(f"anonymous pdf: {len(pages)} pages, {pdf.stat().st_size / 1024:.0f} KB, anonymous={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
