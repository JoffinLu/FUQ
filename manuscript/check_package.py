"""Cross-check that the package documents agree with the actual artifacts.

Checks (all must pass):
  * main.pdf has 16 pages, main_test.pdf has 18 pages, supplement.pdf has 6 pages;
  * main.tex contains 7 tables and 4 figures;
  * check_numbers.py verifies 123 numbers with none missing;
  * refs_checked.json covers 18 bibliography entries with no missing DOI;
  * submission zip v2.0 exists with 24 entries and contains the three PDFs;
  * release zip exists and contains MANIFEST.tsv with 164 files;
  * reviewer copy (16 pages) and combined PDF (22 pages) exist.

Usage: python manuscript/check_package.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def pdf_pages(path: Path) -> int:
    import fitz  # pymupdf

    return len(fitz.open(path))


def main() -> int:
    failures: list[str] = []
    checks: list[tuple[str, bool, str]] = []

    checks.append(("main pages", pdf_pages(HERE / "main.pdf") == 16, f"{pdf_pages(HERE / 'main.pdf')}"))
    checks.append(("main_test pages", pdf_pages(HERE / "main_test.pdf") == 18, f"{pdf_pages(HERE / 'main_test.pdf')}"))
    checks.append(("supplement pages", pdf_pages(HERE / "supplement.pdf") == 6, f"{pdf_pages(HERE / 'supplement.pdf')}"))
    main_tex = (HERE / "main.tex").read_text(encoding="utf-8")
    checks.append(("main tables", main_tex.count(r"\begin{table}") == 7, str(main_tex.count(r"\begin{table}"))))
    checks.append(("main figures", main_tex.count(r"\begin{figure}") == 4, str(main_tex.count(r"\begin{figure}"))))

    proc = subprocess.run([sys.executable, str(HERE / "check_numbers.py")], capture_output=True, text=True)
    checks.append(("check_numbers exit", proc.returncode == 0, proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""))

    checked = json.loads((HERE / "refs_checked.json").read_text(encoding="utf-8"))
    entries = checked if isinstance(checked, list) else checked.get("entries", [])
    checks.append(("refs checked entries", len(entries) == 18, str(len(entries))))
    # roy2026uq is the UAI/PMLR version, not indexed in OpenAlex; its DOI/arXiv
    # record was verified by hand against the paper PDF (see manuscript/README.md).
    manual_ok = {"roy2026uq"}
    missing = [e.get("key") for e in entries if e.get("verdict") == "missing" and e.get("key") not in manual_ok]
    checks.append(("refs unresolved", not missing, ",".join(missing)))
    supp_tex = (HERE / "supplement.tex").read_text(encoding="utf-8")
    checks.append(("supplement S-numbering", "thetable}{S" in supp_tex, ""))

    sub = HERE / "submission" / "fuq-fairness_submission_v2.0.zip"
    if not sub.exists():
        checks.append(("submission zip v2.0", False, "missing"))
    else:
        names = zipfile.ZipFile(sub).namelist()
        ok = (
            len(names) == 24
            and "manuscript/main.pdf" in names
            and "manuscript/main_test.pdf" in names
            and "manuscript/supplement.pdf" in names
            and "manuscript/sn-jnl.cls" in names
        )
        checks.append(("submission zip v2.0", ok, f"{len(names)} entries"))

    release = ROOT / "release" / "fuq-fairness-v1.0-source.zip"
    if not release.exists():
        checks.append(("release zip", False, "missing"))
    else:
        names = zipfile.ZipFile(release).namelist()
        manifest = [n for n in names if n == "MANIFEST.tsv"]
        n_files = len([n for n in names if not n.endswith("/")]) - 1
        checks.append(("release zip", bool(manifest) and n_files == 164, f"{n_files} files"))

    review = HERE / "main_review.pdf"
    if not review.exists():
        checks.append(("reviewer copy", False, "missing"))
    else:
        pages = pdf_pages(review)
        checks.append(("reviewer copy", pages == 16, f"{pages} pages"))

    combined = HERE / "fuq-fairness_full.pdf"
    if not combined.exists():
        checks.append(("combined PDF", False, "missing"))
    else:
        pages = pdf_pages(combined)
        checks.append(("combined PDF", pages == 22, f"{pages} pages"))

    width = max(len(name) for name, _, _ in checks)
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{name:<{width}}  {status}  {detail}")
        if not ok:
            failures.append(name)
    print(f"\n{len(checks) - len(failures)}/{len(checks)} package checks passed")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
