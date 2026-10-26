# Source release — Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification

This archive contains everything needed to reproduce the numbers reported in the paper and its
supplementary material, except the two public datasets, which are downloaded from their original
sources (see `DATA_NOTES.md`).

> Working title; authors and the final title are to be confirmed.

## Contents

| path | what it is |
|---|---|
| `code/core/` | `fairuq.py` (online multiplier bootstrap, training updates) and `dgp.py` (synthetic generators) |
| `code/data_prep/00_all.py` | builds `data/processed/*.npz` from `data/raw/` (runs the three dataset scripts; idempotent) |
| `code/exps/` | every experiment in the paper: reproduction runs, protocol-A joint bootstrap, variance budget, sensitivity, source ablation, convergence-rate check, figure scripts |
| `code/verify/` | independent reference implementation of the primitive operations (supplement Table 7) |
| `code/tests/test_invariants.py` | 16 fast invariant checks of the primitives (< 1 s): projection/KKT, multiplier moments, fairness functionals, finite-difference gradients, determinism, generators |
| `requirements.txt` | pinned Python environment used for every number in the paper |
| `code/reproduce_all.py` | one-command driver (`--scale light` for a smoke test, `--scale full` for all reported runs) |
| `results/tables/` | the only source of the numbers in the manuscript (JSON/CSV) |
| `results/raw/` | per-repetition raw outputs |
| `manuscript/` | LaTeX source + compiled PDFs of the paper and of the supplementary material |
| `manuscript/check_numbers.py` | checks 111 numeric strings in `main.tex` against `results/tables/` |
| `notes/` | reproduction report, independent verification, theory sketch, extended results, data notes, referee preparation |
| `submission/` | cover letter, target-journal notes, JAS format notes, checklist, title page |

## Reproduce

```bash
# 1. Python 3.11+ (tested on 3.13.15): python -m pip install -r requirements.txt   (no GPU)
# 2. fast correctness check of the primitives (no data needed):
#    python code/tests/test_invariants.py            # 16 checks, < 1 s
# 3. put the raw datasets in data/raw/ (or set FUQ_RAW_DIR=<dir>; see DATA_NOTES.md), then:
python code/data_prep/00_all.py
python code/reproduce_all.py --scale full        # ~2 h on one CPU
python manuscript/check_numbers.py               # exits 0 iff manuscript numbers match tables

# LaTeX (Tectonic, or pdflatex+bibtex):
cd manuscript && tectonic main.tex && tectonic supplement.tex
```

`python code/reproduce_all.py --scale light` runs a minutes-scale end-to-end smoke test whose
outputs are tagged `*_light` and do not touch the reported tables.

Verified end-to-end: extracting this archive and running
`python code/reproduce_all.py --scale light` (with the raw datasets made visible through
`FUQ_RAW_DIR`/`--data-root`, or with `data/processed/` copied in) finishes in about 25 s with
exit code 0 and prints `checked 111 numeric strings; missing 0`.

## Findings in one paragraph

The existing online-bootstrap interval for a reported fairness gap quantifies only the noise of the
optimisation trajectory; the sampling noise of the held-out evaluation set and of the random
constraint set that defines the fairness-aware estimator are separate, asymptotically independent
components.  With the held-out sizes used in practice the evaluation component dominates, so the
existing interval covers the population gap with probability as low as 0.00–0.62 instead of 0.95.
A joint bootstrap that resamples all three sources restores nominal coverage (0.98–1.00) at a
width cost of a factor 1.15–5.72, and a variance budget shows that training noise contributes only
0.8–8.3% of the total uncertainty in typical audits.

## License

Code: MIT (see `LICENSE`); manuscript text: not yet released under a license (to be confirmed);
datasets: governed by their original licenses (`DATA_NOTES.md`).
