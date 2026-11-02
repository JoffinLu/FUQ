# fuq-fairness — Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification

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

## Use of AI tools

The associated manuscript openly discloses that an AI-based assistant was used to help
implement and run the numerical experiments and to draft and revise the text. Every reported
number was recomputed from the released code and raw output files, and the author takes
responsibility for the full content. No third-party code was copied: the estimators, data
preparation, and verification modules were written from the published equations and the worked
specification in `SPEC.md`; the only redistributed third-party files are the two Springer
Nature template files listed below.

## Third-party files

- `manuscript/sn-jnl.cls` and `manuscript/sn-basic.bst` are the official Springer Nature
  LaTeX template files (LaTeX Project Public License), included unmodified so that the
  submission version compiles without external downloads. They are not part of the
  reproduction code.

## License

MIT (see `LICENSE`). Public datasets (Adult, COMPAS, ACSIncome) retain their original licenses and are
not redistributed here.
