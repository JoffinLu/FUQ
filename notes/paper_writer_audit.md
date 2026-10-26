# Paper-writer audit (Round 18)

Audit of `manuscript/main.tex` (the manuscript from which the TEST version `main_test.tex`
is generated) performed under the `paper-writer` skill, after the Round 17 five-perspective
self-review recorded in `notes/review_changes.md`. Scope: full manuscript, evidence
discipline, writing rules, citation layer. All changes are listed in §3; nothing is
paraphrased from memory or from the model.

## 1. Evidence base

| Source | Content | Use |
|---|---|---|
| `results/tables/*.json|.csv` (48 files) | reproduction, protocol A, variance budget, sensitivity, source ablation, finite-sample grid, convergence rates | every number in the paper |
| `results/raw/*` | per-repetition raw records | checked when a table was ambiguous |
| `code/core/*.py`, `code/exps/*.py` | estimators, bootstrap, experiment drivers | mechanism claims, reproduction commands |
| `notes/repro_report.md`, `notes/verification.md`, `notes/extension_results.md`, `notes/reproducibility_verification.md` | reproduction findings, independent verification V1–V7, extension results | reproduction and deviation claims |
| `paper/main_text.txt` | published paper text | what the baseline does and reports |
| `refs.bib` (19 entries) | literature | citation-level statements only |

## 2. Findings and disposition

Severity: CRITICAL / MAJOR / MINOR.

| # | Severity | Finding (evidence) | Fix |
|---|---|---|---|
| F1 | CRITICAL | Abstract, contribution 2 and Conclusion said the joint bootstrap "resamples all three sources", while Theorem 2 conditions on the design and the experiments use two sources (fixed `D'`; `real_joint_ci.py` docstring) | Abstract/contributions/method/conclusion now separate a two-source construction (fixed design) from an optional constraint-set layer; experiments labelled as two-source |
| F2 | MAJOR | Intro said evaluation noise "3.9 times" the training noise; Table 4 gives se(eval)/se(train) = 0.0259/0.0056 = 4.6 for Adult | changed to 4.6 with a pointer to Table 4 |
| F3 | MAJOR | "violated by orders of magnitude" (contribution 1) unsupported by a number | "by two to three orders of magnitude": (m/T)/(v²/σ²_Δ) = 0.0004–0.004 with the Table 4 components |
| F4 | MAJOR | Theorem 2's design-layer clause did not state the `S → ∞` requirement used in the proof | clause now reads "If the design is random, the third term is included, and S → ∞" |
| F5 | MINOR | "exact coverage" for Corollary 1 (a closed-form asymptotic expression) | "closed-form asymptotic coverage" in abstract, contribution 1, appendix A |
| F6 | MINOR | "held-out sets used in practice" (unsupported generalisation) | "a finite held-out set" |
| F7 | MINOR | "costs one extra pass over the evaluation set" (the joint bootstrap is R vectorised passes) | "adds a few vectorised passes over the held-out predictions" |
| F8 | MINOR | Figure 2 caption's mechanism claim ("penalty frozen at its training value inside the feasible region") is not supported by any stored result | caption rewritten around measured quantities: half-width 0.058 vs evaluation standard error 0.062, population coverage 0.62 |
| F9 | MINOR | "nearly a copy of the label" for the synthetic generator was qualitative only | quantified: corr(z,y) = 0.828, attribute-only label accuracy 0.909 (`dgp_di(200000, seed=20261026)`); recorded in `notes/repro_report.md` |
| F10 | MINOR | Figure 1 caption said the interval "covers the held-out estimand" (it covers it in 0.89 of repetitions) | caption now states 0.89 and 0.43 |
| F11 | MINOR | Appendix B referred to a "complementary sensitivity analysis for the DM penalty" that does not exist in the results | replaced by the released report's optimisation-bias record |
| F12 | MINOR | Data-availability statement said the reproduction report is "included as Appendix B" (it is released with the code) | corrected |
| F13 | MINOR | AI-use statement ("language polish only") understated the actual use of AI assistance | truthful disclosure: assistant helped implement/run experiments and draft/revise text; results re-checked against released code; author takes responsibility |
| F14 | MINOR | "quasi-Newton method" for the constraint-set solves (the code uses the configured constrained solver) | "standard constrained solver" |
| F15 | MINOR | "σ²_Δ and v² are of the same order" (both equal in L2 theory, not an empirical fact about the regimes) | "the evaluation variance is not negligible in the regimes we study" |
| F16 | MINOR | Protocol (B) described as "a single run with the reported audit budget" without saying how it is used | explicit: operating point in Figure 3, planning uses protocol (A) components at this budget |
| F17 | MINOR | van der Vaart & Wellner (1996) mentioned by name with no bibliography entry | `vdvwellner1996` added (DOI 10.1007/978-1-4757-2545-2, verified via Crossref: "Weak Convergence and Empirical Processes", Springer, 1996) |
| F18 | MINOR | Deviations-table rationale for θ* ("audit-protocol baseline") vague | "evaluate estimand at constraint optimum" |
| F19 | MINOR | Subgroup-variance sentence in Related work made an unlinked claim | now tied to Lemma 2 (evaluation variance) |
| F20 | MINOR | `main_test.tex` was built from a stale `main.tex` | regenerated by `code/build_test_tex.py` before compiling |

## 3. Claim-to-evidence map (spot checks performed)

| Claim in paper | Evidence |
|---|---|
| baseline coverage 0.30 / 0.25 / 0.62; joint 0.98 / 1.00 / 1.00 | `results/tables/real_joint_ci_{adult,acsincome,compas}.json` |
| synthetic protocol A coverage 0.56 / 0.85 / 0.99 (m = 100 / 1000 / 5000) | `results/tables/joint_bootstrap_v3b_fresh_eval.json` |
| variance shares 3.6/78.3/18.1, 0.8/60.3/39.0, 8.3/37.1/54.6 | `results/tables/variance_budget_*.json` |
| source-ablation 7 settings | `results/tables/ablation_*.json` |
| finite-sample grid (Table S9) | `results/tables/ablation_fs_T*_m*.json` |
| convergence slopes 0.47 / 0.46 (theory −0.5) | `results/tables/rate_check_synth_di.json` |
| κ sensitivity table | `results/tables/sensitivity_adult.csv` |
| minimum detectable gaps | `results/tables/min_detectable_gap.csv` |
| reproduction numbers (Table 1, Table S2) | `results/tables/repro_summary.csv` |

## 4. Verification status

- `python manuscript/check_numbers.py` → 123 numeric strings checked, missing 0.
- `python manuscript/check_refs.py` → 19 entries: 16 exact; 2 near with documented reasons (zhu2021: title match 1.00, author field spans lines in the bib parser; vdvwellner1996: Crossref record of the book omits the subtitle; DOI, author and year verified in both cases); 1 missing by design (`roy2026uq`: UAI 2026 proceedings record is not indexed by OpenAlex; verified against the published PDF and the 2023 arXiv version 2304.13950, recorded with a note). Verdicts are cached in `refs_checked.json`; `--refresh` forces a fresh network pass.
- `main.pdf` 16 pages, `main_test.pdf` 18 pages, 0 undefined references; `main_test` carries 2 pre-existing appendix-equation overfull boxes (16.9 pt and 34.2 pt) that are inherited from the wide display equations and do not clip in print.
- `python manuscript/check_package.py` → 13/13 (page, table, figure, number, reference, supplement-numbering, submission-zip and release checks).

## 5. Capability note (paper-writer Phase-5 degradation)

The independent fresh-context citation verification sub-agent could not be used: the
sub-agents returned product errors (no output) in Rounds 17 and 18. Per the
verification-ladder degradation rule, the citation layer was instead checked
programmatically (OpenAlex title/author/year matching plus Crossref DOI resolution) and
every literature statement was capped at citation level — no sentence asserts a specific
numerical result or internal mechanism of a cited work. This is disclosed here rather than
hidden; the code-checked claims are unaffected.

## 6. Remaining known gaps (not fabricated to fill)

- `refs.bib` has 19 entries; a full Introduction in this genre typically weaves 15–25
  works and Related Work 15–30. The current set covers the directly relevant lines
  (fairness auditing, DP/EO, SGD/SA, bootstrap, constrained optimisation, distribution-free
  inference). Additional citations would require full-text verification to be useful.
- The third (constraint-set) variance component is studied as a design/target decomposition
  (Table 4, Section 3.3), not as a resampling layer in the experiments; the paper now says
  exactly this in the abstract, contributions, method and conclusion.
