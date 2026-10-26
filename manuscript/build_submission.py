"""Build the standalone manuscript submission package (v2.0) and verify it compiles.

Layout inside the archive mirrors the repository so that relative figure paths
(`../results/figures/...`) resolve after extraction:

    manuscript/{main.tex,main.pdf,main_test.tex,main_test.pdf,sn-jnl.cls,
                sn-basic.bst,supplement.tex,supplement.pdf,refs.bib,
                refs_checked.json,make_supplement.py,check_numbers.py,
                check_refs.py,README.md,supplementary_repro_report.md,
                submission/{checklist,cover_letter,target_journals,
                            test_format_notes,title_page}.md}
    results/figures/{repro_synth_di,repro_compas,sample_size,
                     ablation_coverage}.pdf

Usage: python manuscript/build_submission.py [--version v2.0] [--skip-compile]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
TECTONIC = ROOT.parent / "tools" / "tectonic" / "tectonic.exe"

FILES = [
    "main.tex", "main.pdf", "main_test.tex", "main_test.pdf", "sn-jnl.cls", "sn-basic.bst",
    "supplement.tex", "supplement.pdf", "refs.bib",
    "refs_checked.json", "make_supplement.py", "check_numbers.py", "check_refs.py", "README.md",
]
SUBMISSION = ["checklist.md", "cover_letter.md", "target_journals.md", "test_format_notes.md", "title_page.md"]
FIGURES = [
    "results/figures/repro_synth_di.pdf",
    "results/figures/repro_compas.pdf",
    "results/figures/sample_size.pdf",
    "results/figures/ablation_coverage.pdf",
]


def build(version: str, compile_check: bool) -> Path:
    staging = Path(tempfile.mkdtemp(prefix="fuq_submit_"))
    try:
        ms = staging / "manuscript"
        ms.mkdir(parents=True)
        for name in FILES:
            shutil.copy2(HERE / name, ms / name)
        shutil.copy2(HERE.parent / "notes" / "repro_report.md", ms / "supplementary_repro_report.md")
        (ms / "submission").mkdir()
        for name in SUBMISSION:
            shutil.copy2(HERE / "submission" / name, ms / "submission" / name)
        fig = staging / "results" / "figures"
        fig.mkdir(parents=True)
        for rel in FIGURES:
            shutil.copy2(ROOT / rel, fig / Path(rel).name)

        archive = HERE / "submission" / f"fuq-fairness_submission_{version}.zip"
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(staging).as_posix())
        count = len(zipfile.ZipFile(archive).namelist())
        print(f"submission: {archive} ({archive.stat().st_size / 1024:.0f} KB, {count} entries)")

        if compile_check:
            check = Path(tempfile.mkdtemp(prefix="fuq_check_"))
            try:
                zipfile.ZipFile(archive).extractall(check)
                assert TECTONIC.exists(), f"tectonic not found at {TECTONIC}"
                for tex in ["main.tex", "main_test.tex", "supplement.tex"]:
                    proc = subprocess.run(
                        [str(TECTONIC), tex],
                        cwd=check / "manuscript",
                        capture_output=True, text=True, errors="ignore",
                    )
                    status = "OK" if proc.returncode == 0 else f"FAIL({proc.returncode})"
                    print(f"  self-contained compile {tex}: {status}")
                    if proc.returncode != 0:
                        print(proc.stderr[-800:])
                        raise SystemExit(1)
            finally:
                shutil.rmtree(check, ignore_errors=True)
        return archive
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", default="v2.0")
    ap.add_argument("--skip-compile", action="store_true")
    args = ap.parse_args()
    build(args.version, not args.skip_compile)
