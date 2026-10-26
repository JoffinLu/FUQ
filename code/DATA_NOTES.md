# Data notes

The release does **not** redistribute the datasets. The preprocessing scripts read raw files from `data/raw/` (override with the `FUQ_RAW_DIR`
environment variable); the ACSIncome files are downloaded into `data/raw/acs_pums` on first use.
Every reported split is regenerated deterministically by `code/data_prep/00_all.py` (which runs
`01_adult.py`, `02_compas.py` and `03_acsincome.py`; see `notes/data_prep.md`).

| file | source | license / terms |
|---|---|---|
| `adult.data`, `adult.test` | UCI Machine Learning Repository, Adult (Census Income), https://archive.ics.uci.edu/dataset/2/adult | CC BY 4.0 (UCI terms); no redistribution issue for derived statistics |
| `compas.csv` | ProPublica COMPAS analysis, https://github.com/propublica/compas-analysis | no explicit license stated upstream; used here for research reproduction only |
| `acs_income/` (folktables ACS PUMS 2018, 1-Year, task `ACSIncome`) | folktables, https://github.com/socialfoundations/folktables | PUMS microdata from the U.S. Census Bureau; follow Census terms of use |

> The UCI Adult *test* split is not merged: our local copy is truncated, and the canonical
> training split (`adult.data`, 32,561 rows; 30,162 after dropping missing values) is the standard
> Zafar et al. pool.  This is documented in `data/processed/MANIFEST.md`.

## Preprocessing summary

* **Adult** (DI): `sex` (Male=1) as sensitive attribute, binary label from `income`; records with
  missing values dropped (30,162 rows); features z-scored on the training pool; 96 features after
  one-hot encoding.
* **COMPAS** (DM): `race` (African-American=1) as sensitive attribute, binary label `two_year_recid`;
  the five features listed in the paper; z-scored.
* **ACSIncome** (DI): `SEX` (Male=1), label `PINCP > 50,000`; the ten folktables features, z-scored;
  1,664,500 rows.

The z-score means/stds and the train/constraint/held-out splits are computed on the training pool
only and are fixed across all repetitions, exactly as in the original simulation study
(`notes/repro_report.md`, deviations table).
