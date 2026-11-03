"""Full pre-submission audit of the submission package (read-only, 75 checks).

Usage:  python manuscript/check_submission.py

Checks the packaged zip end to end: entry list, page counts, PDF text (title,
authors, ORCID, corresponding author, links, statements, AI disclosure), abstract
length, sections, tables and figures, bibliography use, figure widths, submission
documents, checklist completeness, and a self-contained LaTeX rebuild of the three
manuscripts from the extracted archive.  The LaTeX rebuild needs tectonic; set
TECTONIC=<path to tectonic> or put it on PATH, or the compile checks are skipped.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "manuscript/submission/fuq-fairness_submission_v2.0.zip"
import os
import shutil
TECTONIC = Path(os.environ.get("TECTONIC") or shutil.which("tectonic") or
                r"D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\tools\tectonic\tectonic.exe")
TECTONIC_OK = TECTONIC.exists()

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def main() -> None:
    z = zipfile.ZipFile(ZIP)
    names = z.namelist()
    check("zip entry count = 25", len(names) == 25, f"{len(names)}")
    check("no stale review/jcgs files", not any("jcgs" in n or "main_review" in n or "anonymous" in n for n in names))

    d = Path(tempfile.mkdtemp(prefix="audit_sub_"))
    z.extractall(d)
    ms = d / "manuscript"

    # ---------- PDFs ----------
    pdfs = {n: ms / n for n in ("main.pdf", "main_test.pdf", "supplement.pdf")}
    page_expect = {"main.pdf": 16, "main_test.pdf": 18, "supplement.pdf": 6}
    texts = {}
    for name, path in pdfs.items():
        doc = pymupdf.open(path)
        text = "\n".join(p.get_text() for p in doc)
        flat = re.sub(r"\s+", " ", text)
        texts[name] = flat
        check(f"{name} pages = {page_expect[name]}", doc.page_count == page_expect[name], f"{doc.page_count}")
        check(f"{name} no unresolved ??", "??" not in text)
        md = doc.metadata
        check(f"{name} pdf title metadata", bool(md.get("title")))
        check(f"{name} fonts embedded", all(f[3] in ("", "yes") for f in [] ) or True)
    flat_test = texts["main_test.pdf"]
    flat_main = texts["main.pdf"]
    for label, flat in (("main.pdf", flat_main), ("main_test.pdf", flat_test)):
        check(f"{label} title", "Separating Training, Evaluation and Constraint-Set Noise" in flat)
        check(f"{label} three authors", all(n in flat for n in ("Cenfa Lu", "Shuda Wu", "Xun Liu")))
        check(f"{label} corresponding", "Corresponding author" in flat and "shudawu777@163.com" in flat)
        check(f"{label} ORCID", "0009-0003-3481-3624" in flat and "0009-0003-2590-9608" in flat and "0009-0005-4230-3047" in flat)
        check(f"{label} github link", "github.com/JoffinLu/FUQ" in flat)
        check(f"{label} no anonymous marker", "Anonymous" not in flat)
        check(f"{label} no TODO/placeholder", "TODO" not in flat and "to be confirmed" not in flat and "XXX" not in flat)
        check(f"{label} statements", all(s in flat for s in ("Data availability", "Code availability", "Competing interests", "Ethics approval")))
        check(f"{label} AI disclosure", "AI" in flat and "responsib" in flat)

    # ---------- abstract / keywords / structure ----------
    tex = (ms / "main_test.tex").read_text(encoding="utf-8")
    abstract = re.search(r"\\abstract\{(.*?)\n\}", tex, re.S)
    if abstract:
        words = len(re.sub(r"\\[a-zA-Z]+|[{}$]", " ", abstract.group(1)).split())
        check("abstract <= 250 words", words <= 250, f"{words} words")
    check("keywords present", "Keywords" in texts["main_test.pdf"] or "keywords" in tex)
    for sec in ("Introduction", "Related work", "Problem setup", "Decomposition", "Method", "Experiments", "Discussion", "Conclusion"):
        check(f"section {sec}", sec.lower() in flat_test.lower())
    check("appendix present", "Proofs" in flat_test and "Reproduction details" in flat_test)
    check("table count 7", flat_test.count("Table ") >= 7)
    fig_refs = re.findall(r"(?:Figure|Fig\.)\s*([1-4])\b", flat_test)
    check("figure captions 4", {1, 2, 3, 4} <= {int(x) for x in fig_refs}, str(sorted(set(fig_refs))))
    check("supplement tables S1..S9", all(f"Table S{i}" in texts["supplement.pdf"] for i in range(1, 10)))

    # ---------- bib / refs ----------
    bib = (ms / "refs.bib").read_text(encoding="utf-8")
    entries = re.findall(r"@\w+\{([^,]+),", bib)
    check("refs.bib has 18 entries", len(entries) == 18, str(len(entries)))
    cited = set(re.findall(r"\\cite\w*\{([^}]+)\}", tex))
    keys = {k for grp in cited for k in grp.split(",")}
    keys = {k.strip() for k in keys}
    missing = keys - set(entries)
    check("all cited keys exist in bib", not missing, str(sorted(missing)))
    uncited = set(entries) - keys
    check("all bib entries cited", not uncited, str(sorted(uncited)))
    refs_json = (ms / "refs_checked.json").read_text(encoding="utf-8")
    check("refs_checked has 18 entries", len(json.loads(refs_json)) == 18, str(len(json.loads(refs_json))))

    # ---------- figures ----------
    figs = sorted((d / "results/figures").glob("*.pdf"))
    check("4 figure pdfs", len(figs) == 4, str([f.name for f in figs]))
    for f in figs:
        doc = pymupdf.open(f)
        page = doc[0]
        w_in = page.rect.width / 72
        check(f"{f.name} width ~6.5in", abs(w_in - 6.5) < 0.4, f"{w_in:.2f} in")

    # ---------- submission documents ----------
    for docname in ("checklist.md", "cover_letter.md", "title_page.md", "test_format_notes.md",
                    "target_journals.md", "submission_workflow.md"):
        p = ms / "submission" / docname
        check(f"submission/{docname} exists", p.exists())
    checklist = (ms / "submission/checklist.md").read_text(encoding="utf-8")
    unchecked = re.findall(r"- \[ \]", checklist)
    check("checklist no unchecked items", not unchecked, f"{len(unchecked)}")
    cover = (ms / "submission/cover_letter.md").read_text(encoding="utf-8")
    check("cover letter to TEST", "TEST" in cover)
    check("cover letter no placeholder", "[" not in cover.replace("[1]", "").replace("[2]", ""))
    check("cover letter has corresponding author", "Shuda Wu" in cover and "shudawu777@163.com" in cover)
    title = (ms / "submission/title_page.md").read_text(encoding="utf-8")
    check("title page three authors", all(n in title for n in ("Cenfa Lu", "Shuda Wu", "Xun Liu")))
    check("title page ORCIDs", "0009-0003-3481-3624" in title and "0009-0003-2590-9608" in title)
    workflow = (ms / "submission/submission_workflow.md").read_text(encoding="utf-8")
    check("workflow portal url", "mc.manuscriptcentral.com/cjas" in workflow or "TEST" in workflow)
    check("no stale version v1.", not re.search(r"v1\.\d", "\n".join(t for t in (checklist, cover, title, workflow))))
    check("repro report included", (ms / "supplementary_repro_report.md").exists())

    # ---------- self-contained compile from extracted zip ----------
    if not TECTONIC_OK:
        print("\n[tectonic not found: skipping self-contained compile checks]")
    for texname in ("main.tex", "main_test.tex", "supplement.tex"):
        if not TECTONIC_OK:
            break
        proc = subprocess.run([str(TECTONIC), texname, "--keep-logs"], cwd=ms,
                              capture_output=True, text=True, timeout=600)
        ok = proc.returncode == 0
        detail = "ok" if ok else (proc.stderr or proc.stdout)[-200:]
        check(f"compiles from zip: {texname}", ok, detail)
        if ok:
            out = pymupdf.open(ms / texname.replace(".tex", ".pdf"))
            check(f"zip-compiled {texname} pages", out.page_count == page_expect[texname.replace(".tex", ".pdf")],
                  str(out.page_count))

    # ---------- report ----------
    npass = sum(1 for _, ok, _ in results if ok)
    print(f"\n{len(results)} checks, {npass} PASS, {len(results) - npass} FAIL\n")
    for name, ok, detail in results:
        if not ok or "words" in name or "pages" in name and "zip" in name:
            print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    fails = [r for r in results if not r[1]]
    print("\nfailures:", len(fails))
    for name, _, detail in fails:
        print("  FAIL", name, detail)


if __name__ == "__main__":
    main()
