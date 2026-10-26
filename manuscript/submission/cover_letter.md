# Cover letter

> 占位符用 `[ ]` 标出，提交前替换（日期、仓库 URL/DOI）。

---

[Date]

The Editor-in-Chief
*TEST*

Dear Editor,

We are pleased to submit our manuscript **"Separating Training, Evaluation and Constraint-Set Noise
in Fairness Uncertainty Quantification"** for consideration as an original research article in
*TEST*.

**What the paper does.** Fairness-aware classifiers are trained by stochastic optimisation and
evaluated on finite held-out samples, so reported demographic-parity or equalised-odds gaps are
random. A recent line of work quantifies this randomness with an online multiplier bootstrap. We show
that such intervals cover only the *training* component: the error of a reported gap decomposes into
training, evaluation and constraint-set sampling components, which are asymptotically independent. We
derive the limiting distribution and the exact coverage loss of the existing interval as a function of
the ratio between training iterations and evaluation size, and we propose a joint bootstrap that
resamples all three sources and is asymptotically valid. A variance budget on Adult, ACSIncome and
COMPAS shows that training noise contributes only 0.8%–8.3% of the total uncertainty, whereas
evaluation sampling (37%–78%) and constraint-set sampling (18%–55%) dominate. At the audit budgets
used in practice the minimum certifiable gap exceeds the reported gap in two of the three datasets,
which yields concrete guidance on how to allocate audit effort. The paper further reports a full
reproduction of the baseline (no official code exists) and documents two reproducibility findings: the
published step size does not reach the reported convergence regime, and the synthetic generator is
close to degenerate, an issue that matters when the generator is used to demonstrate fairness
mechanisms.

**Why this journal.** The contribution is methodological statistics: a three-source variance
decomposition with a limiting distribution, an exact coverage-loss formula, a joint resampling
estimator with an asymptotic validity result and a sample-size allocation rule, supported by a
reproducible simulation study and three real audit datasets. This mix of methodology, theory and
applications is the profile of *TEST*, and the paper is written to be accessible to statisticians
without prior expertise in fairness auditing. All experiments are reproducible from the released
code, and the supplement documents the full protocol, per-dataset tables and an independent
verification of every primitive operation.

**Statements.**
- The manuscript is original, has not been published elsewhere, and is not under consideration by
  another journal.
- The author has read and approved the submitted version and agrees to its submission.
- The author declares no competing interests.
- Data are public benchmarks; code and all result files are available at [repository URL / DOI].
- A 6-page supplement documents the full simulation protocol, per-dataset tables, the independent
  verification of the primitive operations and the reproduction commands.
- **Use of AI tools:** an AI-based language tool was used only to polish the English expression of
  the manuscript; it was not used to generate scientific content, code, or results, and the author
  verified every statement and number in the paper.
- The manuscript was prepared with the official Springer Nature LaTeX template (`sn-jnl`, class
  option `sn-basic`).

We suggest the following potential reviewers, whose expertise covers statistical inference for
fairness, evaluation-only inference and auditing methodology: Jad Salem (Ecole Polytechnique), Linjun
Zhang (Rutgers University), Nathan Kallus (Cornell University), Krishnaram Kenthapadi (Amazon) and
Harvineet Singh (Amazon); contact details are available on request and can be added in the submission
system. None of the suggested reviewers is a collaborator of the author.

Thank you for your consideration.

Sincerely,

Cenfa Lu
joffin@163.com
ORCID: 0009-0003-3481-3624
School of Mathematics and Computational Science, Guilin University of Electronic Technology, Guilin 541004, China
(corresponding author)
