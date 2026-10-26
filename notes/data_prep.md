# 数据准备说明（data-prep）

任务：按 `SPEC.md` §6、§9 为复现准备 Adult / COMPAS / ACSIncome 三个数据集。产出在 `data/processed/`
（`.npz` + 同名 `.json` + `MANIFEST.md`），生成脚本在 `code/data_prep/`（绝对路径常量、确定性、可重跑），
质量检查 `code/data_prep/99_qa.py` 全部 PASS。**未安装任何新包**；原始数据目录只读、未改动。

## 总览

| 数据集 | 用途 | 生成脚本 | n | p | 阳性率 | 敏感属性 z | 组样本（z=0 / z=1） | 与论文口径 |
|---|---|---|---|---|---|---|---|---|
| Adult | DI | `01_adult.py` | 30,162 | 95 | 0.248922 | sex：Female=0，Male=1 | 9,782 / 20,380 | 13 特征一致；n 论文未给 |
| COMPAS | DM | `02_compas.py` | 5,278 | 5 | 0.470443 | race：Caucasian=0，African-American=1 | 2,103 / 3,175 | n/p/敏感属性完全一致 |
| ACSIncome | DI | `03_acsincome.py` | 1,664,500 | 10 | 0.368920 | SEX：Female（2）=0，Male（1）=1 | 797,765 / 866,735 | **n/p 精确一致**（逐行核验） |

`.npz` keys 恒为 `X`（float64, n×p）、`y`（int8, ±1）、`z`（int8, 0/1）；JSON 有 `feature_names/sensitive_name/n/p/positive_rate/group_sizes/source`
及 `feature_mean/feature_std`（便于下游 z-score）。所有数据**未做实验划分、未标准化**；$D',\tilde D,W_k$ 由 Lead 的 `code/core/` 按 SPEC §6 抽取。

## 1. Adult（DI）
- **来源**：本地只读 `fairness_unawareness\data\raw\adult.data`（UCI Adult 官方训练集，32,561 行；
  `adult.test` 本地副本被截断——9,216 条完整记录后文件在行中间断开，故**未合并**，见 `adult.json.adult_test_note`）。
- **特征清单**：13 个原始属性（去掉 `fnlwgt`、`income`），按 UCI 顺序：
  `age, workclass, education, education-num, marital-status, occupation, relationship, race, sex, capital-gain, capital-loss, hours-per-week, native-country`。
  预处理：删 `'?'` 缺失行（2,399）→ n=30,162；8 个类别属性 one-hot（`drop_first=True`，首水平被截距吸收），
  5 个数值属性保留原值 → **p=95** = 5 连续 + 90 哑变量（6+15+6+13+5+4+1+40）。精确 95 个名字见 `adult.json.feature_names`。
- **标签**：`income == '>50K'` → y=+1，否则 −1。**敏感属性**：`sex=='Male'` → z=1，Female → z=0（`sex_Male` 哑变量与 z 相同）。
- **与论文不一致处**：① 论文只说"13 features、sex 敏感"，未给 n/编码/标准化；本数据 n=30,162 = UCI 训练集删缺失（Zafar 等常用口径），
  未用完整 48,842（train+test）版本（本地 test 截断）。② p=95 是 one-hot 后维度，论文的"13"是原始属性数；
  上游 Lead 消息里的 "108" 有误，**真实 p=95（X.shape=(30162,95)，d=p+1=96）**。③ 无标准化（按任务要求保留原值）。
- **建议下游用法**：D' 的约束直接吃全部 95 列；因 `capital-gain/loss` 量级 $10^4$–$10^5$ 会主导 $\tilde x$，**先按列 z-score**
  （JSON 有 mean/std），否则 $\epsilon=10^{-5}$ 与论文不可比。若不想让 sex 进特征，core 可删 `sex_Male` 一列（p=94），但论文口径默认保留。

## 2. COMPAS（DM）
- **来源**：本地只读 `fairness_unawareness\data\raw\compas.csv`（ProPublica compas-scores-two-years，7,214 行）。
- **预处理（复现 Zafar et al. 2019 / 论文 5,278 人）**：`-30≤days_b_screening_arrest≤30`（→6,172）→ `is_recid!=-1` →
  `c_charge_degree!='O'` → `score_text!='N/A'`（此文件均无变化）→ `race ∈ {African-American, Caucasian}` → **n=5,278**。
  仅前 4 个过滤得 6,172，原论文的 5,278 必须再限定两族（精确命中）。
- **特征清单（5，按论文顺序）**：`sex`（Male=1/Female=0）、`age`（原值）、`race`（African-American=1/Caucasian=0，与 z 相同）、
  `priors_count`（原值）、`c_charge_degree`（F=1/M=0）。**标签**：`two_year_recid==1` → y=+1，否则 −1。
  **敏感属性 z 写死**：`race=='African-American'` → 1；`race=='Caucasian'` → 0（两族限定后即"其余=0"）。
- **与论文不一致处**：① 论文未说 race 二值化方向（AA=1 vs Caucasian=1）；本数据 AA=1，只影响 $\Delta_{DM}$ 符号、不影响 $|\Delta_{DM}|$。
  ② 论文未说编码/标准化；本数据 age/priors_count 原值。③ 官方"5 特征"里含 race（=敏感属性列），本数据保留。
- **建议下游用法**：z 直接用现成列；建议对 `age/priors_count` z-score 以贴近论文 $R^2=300$ 的有效尺度。

## 3. ACSIncome（DI）
- **来源**：Census 官方 2018 1-Year ACS PUMS person 文件：全国 `csv_pus.zip`（两个分卷 `psam_pusa/b.csv`）+ 波多黎各 `csv_ppr.zip`；
  缓存在 `data/raw/acs_pums/2018/1-Year/`。官方基准快照：OpenML dataset 43141（Ding et al. 2021）。
- **预处理（= folktables.ACSIncome / Ding et al.）**：流式读取 13 列（原始 3,242,656 条 person 记录）→
  `AGEP>16`（2,627,069）→ `PINCP>100`（2,343,495）→ `WKHP>0`（1,668,687）→ `PWGTP>=1`（1,668,687）→
  **剔除 DC（ST=11，4,187 行）** → **n=1,664,500**。剔除 DC 是因为 Ding et al./folktables 的 state_list = 50 州+PR、不含 DC；
  剔除后与 OpenML 43141 快照**逐行完全一致（X、y、ST 全部 array_equal）**，WY 另与 folktables 逐元素一致。
- **特征清单（10，Ding et al./folktables 顺序，PUMS 原始编码，未 one-hot）**：
  `AGEP, COW, SCHL, MAR, OCCP, POBP, RELP, WKHP, SEX, RAC1P`。**标签**：`PINCP>50000` → y=+1，否则 −1。
  **敏感属性**：`SEX==1`（Male）→ z=1，`SEX==2`（Female）→ z=0；`SEX` 同时也是 10 特征之一。
- **与论文不一致处**：① 论文未说特征是否 one-hot/标准化；本数据保留 folktables 原生原始编码（与 Ding et al. 发布表示一致、n 精确）。
  ② 获取路径用"官方全国分卷 + PR"代替 folktables 52 州逐个下载（数据等价、已双重校验），详见 `MANIFEST.md` §3。
- **建议下游用法**：10 列直接用（建议先 z-score，JSON 有 mean/std）；**不要**对 OCCP/POBP 另做 one-hot（p>1000 且偏离基准表示）。

## 复跑与验收
```powershell
python code/data_prep/01_adult.py
python code/data_prep/02_compas.py
python code/data_prep/03_acsincome.py   # 首次需下载 ~568MB（缓存于 data/raw/acs_pums/）
python code/data_prep/99_qa.py          # 三数据集全部 PASS
```
- 三脚本无随机操作（`seed=20261026` 仅记录），重跑数组逐位相同；原始数据目录未改。
- 数据划分/标准化不在本阶段做，见 `MANIFEST.md` §5"下游实验建议"。
- **blocker**：无。已知风险点：Adult 未合并完整 test 集（本地副本截断）；三个数据集均未标准化，$\epsilon$/R² 尺度需 Lead 在 core 决定是否 z-score。
