# Language polish pass (TEST manuscript)

Requested: run the `paper-polish` and `nature-polishing` skills over the manuscript, remove
AI-sounding wording, and make the prose read like a human wrote it.

Axes used: paper type `methods` (proposes a procedure and compares it against the baseline),
language `en`, journal `generic` (TEST / Springer), sections: whole manuscript.

## What was changed

- 22 paragraph-level edits, applied by script with an exact-match assertion per edit, then five
  follow-up grammar fixes. Numbers, LaTeX macros, labels, tables, figures and citations were not
  touched.
- Em dashes in the main text: 7 to 0. Sentence-initial signposts ("First", "Second", "Third") in the
  discussion were removed, and the roadmap at the end of the introduction was compressed to one
  sentence.
- Abstract rewritten around the evidence actually shown in the paper: two-source joint bootstrap,
  optional third (design) layer, closed-form asymptotic coverage, real-audit coverage 0.00--0.62
  against 0.98/0.30, training-noise share 0.8--8.3%.
- Long compound sentences split (introduction, related work, reproduction of the baseline,
  variance budget, sample-size planning, source ablation, discussion, conclusion). Emphatic words
  ("precisely", "exactly", "crucially") removed where the surrounding numbers already carry the
  point.
- Claims kept at the strength of the evidence: the design layer is described as a sensitivity for a
  realised audit, not as an inferential uncertainty; "closed-form asymptotic coverage" rather than
  "exact coverage"; the synthetic DGP is described as degenerate with the measured correlation
  (0.83) rather than as "nearly a copy of the label".
- Terminology kept stable throughout (demographic parity, equalised odds, held-out estimand,
  population estimand, training / evaluation / constraint-set component) to avoid synonym cycling.

## Verification after the pass

- `python manuscript/check_numbers.py`: 123 numeric strings checked, missing 0.
- `python manuscript/check_refs.py`: 19 entries, 16 exact / 2 near / 1 by-design missing.
- Pages: main 16, TEST version 18, supplement 6, reviewer copy 16, anonymous 16, combined 22.
- `python manuscript/check_package.py`: 13/13 checks pass.
- Rebuilt submission package (v2.0, 24 entries) and release package (165 files, 1.57 MB); both
  self-contained compiles succeed.

## Residual formatting notes

Two overfull equations remain in the appendix of the TEST version (long display formulas inherited
from the generic build, 16.9 pt and 34.2 pt); they do not affect the page count and are recorded in
`manuscript/submission/test_format_notes.md`.
