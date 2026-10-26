# Reference existence audit (Round 22)

Date: 2026-10-27. Scope: every entry in `manuscript/refs.bib` at the start of the
audit (19 entries). Method: `supervisor-deep-research` citation protocol,
fact-check mode, run serially (no sub-agents).

Reproducible check: `python code/verify/verify_citations.py` re-queries Crossref,
DataCite, arXiv and the JMLR/PMLR listings for all 18 entries and prints one
verdict per entry. Last run: 2026-10-27, 18 verified.

## Result

| status | count |
|---|---|
| verified (record found, metadata reconciled) | 18 |
| of which metadata corrected during the audit | 2 (chen2016, fang2018) |
| unverifiable, removed | 1 (moreau2024) |
| entries after audit | 18 |

`manuscript/refs_checked.json` now reports 15 exact, 2 near, 1 missing:
`roy2026uq` is marked missing because the UAI 2026 PMLR volume is not indexed
by OpenAlex; it is verified manually against the PMLR page and the arXiv
preprint (see below). The two near matches are explained by record shape
(`zhu2021`: Crossref author fields split across lines; `vdvwellner1996`: the
Crossref record omits the book's subtitle).

## Per-entry evidence

| key | cited as | verification |
|---|---|---|
| roy2026uq | UAI 2026, PMLR 337:5845-5865 | PMLR v337 page (title, authors, venue, pages) + arXiv 2304.13950 |
| roy2023uq | arXiv:2304.13950 (2023) | arXiv API; title matches v1 exactly |
| cherian2023 | JMLR 25(149):1-49, 2024 | JMLR v25 listing; arXiv 2305.03712; ACM DL |
| maity2021 | ICLR 2021 | DataCite (arXiv DOI), arXiv 2103.16714 |
| fang2018 | JMLR 19(78):1-21, 2018 | JMLR v19 listing (pages corrected from 1-30) |
| chen2016 | Ann. Statist. 48(1):251-273, 2020 | Crossref 10.1214/18-AOS1801 (number/pages corrected from 5 and 2513-2540) |
| zhu2021 | JASA 118(541):393-404, 2023 | Crossref 10.1080/01621459.2021.1933498 (issue year 2023; online 2021) |
| polyak1992 | SIAM J. Control Optim. 30(4):838-855, 1992 | Crossref 10.1137/0330046 |
| duchi2016 | Ann. Statist. 49(1):21-48, 2021 | Crossref 10.1214/19-AOS1831 |
| ramprasad2023 | JASA 118(544):2901-2914, 2023 | Crossref 10.1080/01621459.2022.2096620 (online 2022; issue 2023) |
| hardt2016 | NeurIPS 2016 | arXiv 1610.02413 |
| zafar2019 | JMLR 20(75):1-42, 2019 | JMLR v20 listing |
| diciccio2020 | KDD 2020, 1467-1477 | Crossref 10.1145/3394486.3403199 |
| taskesen2021 | FAccT 2021, 648-665 | Crossref 10.1145/3442188.3445927 |
| rosenblatt2024 | arXiv:2410.02005 | DataCite (arXiv DOI) |
| ding2021 | NeurIPS 34, 6478-6490, 2021 | arXiv 2108.04884 (proceedings pagination follows the arXiv note) |
| corbett2017 | KDD 2017, 797-806 | Crossref 10.1145/3097983.3098095 |
| vdvwellner1996 | Springer, 1996 | Crossref 10.1007/978-1-4757-2545-2 |

## Removed entry

`moreau2024` (Moreau & Weber, "Quantifying Algorithmic Fairness: A Novel
Perspective Through Uncertainty Estimation", *European Journal of Emerging
Artificial Intelligence* 1(1):96-112, ISSN 3087-4602) could not be verified:

- no Crossref work matches the title, and `filter=issn:3087-4602` returns 0 works;
- the journal title does not appear in the Crossref journal registry (the ISSN
  lookup returns HTTP 404);
- the arXiv API returns no paper with this title, and DataCite has no record;
- the ISSN portal page for 3087-4602 is behind a bot challenge, so the ISSN
  itself could not be confirmed either.

Per the protocol's grey-zone rule (unconfirmable means unused) the entry was
deleted, together with the sentence it supported in Section 2. Disclosure: the
entry had been in `refs.bib` since the first v1.0 commit and was carried through
earlier checks without independent verification; removing it is a correction,
not a change of the argument, since the surrounding paragraph keeps its
verified citations.

## Quote-level review

Each citation was read against the sentence it supports. One over-attribution
was fixed: Section 2 described `fang2018`, `chen2016`, `zhu2021` as "online
bootstrap and batch-means procedures"; `chen2016` and `zhu2021` develop online
covariance/random-scaling inference rather than batch means, so the sentence now
reads "online bootstrap and online covariance procedures". The remaining
attributions were checked sentence by sentence (permutation tests
[diciccio2020], optimal-transport projections [taskesen2021], individual-fairness
tests [maity2021], bootstrap audits [cherian2023], uncertainty benchmarks inside
fair predictors [rosenblatt2024], averaging [polyak1992], constrained variants
[duchi2016], policy evaluation [ramprasad2023], fairness background
[hardt2016, zafar2019, corbett2017, ding2021]).

## Limitations

OpenAlex was rate-limited throughout (HTTP 429, no API key available), so
verification relied on Crossref, DataCite, the arXiv API, the JMLR/PMLR volume
listings and the publisher PDFs. Paywalled full texts were not consulted for
bibliographic details; only metadata and the cited-paper abstracts were used.
The three "reviewer perspectives" of the deep-research skill were not run as
isolated sub-agents because the sub-agent product failed in this session
(recorded earlier in this project); the audit is a single-context fact-check.
