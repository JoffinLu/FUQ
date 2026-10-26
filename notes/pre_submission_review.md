# Pre-submission review record (Round 21)

Run with the `pre-submission-reviewer` and `nature-reviewer` skills on the TEST-format manuscript
(`manuscript/main.tex`, 17 pp., build of 2026-10-27; supplement `manuscript/supplement.tex`, 6 pp.).

## Review setup

- **Input scope.** Full text and abstract of the generic `article` build, supplement, `results/tables/*`
  JSON files, `notes/repro_report.md`, `notes/theory_sketch.md`, the experiment drivers under
  `code/exps/`, and the release package contents.
- **Assessment boundary.** Theory was checked for algebra and statement-to-proof consistency, not for
  originality of the underlying stochastic-optimisation results. The reproduction was checked against
  the stored result files, not by re-running the full grid. No editorial decision or journal-fit
  certainty is claimed.
- **Isolation limitation.** The three reports below were produced by one reviewer process with explicit
  role separation (each lens read the same immutable packet and did not revise after synthesis started).
  True mutual blindness cannot be guaranteed in a single context, so the agreement reported in the
  synthesis is weaker evidence than an isolated three-referee panel would give. This limitation is
  recorded rather than hidden.
- **Visible evidence base.** `main.tex` (775 lines), `supplement.tex`, 48 result tables, 18 figure PDFs
  (4 in the manuscript), `refs.bib` (19 entries), build and check scripts.

## Reviewer 1 (methodology and statistical theory)

**Overall assessment.** The paper's core argument is sound and the empirical ordering is clear, but two
technical flaws had to be fixed before the case could be established.

**Major strengths.** The decomposition is elementary and persuasive; the diagnostic condition
`m >> T v^2 / sigma_Delta^2` is stated in the form a practitioner can check; the two-source bootstrap is
implemented faithfully; the optimisation-bias analysis in Section 6 is a welcome honesty check.

**Major Concerns**

- R1-M1 (Blocking: Yes). *Sample-size allocation formula inverted.* Section 5 and Appendix A.6 give
  `T = z^2/w^2 (sigma_Delta^2 + sigma_Delta v sqrt(c_T/c_m))`. The first-order conditions of
  `min c_T T + c_m m` give `T = sigma_Delta sqrt(mu/c_T)` and `m = v sqrt(mu/c_m)`, hence
  `m/T = (v/sigma_Delta) sqrt(c_T/c_m)` and, after substituting into the constraint,
  `T = (z^2/w^2)(sigma_Delta^2 + sigma_Delta v sqrt(c_m/c_T))`. With the printed version a higher
  training cost `c_T` would increase `T`, which is impossible. **Resolution test:** derive `T` and `m`
  from the first-order conditions and check the signs of both cost ratios.
- R1-M2 (Blocking: No). *Theorem 1 is not stated as a joint limit.* The display uses `sqrt(T)` while
  the bias term is `O(T^{-1/2})` only under a condition on the averaged iterate; the statement should
  say `T, m -> infinity` with `m/T -> lambda`, and the proof should mark where the optimisation bias is
  absorbed.
- R1-M3 (Blocking: No). *The Taylor-linearisation step in Appendix A.2 is not valid for a non-smooth
  functional.* A first-order expansion of the empirical process in theta requires differentiability of
  the map theta -> (Delta(theta), P h_theta) at a fixed point; state Hadamard differentiability and the
  Donsker property, or replace with a direct empirical-process argument.
- R1-M4 (Blocking: No). *The protocol-A evaluation resample count is not reported.* The driver uses 400
  evaluation resamples for the synthetic studies (`combine_ci_v3_fresh_eval.py`) and 300 for the real
  audits (`real_joint_ci.py`), while the text says only "B bootstrap replications". Report the number,
  name it distinctly from `R` (the resample count collides with the penalty symbol `R` in the DM
  objective), and add it to the notation table.

**Minor Comments.** Write W_2 and MIS definitions close to first use; avoid the phrase "exact
coverage" for an asymptotic formula; make the sign convention of the gap explicit in the summary.
**Recommendation posture.** Major revision on R1-M1; the rest are minor fixes.

## Reviewer 2 (fairness and machine learning)

**Overall assessment.** The paper is well positioned against the online-bootstrap baseline and the
reproduction is a genuine contribution. Claims must match what the experiments actually do.

**Major strengths.** Clear gap statement; honest treatment of the degenerate synthetic generator;
practical design guidance that a fairness auditor could use.

**Major Concerns**

- R2-M1 (Blocking: Yes). *"Resamples all three sources" overclaims.* The abstract, contribution 2 and
  conclusion say the bootstrap resamples training, evaluation and constraint-set samples, while every
  coverage experiment fixes `D'` and resamples two sources; the constraint-set layer is never evaluated
  in the tables. Either evaluate the three-source variant or state the two-source construction as the
  method and the third layer as an option for a random audit design. **Resolution test:** grep the
  experiment drivers for constraint-set resampling; none exists.
- R2-M2 (Blocking: No). *Figure 4 caption generalises too far.* "Each single-source interval fails
  where the source it ignores dominates" is contradicted by the evaluation-only column for synthetic DI
  at `m = 100`, which reaches 0.98. Name the settings where each variant fails.
- R2-M3 (Blocking: No). *The reported violation factor conflicts with Table 4.* "Two to three orders
  of magnitude" is not supported: the ratio `(se_eval/se_train)^2` is 21.5 (Adult), 78.7 (ACSIncome)
  and 4.5 (COMPAS), so the text should say factors of 4.5 to 79.
- R2-M4 (Blocking: No). *Different population values of phi appear without explanation.* Table 2 uses
  the held-out estimate (0.0835) while Table 3 reports the population value (0.0212). Say which
  estimand each table reports and why they differ.

**Minor Comments.** "Constant step size" contradicts the printed decay schedule `eta_0 k^{-0.501}`;
"the reported population gap" should name the estimand; the related-work paragraph could mention the
fairness-audit measurement-error literature, but only if a verified reference is added.
**Recommendation posture.** Major revision on R2-M1; major on R2-M3 (claim-to-table conflict); the
rest minor.

## Reviewer 3 (reproducibility and applied audit)

**Overall assessment.** The reproduction package is unusually complete. The remaining risks are
reporting risks: artefacts that the text points to must exist, and the audit story must be reproducible
from the released code.

**Major strengths.** Released code, stored raw results, and a deviations table; a full reproduction of
a paper without official code; figures regenerated from scripts.

**Major Concerns**

- R3-M1 (Blocking: No). *"Constant step size" is wrong.* The reproduction follows a decayed schedule
  (`eta_k = eta_0 k^{-0.501}`); the deviations table already says the published schedule does not reach
  the convergence regime, so the prose should match the table.
- R3-M2 (Blocking: No). *The paper points to a complete reproduction report but only summarises it.*
  Appendix B summarises deviations; say that the complete report is released with the code, and give
  the reviewer-time access route.
- R3-M3 (Blocking: No). *The audit-budget paragraph is overloaded.* It mixes the feasible-region
  figure, the minimum certifiable gap and the width floor; split it and check the ratio arithmetic
  (1.5 and 21 against the table values).

**Minor Comments.** Add the companion note to Fig 3 that the gap annotations were removed and the
values are given in the text; make the replicate counts consistent between table captions and the
protocol section; report the per-run wall-clock cost of the joint bootstrap.
**Recommendation posture.** Minor revision; no blocking concern.

## Cross-review synthesis (post-review; not shown to the reviewers)

- **Consensus blocking concerns.** R1-M1 (sample-size formula) and R2-M1 (three-source claim). Both
  strike at the paper's case: one is a wrong formula, the other an overclaim about the experiments.
- **Other consensus major concerns.** R1-M4 (unreported resample count, plus symbol collision),
  R2-M3 (violation factor vs Table 4), R3-M1 (constant step size), R2-M4 (phi estimands).
- **Minor checklist.** Theorem 1 joint limit; Appendix A.2 linearisation; Figure 4 caption; Figure 3
  caption (half-width); density of the sample-size paragraph; data availability wording; notation row
  for the evaluation resample count; reproduction-report phrasing.
- **Where emphasis differs.** R1 weights the algebra and the proof, R2 the claims and the experiment
  description, R3 the artefact-level reproducibility. Agreement on the two blocking items is
  independent enough to act on; the minor lists overlap only partially.

## What was changed (all in `manuscript/main.tex`; verified after rebuild)

| Concern | Change | Evidence |
|---|---|---|
| R1-M1 | Both `T` and `m` formulas now use `sqrt(c_m/c_T)` and `sqrt(c_T/c_m)` in the direction the Lagrangian gives | Appendix A.6 display; Section 5 inline display |
| R2-M1 | Abstract, contribution 2, Method, Discussion and Conclusion now say two-source construction for a fixed design, with the constraint-set layer as an option for a random design | grep "three sources" = 0 hits in `main.tex` |
| R2-M3 | "two to three orders" replaced by "factors of 4.5 to 79 (Table 4)" | contribution 1; `check_numbers.py` unchanged |
| R1-M4 | Evaluation resample count now named `Q` (400 synthetic, 300 real), reported in the protocol paragraph and Table 3/6 captions, and added to Table 1 | notation table row `Q` |
| R1-M2 | Theorem 1 stated with `T, m -> infinity` and `m/T -> lambda` | theorem statement |
| R1-M3 | Appendix A.2 now splits the error into three terms and uses Hadamard differentiability plus the Donsker property instead of a first-order Taylor expansion of the empirical process | Appendix A.2 |
| R2-M2 | Figure 4 caption now names the settings: training-only undercovers everywhere, evaluation-only undercovers on synthetic DM at m=100 (0.81) | Fig. 4 caption |
| R2-M4 | Table 3 caption states that the reported phi is the population value and why it differs from Table 2 | Table 3 caption |
| R3-M1 | "constant step size" replaced by "step-size schedule" in both places | intro and reproduction paragraph |
| R3-M2 | Data availability now says the complete report comes with the code and is available on request during review | Statements |
| R3-M3 | Sample-size paragraph split; ratios 1.5 and 21 checked against Table 4 components | Section 6 |
| minor | Figure 3 caption "width" -> "half-width"; Figure 2/3 numbers preserved; reproduction and limitations paragraphs split; A.1 notation conflict (`phi_theta` -> `h_theta`) fixed | captions, appendix |

Verification after the rebuild: `main.pdf` 17 pages, `main_test.pdf` 18 pages, `supplement.pdf` 6
pages, reviewer copy 17 pages, combined PDF 23 pages; `check_numbers.py` 123 numeric strings, 0
missing; `check_package.py` 13/13 PASS; submission zip 1.04 MB / 24 entries with self-contained
compiles; release 166 files / 1.99 MB.
