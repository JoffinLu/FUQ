"""Round 16: patch build scripts, rebuild all PDFs and packages (TEST version)."""
from pathlib import Path
import re

ROOT = Path(".")
HERE = ROOT / "manuscript"

# ---------------------------------------------------------------- build_submission.py
p = HERE / "build_submission.py"
s = p.read_text(encoding="utf-8")
s = s.replace("(v1.9)", "(v2.0)")
s = s.replace("""    manuscript/{main.tex,main.pdf,supplement.tex,supplement.pdf,refs.bib,
                refs_checked.json,make_supplement.py,check_numbers.py,
                check_refs.py,README.md,supplementary_repro_report.md,
                submission/{checklist,cover_letter,target_journals,
                            jcgs_format_notes,title_page}.md}""",
              """    manuscript/{main.tex,main.pdf,main_test.tex,main_test.pdf,sn-jnl.cls,
                sn-basic.bst,supplement.tex,supplement.pdf,refs.bib,
                refs_checked.json,make_supplement.py,check_numbers.py,
                check_refs.py,README.md,supplementary_repro_report.md,
                submission/{checklist,cover_letter,target_journals,
                            test_format_notes,title_page}.md}""")
s = s.replace('Usage: python manuscript/build_submission.py [--version v1.8] [--skip-compile]',
              'Usage: python manuscript/build_submission.py [--version v2.0] [--skip-compile]')
s = s.replace('''FILES = [
    "main.tex", "main.pdf", "supplement.tex", "supplement.pdf", "refs.bib",
    "refs_checked.json", "make_supplement.py", "check_numbers.py", "check_refs.py", "README.md",
]
SUBMISSION = ["checklist.md", "cover_letter.md", "target_journals.md", "jcgs_format_notes.md", "title_page.md"]''',
              '''FILES = [
    "main.tex", "main.pdf", "main_test.tex", "main_test.pdf", "sn-jnl.cls", "sn-basic.bst",
    "supplement.tex", "supplement.pdf", "refs.bib",
    "refs_checked.json", "make_supplement.py", "check_numbers.py", "check_refs.py", "README.md",
]
SUBMISSION = ["checklist.md", "cover_letter.md", "target_journals.md", "test_format_notes.md", "title_page.md"]''')
s = s.replace('for tex in ["main.tex", "supplement.tex"]:', 'for tex in ["main.tex", "main_test.tex", "supplement.tex"]:')
s = s.replace('ap.add_argument("--version", default="v1.9")', 'ap.add_argument("--version", default="v2.0")')
p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------- make_supplement.py: add build_test_tex command
p = HERE / "make_supplement.py"
s = p.read_text(encoding="utf-8")
anchor = "python code/reproduce_all.py --scale full         # one-command driver for all runs"
if anchor in s:
    s = s.replace(anchor, anchor + "\npython code/build_test_tex.py                        # TEST (Springer) LaTeX version -> main_test.tex")
else:
    print("WARN: reproduce_all anchor not found in make_supplement.py")
p.write_text(s, encoding="utf-8")

print("patched build_submission.py and make_supplement.py")
