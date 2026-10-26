"""Round 16 docs rewrite: retarget to TEST (Springer, CAS Q3), GitHub repo files."""
from pathlib import Path

ROOT = Path(".")
SUB = ROOT / "manuscript" / "submission"

# ---------------------------------------------------------------- target_journals.md
(SUB / "target_journals.md").write_text(
    """# 目标期刊匹配（中科院 2025 三区口径；2026-10-27 决策版）

> 口径：用户要求**中科院分区三区**（2026-10-27 确认）。分区数据为第三方聚合的 2025 年中科院
> 期刊分区表（检索日 2026-10-27）；**投稿前必须以中国科学院文献情报中心《期刊分区表》官方平台
> 或学校图书馆版本复核**。本文档记录匹配与“录用率优先”理由，不构成分区承诺。

## 首选：TEST — *TEST*（Springer）

- **分区与指标（2026-10-27 检索）**：**中科院 2025 版 3 区（基础版 3 区 / 新锐 3 区）**；
  SCIE；JCR **Q2**（STATISTICS & PROBABILITY，排名 69/170）；IF **1.5**、5 年 IF 1.7、JCI 0.65；
  ISSN 1133-0686 / eISSN 1863-8260；Springer 出版。
- **why TEST（录用率优先 + 匹配）**：
  1. **口径满足**：中科院三区（基础版 3 区）；JCR Q2 同区间，官方分区表复核即可。
  2. **scope 匹配**：TEST 接收“统计方法学”论文——理论贡献 + 模拟实验 + 真实数据应用。
     本文正是：三源方差分解（理论）、解析覆盖率与联合 bootstrap（理论/方法）、5 组合成+3 组真实
     数据实验、审计预算建议（应用）；方法学贡献与实证证据的比例符合 TEST 的惯例。
  3. **录用难度相对低**：LetPub 作者自报竞争性 “Easy”（投稿量适中、3 期/年、每期约 12 篇文章，
     编辑部反馈快）；相较高区期刊更看重“贡献清晰、结论可靠、可复现”，本文这三项都是强项。
  4. **官方模板可得**：Springer 统一使用 Springer Nature LaTeX 模板（sn-jnl v2.1），已下载并
     完成转换（见 `test_format_notes.md`）；电子补充材料（supplement）受支持。
- **篇幅/格式**：单栏 17 页（7 表 4 图 + 附录 A 证明 + 附录 B 复现细节），补充材料 6 页
  （表 S1–S9）；TEST 对篇幅较宽松（无硬性 20 页限制），补充材料可长。
- **投稿系统**：Springer 期刊统一投稿门户（Editorial Manager / Springer Nature）。
- **审稿周期**：按 3–6 个月规划（TEST 平均审稿周期约 2–3 个月，编辑处理较快）。
- **风险**：TEST 偏好“统计方法学”而非“计算算法”；cover letter 与摘要已按“方法学+应用”定位
  表述（三源分解 → 区间覆盖率 → 审计实践），并把纯计算/工程细节放补充材料。

## 备选（均为中科院 2025 三区）

1. **COAP — Computational Optimization and Applications**（Springer）：中科院 2025 基础版 3 区
   （新锐 2 区）；JCR Q1，IF 2.5。匹配点：约束 SDA/投影算子/乘子法的算法视角；需改写为优化算法
   导向（算法 1 收敛与投影实现、bootstrap 作为在线方差估计），压缩统计推断篇幅。
2. **DMKD — Data Mining and Knowledge Discovery**（Springer）：中科院 2025 3 区；JCR Q1，
   IF 5.5，CCF B。匹配点：公平性审计作为 ML 应用；需突出“审计协议设计与评估数据预算”。
3. **JCGS — Journal of Computational and Graphical Statistics**（T&F/ASA）：中科院 2025 数学 3 区
   （小类统计学与概率论 3 区）；JCR Q2，IF 1.6。计算统计视角匹配，但审稿人更看重算法新颖性，
   录用难度高于 TEST。

## 进阶目标（高于三区要求，若希望冲 2 区）

- **Statistics and Computing**（Springer）：中科院 2025 2 区、JCR Q2、IF 1.8。scope 与本文
  （计算统计、bootstrap、优化）高度契合；可作为“先投更高”的一投目标（需用户决定）。

## 不采用

- **Journal of Applied Statistics**：JCR Q3 但中科院 **数学 4 区**，不满足三区口径。
- **Knowledge and Information Systems（KAIS）**：中科院 **计算机科学 4 区**。
- 纯 ML 会议（NeurIPS/ICML/UAI）：不符合期刊发表要求。

## 投稿策略

1. 首选 **TEST**（分区满足、scope 匹配、录用难度相对低、官方模板与补充材料机制成熟）。
2. 若被拒：按审稿意见改投 **COAP**（优化算法视角）或 **DMKD**（ML 应用视角）；若理论加强后
   可冲 **Statistics and Computing**。
3. 所有版本共用同一代码仓库（GitHub）与结果文件，保证可复现声明一致。

## 证据来源（2026-10-27 检索）

- TEST 分区/指标：<https://ai4paper.pro/journal/test/>（中科院 3 区 / 基础版 3 区；JCR Q2；IF 1.5；
  排名 69/170；Springer）
- TEST 竞争性（作者自报 Easy/Slow 等）：letpub.jp 期刊页 <https://www.letpub.jp/index.php?page=journalapp&view=detail&journalid=7970>
- TEST 引文格式（作者-年份）：<https://cdn.paperpile.com/s/test-citation-style/>
- Springer Nature LaTeX 模板（官方）：<https://www.overleaf.com/latex/templates/springer-nature-latex-template/myxmhdsbzkyd>
  （本地镜像 v2.1 April 2023：`tools/sn-jnl/`；`sn-jnl.cls` + `sn-basic.bst`）
- JCGS / COAP / DMKD / Statistics and Computing 分区：ai4paper 期刊页（见上一版记录）
""",
    encoding="utf-8",
)

# ---------------------------------------------------------------- test_format_notes.md
(SUB / "test_format_notes.md").write_text(
    """# TEST（Springer）格式笔记与官方模板说明

> 目标期刊 *TEST*（Springer，ISSN 1133-0686）。Springer 期刊统一使用 **Springer Nature LaTeX
> Template v2.1 (April 2023, `sn-jnl.cls`)**；TEST 的参考文献采用 **Springer Basic 风格
> （作者-年份）** —— 依据 Paperpile TEST 引文样式页：正文引作 “(Roy and Mohapatra 2026)”，
> 文末按字母序排列。因此类选项用 `[sn-basic]`、参考文献样式用 `sn-basic.bst`。

## 1. 官方模板来源（本地已保存）

- 官方 Overleaf 模板页：<https://www.overleaf.com/latex/templates/springer-nature-latex-template/myxmhdsbzkyd>
- 本地镜像（v2.1 April 2023，与官方一致）：`tools/sn-jnl/`（`sn-jnl.cls`、`sn-article.tex`、
  `sn-basic.bst`、`user-manual.pdf`、`README.md`）
- 投稿包中附带 `manuscript/sn-jnl.cls` 与 `manuscript/sn-basic.bst`，保证审稿人能直接编译。

## 2. 生成与编译

```powershell
python code/build_test_tex.py           # main.tex → manuscript/main_test.tex
cd manuscript
..\\..\\tools\\tectonic\\tectonic.exe -X compile main_test.tex
```

- 类选项：`\\documentclass[pdflatex,sn-basic]{sn-jnl}`。**注意**：`pdflatex` 选项在模板中
  仅用于跳过 `breakurl` 宏包（该宏包的 dvips specials 依赖 `\\headerps@out`，在 XeTeX/Tectonic
  下会报 Undefined control sequence）。文献 URL 仍由 hyperref 正常链接，仅失去 URL 自动断行；
  在 pdfLaTeX 下提交时该选项同样安全。
- 前置宏包：`graphicx, multirow, amsmath/amssymb/amsthm/mathtools, booktabs, xcolor,
  textcomp, manyfoot`（`manyfoot` 是模板自身 `\\AtBeginDocument` 中 `\\SetFootnoteHook` 所需）。
- 作者块用模板命令：`\\author*[1]{\\fnm{Cenfa} \\sur{Lu}}\\email{...}`、
  `\\affil*[1]{\\orgdiv{...},\\orgname{...},\\orgaddress{...}}`；`\\abstract{...}`、`\\keywords{...}`、
  `\\maketitle`。
- 后置部分：正文 `\\section*{Declarations}`（Springer 标准声明区），条目用 `\\bmhead{...}`：
  Data availability、Code availability、Funding、Competing interests、Ethics approval、
  Consent to participate、Consent for publication、Authors' contributions、Acknowledgements、
  Use of AI tools。生成脚本自动把 `main.tex` 里的 `\\paragraph{...}` 声明转为 `\\bmhead{...}`。

## 3. 当前编译状态（2026-10-27）

- `manuscript/main_test.pdf`：**17 页**，7 表 4 图，0 undefined reference，2 处 overfull hbox
  （附录 A 证明中的长公式，16.9pt / 34.2pt；可接受，排版时由编辑部微调）。
- `manuscript/main.pdf`（通用版）：16 页，作为内容对照版保留。
- 补充材料：`manuscript/supplement.pdf`（独立 `article` 版，6 页，表 S1–S9）；Springer 接受
  electronic supplementary material，投稿时单独上传（PDF + 源文件）。

## 4. 投稿包清单（TEST 版）

`manuscript/main_test.tex`、`main_test.pdf`、`sn-jnl.cls`、`sn-basic.bst`、`refs.bib`、
`supplement.pdf/tex`、`results/figures/*.pdf`（4 张）、`submission/{cover_letter,title_page,
checklist,target_journals,test_format_notes}.md`。审稿系统要求上传 PDF 时用 `main_test.pdf`；
若要求可编辑源文件，上传 `main_test.tex + refs.bib + sn-jnl.cls + sn-basic.bst + figures/`。

## 5. 门户核对项（官方 INSTRUCTIONS FOR AUTHORS 页面被 Cloudflare/登录墙拦截，
> 提交前必须在 Springer 投稿门户中逐项确认；以下为 Springer 期刊通用要求）

- [ ] 摘要词数上限（Springer 常见 150–250 词；当前摘要 223 词）
- [ ] 关键词数量（当前 5 个）
- [ ] Declarations 各项是否齐全（已按模板列表写全）
- [ ] 是否要求 Highlights / graphical abstract（TEST 通常不需要）
- [ ] 是否允许单栏 article 版式（sn-jnl 默认单栏，符合）
- [ ] 电子补充材料上传方式（PDF 与源文件）
- [ ] ORCID 与通讯作者邮箱在系统中填写（当前作者块已含）
""",
    encoding="utf-8",
)

# ---------------------------------------------------------------- cover_letter.md
(SUB / "cover_letter.md").write_text(
    """# Cover letter

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
""",
    encoding="utf-8",
)

# ---------------------------------------------------------------- title_page.md
(SUB / "title_page.md").write_text(
    """# Title page

**Journal:** *TEST* (Springer) — primary target venue (CAS 2025 Q3); alternatives in
`target_journals.md`.
**Manuscript type:** Original research article.
**Template:** Springer Nature LaTeX template v2.1 (`sn-jnl.cls`, class option `sn-basic`).

## Title

Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification

## Short running head

Three Noise Sources in Fairness Audits (≤ 40 characters)

## Authors

| # | Name | Affiliation | ORCID |
|---|------|-------------|-------|
| 1 | Cenfa Lu (corresponding author) | School of Mathematics and Computational Science, Guilin University of Electronic Technology | 0009-0003-3481-3624 |

**Affiliation.** School of Mathematics and Computational Science, Guilin University of Electronic
Technology, Guilin 541004, China.

## Corresponding author

Cenfa Lu, School of Mathematics and Computational Science, Guilin University of Electronic Technology,
Guilin 541004, China. E-mail: joffin@163.com. ORCID: <https://orcid.org/0009-0003-3481-3624>.

## Abstract

As in `main_test.tex` — 223 words. It states: (i) the training-noise-only interval of Roy and
Mohapatra (2026); (ii) the exact rate at which its coverage degrades in the ratio of training to
evaluation error; (iii) the three-source decomposition (training, evaluation, constraint set);
(iv) the joint bootstrap that restores nominal coverage; (v) three real datasets where training noise
is a small fraction of the total uncertainty.

## Keywords

fairness auditing; uncertainty quantification; constrained stochastic optimization; online bootstrap;
distribution-free inference

## Word count

Approximate main text: **4,700 words** (abstract through conclusion, excluding references, appendix,
tables and figure captions; measured from the 17-page TEST-format PDF).

## Suggested reviewers (optional)

Provide 3–5 names in the submission system (not in the manuscript). Candidate pool with rationale and
conflict notes: `notes/referee_prep.md` §建议审稿人 — Jad Salem (Ecole Polytechnique), Linjun Zhang
(Rutgers), Nathan Kallus (Cornell), Krishnaram Kenthapadi (Amazon), Harvineet Singh (Amazon). E-mail
addresses must be verified by the author before submission; avoid suggesting the authors of the
baseline (Roy and Mohapatra).

## Declarations

The Declarations section is included in the manuscript (Data availability, Code availability, Funding,
Competing interests, Ethics approval, Consent to participate, Consent for publication, Authors'
contributions, Acknowledgements, Use of AI tools).
""",
    encoding="utf-8",
)

# remove stale JCGS notes
jcgs = SUB / "jcgs_format_notes.md"
if jcgs.exists():
    jcgs.unlink()

print("wrote target_journals.md, test_format_notes.md, cover_letter.md, title_page.md; removed jcgs_format_notes.md")
