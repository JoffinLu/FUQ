"""Round 16: update check_package.py expected numbers for the TEST submission (v2.0)."""
from pathlib import Path

p = Path("manuscript/check_package.py")
s = p.read_text(encoding="utf-8")

s = s.replace("""  * main.pdf has 15 pages, supplement.pdf has 6 pages;
  * main.tex contains 7 tables and 4 figures;
  * check_numbers.py verifies 123 numbers with none missing;
  * refs_checked.json covers 18 bibliography entries with no missing DOI;
  * submission zip v1.9 exists with 20 entries and contains both PDFs;
  * release zip exists and contains MANIFEST.tsv with 157 files.""",
              """  * main.pdf has 16 pages, main_test.pdf has 17 pages, supplement.pdf has 6 pages;
  * main.tex contains 7 tables and 4 figures;
  * check_numbers.py verifies 123 numbers with none missing;
  * refs_checked.json covers 18 bibliography entries with no missing DOI;
  * submission zip v2.0 exists with 24 entries and contains the three PDFs;
  * release zip exists and contains MANIFEST.tsv with 157 files;
  * reviewer copy (16 pages) and combined PDF (22 pages) exist.""")

s = s.replace('checks.append(("main pages", pdf_pages(HERE / "main.pdf") == 15,',
              'checks.append(("main pages", pdf_pages(HERE / "main.pdf") == 16,')
s = s.replace('checks.append(("supplement pages", pdf_pages(HERE / "supplement.pdf") == 6,',
              'checks.append(("main_test pages", pdf_pages(HERE / "main_test.pdf") == 17, f"{pdf_pages(HERE / \'main_test.pdf\')}"))\n    checks.append(("supplement pages", pdf_pages(HERE / "supplement.pdf") == 6,')

s = s.replace('sub = HERE / "submission" / "fuq-fairness_submission_v1.9.zip"',
              'sub = HERE / "submission" / "fuq-fairness_submission_v2.0.zip"')
s = s.replace('checks.append(("submission zip v1.9", False, "missing"))',
              'checks.append(("submission zip v2.0", False, "missing"))')
s = s.replace('''        ok = len(names) == 20 and "manuscript/main.pdf" in names and "manuscript/supplement.pdf" in names
        checks.append(("submission zip v1.9", ok, f"{len(names)} entries"))''',
              '''        ok = (
            len(names) == 24
            and "manuscript/main.pdf" in names
            and "manuscript/main_test.pdf" in names
            and "manuscript/supplement.pdf" in names
            and "manuscript/sn-jnl.cls" in names
        )
        checks.append(("submission zip v2.0", ok, f"{len(names)} entries"))''')

s = s.replace('checks.append(("reviewer copy", pages == 15, f"{pages} pages"))',
              'checks.append(("reviewer copy", pages == 16, f"{pages} pages"))')
s = s.replace('checks.append(("combined PDF", pages == 21, f"{pages} pages"))',
              'checks.append(("combined PDF", pages == 22, f"{pages} pages"))')

p.write_text(s, encoding="utf-8")
print("check_package.py updated")
