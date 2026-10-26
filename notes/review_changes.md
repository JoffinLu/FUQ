# 论文自审与修订记录（Round 17，2026-10-27）

**方法**：按 `academic-paper-reviewer`（五视角：Journal-Fit / Methodology / Domain / Perspective /
Devil's Advocate，角色分离、先独立判断后综合）、`academic-paper`（写作规范与完整性声明）和
`deep-research`（不编造文献/证据，灰区即 FAIL）的要求，对 TEST 投稿版正文做投稿前自审。
原计划由独立子代理执行五席评审，子代理两次失败后由 Lead 接手完成。

## 发现（CRITICAL / MAJOR）

| # | 级别 | 问题 | 修改 |
|---|---|---|---|
| C1 | CRITICAL | 摘要、贡献、结论称联合 bootstrap“重抽样全部三类来源”，但 Table 2/3 与 `real_joint_ci.py`、`ablation_sources.py` 实验只重抽样训练轨迹与评估集；第三项（约束集）从未在覆盖实验中验证。审稿人一查实验代码即可发现过度声明。 | 摘要改为“two-source joint bootstrap（固定审计设计）+ 设计随机时的 constraint-set layer”；贡献 2 同改；结论改为“resampling the training trajectories and the evaluation set, with a constraint-set layer for audits whose design is itself random”。 |
| C2 | MAJOR | Theorem 2 的“coverage at least 1−α”在约束集固定时加入了无必要的第三项，表述与其证明不匹配；严格说第三项对“固定目标”是保守化而非必需。 | 定理改为两种情形：固定设计（third term omitted）渐近覆盖 1−α；随机设计时对“已实现设计的目标”保守（第三项均值零、与另两项渐近独立）。 |
| C3 | MAJOR | Theorem 1 / Lemma 1 未声明“条件于已实现的约束集 D′”；若 D′ 随机，θ\* 本身随机，误差分解含义不同。 | 分解节标题改为 “Decomposition: two error sources and a design component”，Assumption 后加一节说明“本节所有结论条件于 D′，D′ 的随机性通过目标 θ\* 进入，见 §Experiments 的 variance budget”；Theorem 1 加 “conditionally on D′”。 |
| C4 | MAJOR | Table 4 的“variance of the reported gap”表述不准确：se(D′) 衡量的是目标漂移（设计敏感性），不是估计量的推断不确定性。 | §Variance budget 与 Table 4 caption 重写为“三类变异性：两个误差分量 + 一个设计分量”；补充材料 S4 增加一段文字（表前）解释该区分以及均值/符号比较列；消融段与 Limitations 已与之一致。 |
| C5 | MINOR | Related work “adds the two missing sources of randomness”与 C1 同步失配。 | 改为“adds the evaluation component on top of the training-side theory and treats the constraint-set (design) component separately”。 |
| C6 | MINOR | Table 2 caption 未说明约束集固定，读者可能以为 joint 含第三项。 | caption 加 “and a fixed constraint set (two-source joint interval)”；实验 Setup 段加同样说明。 |

## 已确认无问题（抽查）

- 数字一致性：`check_numbers.py` 123 个数字串，missing 0（修订未新增数字）。
- 参考文献：18 条，全部被引用，无缺 DOI；未新增任何未核实文献（遵循 deep-research 完整性规则）。
- 风格：正文 6 处 em-dash、无 AI-tone 高频词（crucial/leverage/delve 等为 0）。
- 复现证据链：Table 1/2/3/4、supplement S1–S9、`notes/reproducibility_verification.md` 的逐值重跑结论不变。
- 声明完整：Data/Code availability、Funding、Competing interests、Ethics、Consent、AI 使用声明（英文润色）齐备。

## 修订后状态

- `main.tex` 已改（18 处替换）；`main_test.tex` 由 `code/build_test_tex.py` 重新生成。
- 页数：`main.pdf` 16 页；`main_test.pdf` **18 页**（+1 页，内容增长）；`supplement.pdf` 6 页。
- 编译：main exit 0（0 overfull/0 undefined）；main_test exit 0（附录 2 处 overfull 16.9pt/34.2pt，可接受）；supplement exit 0（仅 1 处 3.17pt overfull）。
- `check_package.py`：**13/13 PASS**（main 16、main_test 18、supplement 6、7 表 4 图、123 数字、18 refs、S1–S9、submission 24 entries、release 163 文件、reviewer 16 页、combined 22 页）。
- 投稿包 `fuq-fairness_submission_v2.0.zip` 重建（727 KB / 24 entries，自包含三份 PDF 均编译 exit 0）；发布包重建（165 文件 / 1.57 MB）。

## 已知残留（不阻塞投稿）

1. TEST 官方模板下附录 2 个公式 overfull（16.9pt / 34.2pt），属 sn-jnl 版心较窄所致，可接受。
2. 补充材料 1 处 3.17pt overfull（S7 核验表表头），视觉不可见。
3. 正式投稿前需在 ScholarOne 门户复核页数与官方分区表；审稿人邮箱、仓库 URL/Zenodo DOI 仍待补。

## Round 18 — paper-writer audit (`notes/paper_writer_audit.md`)

Second pass under the `paper-writer` skill, focused on evidence traceability and writing
discipline. 20 changes to `main.tex` and one bibliography entry (`vdvwellner1996`, book,
DOI verified via Crossref):

- CRITICAL: abstract/contribution 2/conclusion now describe a two-source construction for a
  fixed audit design, with the constraint-set layer as an optional extension; the
  experiments are labelled consistently (previously "all three sources" was claimed).
- MAJOR: evaluation/training noise ratio corrected 3.9 -> 4.6 (Table 4); "orders of
  magnitude" -> "two to three orders" ((m/T)/(v^2/sigma_D^2) = 0.0004-0.004); Theorem 2's
  `S -> infinity` condition stated; "exact coverage" -> "closed-form asymptotic coverage".
- MAJOR/MINOR: quantified the synthetic-generator degeneracy (corr(z, y) = 0.828,
  attribute-only label accuracy 0.909; recorded in `notes/repro_report.md`), corrected the
  Figure 2 mechanism claim, removed a non-existent DM sensitivity analysis, corrected the
  data-availability pointer, and made the AI-use statement truthful.
- Verification: `check_numbers.py` 123/0; `check_refs.py` 19 entries (16 exact, 2 near
  with documented reasons, 1 by-design missing with note); `main.pdf` 16 pages;
  `main_test.pdf` 18 pages.
