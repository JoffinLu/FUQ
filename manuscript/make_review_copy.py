"""Build a reviewer-facing copy of the manuscript with continuous line numbers.

The target journal (JCGS) is single-anonymised; reviewers benefit from line numbers
for their reports.  This script only injects the ``lineno``
package into a copy of ``main.tex`` and compiles it with the bundled Tectonic, so the
submitted source (``main.tex``) stays untouched.

    python manuscript/make_review_copy.py

Output: manuscript/main_review.pdf (15 pages, single-spaced, numbered lines).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TECTONIC = ROOT.parent / "tools" / "tectonic" / "tectonic.exe"


def main() -> int:
    src = (HERE / "main.tex").read_text(encoding="utf-8")
    if "\\usepackage[switch]{lineno}" not in src:
        marker = "\\usepackage{natbib}\n"
        if marker not in src:
            raise SystemExit("cannot find \\usepackage{natbib} in main.tex")
        src = src.replace(marker, marker + "\\usepackage[switch]{lineno}\n", 1)
    if "\\linenumbers" not in src:
        marker = "\\begin{document}\n"
        src = src.replace(marker, marker + "\\linenumbers\n", 1)
    target = HERE / "main_review.tex"
    target.write_text(src, encoding="utf-8")

    cmd = [str(TECTONIC), "-X", "compile", target.name]
    print("running:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    sys.stdout.write(proc.stdout[-1500:])
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-3000:])
        return proc.returncode

    pdf = HERE / "main_review.pdf"
    if not pdf.exists():
        raise SystemExit("compilation finished but main_review.pdf is missing")
    pages = pdf.read_bytes().count(b"/Type /Page") - pdf.read_bytes().count(b"/Type /Pages")
    print(f"wrote {pdf} ({pdf.stat().st_size} bytes, ~{pages} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
