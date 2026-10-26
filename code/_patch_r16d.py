"""Round 16: release includes TEST files; prepare GitHub repository files."""
from pathlib import Path

ROOT = Path(".")

# ---------------------------------------------------------------- make_release.py
p = ROOT / "code" / "make_release.py"
s = p.read_text(encoding="utf-8")
add = '''    ("manuscript/main_test.tex", "manuscript/main_test.tex"),
    ("manuscript/main_test.pdf", "manuscript/main_test.pdf"),
    ("manuscript/sn-jnl.cls", "manuscript/sn-jnl.cls"),
    ("manuscript/sn-basic.bst", "manuscript/sn-basic.bst"),
'''
anchor = '    ("manuscript/main.pdf", "manuscript/main.pdf"),\n'
assert anchor in s
if "main_test.tex" not in s:
    s = s.replace(anchor, anchor + add)
s = s.replace('    ("code/reproduce_all.py", "code/reproduce_all.py"),\n',
              '    ("code/reproduce_all.py", "code/reproduce_all.py"),\n    ("code/build_test_tex.py", "code/build_test_tex.py"),\n    ("code/make_release.py", "code/make_release.py"),\n')
p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------- GitHub files
(ROOT / "README.md").write_text(
    """# fuq-fairness — Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification

Source code and results for the paper

> **Cenfa Lu.** *Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty
> Quantification.* Manuscript prepared for *TEST* (Springer), 2026.

Fairness diagnostics such as the demographic-parity (DP) or equalised-odds (EO) gap are computed from
a finite evaluation sample for a classifier trained by a stochastic optimiser, so the reported gap is
random. This repository contains

1. a **three-source variance decomposition** (training, evaluation, constraint-set sampling) of the
   reported gap, with the limiting distribution and the exact coverage loss of the existing
   training-only interval;
2. a **joint bootstrap** that resamples all three sources and restores nominal coverage, with an
   asymptotic validity result and a sample-size allocation rule;
3. a **full reproduction** of the baseline experiments (no official baseline code exists), including
   two documented deviations (step size, near-degenerate synthetic generator);
4. all **result tables, vector figures and verification scripts** behind the numbers in the paper and
   its 6-page supplement.

## Repository layout

```
code/            implementation, experiments, verification, reproducibility drivers
  core/          fairuq.py (projection, SGD, multipliers, phi_hat, MIS/W2), dgp.py, optimum.py
  exps/          reproduction and extension experiments, figure generation
  verify/        independent re-implementation of every primitive operation
  data_prep/     public-data preparation (Adult, COMPAS, ACSIncome)
  tests/         fast invariant tests (16 checks)
  reproduce_all.py  one-command full/light driver
results/         tables/, figures/ (vector PDF), raw/ (per-replication logs)
manuscript/      main.tex/pdf (generic), main_test.tex/pdf (TEST/Springer template), supplement
notes/           reproduction report, verification record, theory sketch, referee preparation
data/raw/        public datasets (not tracked; see DATA_NOTES in notes/)
```

## Reproduce

```bash
python -m pip install -r requirements.txt
python code/data_prep/00_all.py        # public data -> data/processed/*.npz
python code/reproduce_all.py --scale light   # ~25 s smoke of the whole pipeline
python code/reproduce_all.py --scale full    # full experiment grid (~2 h, single CPU)
python manuscript/check_numbers.py          # every number in the paper vs result files
```

The full-precision tables used in the paper are committed under `results/tables/`, so the manuscript
can be rebuilt without rerunning the experiments.

## Build the manuscripts

```bash
# generic article version
cd manuscript && tectonic main.tex
# TEST (Springer) version -- official Springer Nature template, sn-jnl.cls (included)
python code/build_test_tex.py
cd manuscript && tectonic main_test.tex
# supplementary material (tables are generated from results/tables automatically)
python manuscript/make_supplement.py && cd manuscript && tectonic supplement.tex
```

## Reproducibility status

- All five reproduction experiments (synthetic DP/DM, Adult, ACSIncome, COMPAS) match the
  pre-registered published settings documented in `notes/repro_report.md`.
- Every primitive operation (slab projection, multiplier distribution, MIS, constrained optimum) has
  an independent second implementation in `code/verify/`.
- `manuscript/check_numbers.py` verifies 123 reported numbers against the result files;
  `manuscript/check_package.py` verifies the artifact/PDF consistency of the submission package.
- A full rerun on 2026-10-26 reproduced all tables value-for-value (only wall-clock fields differ).

## License

MIT (see `LICENSE`). Public datasets (Adult, COMPAS, ACSIncome) retain their original licenses and are
not redistributed here.
""",
    encoding="utf-8",
)

(ROOT / ".gitignore").write_text(
    """# data: public datasets and derived archives are not tracked
data/raw/
data/processed/

# build artifacts and local outputs
release/
release/stage/
manuscript/*.aux
manuscript/*.out
manuscript/*.log
manuscript/*.blg
manuscript/*.bbl
manuscript/*.toc
manuscript/_*.tex
manuscript/_*.py
manuscript/main_review.tex
manuscript/main_anonymous.tex
manuscript/format_check_twocolumn.tex
manuscript/format_check_twocolumn.pdf
manuscript/fuq-fairness_full.pdf

# submission zips (rebuilt by manuscript/build_submission.py)
manuscript/submission/*.zip

# python
__pycache__/
*.pyc
.ipynb_checkpoints/
.venv/
""",
    encoding="utf-8",
)

(ROOT / "LICENSE").write_text(
    """MIT License

Copyright (c) 2026 Cenfa Lu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    encoding="utf-8",
)

(ROOT / "CITATION.cff").write_text(
    """cff-version: 1.2.0
message: "If you use this code or the results, please cite the manuscript."
type: software
title: "fuq-fairness: Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification"
abstract: "Reproduction code, experiments, verification scripts and result tables for the paper 'Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification'."
authors:
  - family-names: Lu
    given-names: Cenfa
    orcid: "https://orcid.org/0009-0003-3481-3624"
    affiliation: "School of Mathematics and Computational Science, Guilin University of Electronic Technology"
    email: joffin@163.com
license: MIT
version: "1.0.0"
date-released: "2026-10-27"
""",
    encoding="utf-8",
)

print("patched make_release.py; wrote README.md, .gitignore, LICENSE, CITATION.cff")
