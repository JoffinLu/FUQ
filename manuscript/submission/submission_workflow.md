# TEST 投稿操作流程（2026-11-02）

> 本文件是投稿当天的操作清单。投稿系统入口与字段以门户实际显示为准；本文件记录已准备好的
> 全部材料、每个文件在系统中的用途，以及唯一还需要作者本人完成的外部事项。

## 0. 一句话状态

论文、补充材料、cover letter、title page、图表源文件、可编辑 LaTeX 源文件、声明与数据分析
结果已全部就绪；`manuscript/submission/fuq-fairness_submission_v2.0.zip` 即完整投稿包
（24 entries）。剩余只有：门户注册/登录、建议审稿人邮箱、以及点击提交。

## 1. 期刊与稿件类型

- 期刊：*TEST*（Springer；ISSN 1133-0686 / 1863-8964）
- 主页（提交入口）：<https://link.springer.com/journal/11749> → “Submit your manuscript”
- 稿件类型：Original research article
- 模板：Springer Nature LaTeX Template v2.1（`sn-jnl.cls`，`sn-basic` 参考文献风格）
- 语言：英文（AI 仅用于语言润色、代码实现与结果复核，已在 Declarations 与 cover letter 披露）

## 2. 提交前 5 分钟核对

| 项 | 值 | 文件/位置 |
|---|---|---|
| 标题 | Separating Training, Evaluation and Constraint-Set Noise in Fairness Uncertainty Quantification | `main_test.tex` |
| 短标题 | Three Noise Sources in Fairness Audits | `title_page.md` |
| 摘要 | 235 词 | `main_test.tex` |
| 关键词 | fairness auditing; uncertainty quantification; constrained stochastic optimization; online bootstrap; distribution-free inference | `main_test.tex` |
| 作者顺序 | Cenfa Lu¹（通讯）、Shuda Wu¹、Xun Liu¹ | `main_test.tex` |
| 单位 | School of Mathematics and Computing Science, Guilin University of Electronic Technology, Guilin 541004, China | `main_test.tex` |
| ORCID | 0009-0003-3481-3624 / 0009-0003-2590-9608 / 0009-0005-4230-3047 | `title_page.md` |
| 通讯邮箱 | joffin@163.com | `main_test.tex` |
| 正文 PDF | `main_test.pdf`，18 页，7 表 4 图 | 投稿包 |
| 补充材料 | `supplement.pdf`，6 页，表 S1–S9 | 投稿包 |
| 数据/代码 | <https://github.com/JoffinLu/FUQ>（MIT） | 正文 Data/Code availability |

## 3. 系统操作步骤

1. **打开门户**：期刊主页（<https://link.springer.com/journal/11749>）→ “Submit your manuscript”。
   首次使用先注册；用通讯作者账号（Cenfa Lu / joffin@163.com）提交。
2. **选择 Article type**：Original Research（若系统写作 “Research article”，选它）。
3. **填写元数据**：标题、摘要（粘贴纯文本）、关键词（逐条输入）、作者（顺序、单位、ORCID）、
   通讯作者、资助信息（选 “no specific funding”）。
4. **上传文件**（按系统分类名对应）：
   - Cover letter：`submission/cover_letter.md` 的内容（贴入文本框；日期已写 2 November 2026，
     若改日提交请同步改日期）。
   - Manuscript（PDF）：`manuscript/main_test.pdf`。
   - Editable source：`main_test.tex`、`refs.bib`、`sn-jnl.cls`、`sn-basic.bst`，以及
     `results/figures/` 下 4 个 PDF（`repro_synth_di`、`repro_compas`、`sample_size`、
     `ablation_coverage`）。`main_test.tex` 用相对路径 `../results/figures/...`，上传 zip 时保留
     `manuscript/` 与 `results/figures/` 两级目录即可直接编译；若系统要求逐个上传图，按此相对
     路径把图放到对应位置。
   - Supplementary material：`supplement.pdf`，并附 `supplement.tex`。
   - Title page：`submission/title_page.md` 的内容，按系统字段填入（作者信息较多时可用上传
     附件方式）。
5. **Declarations**：原创且未一稿多投；全体作者同意；无 competing interests；AI 使用声明
   （照 cover letter 措辞）；数据与代码可得性（GitHub URL）；Ethics 与 Consent 均为 Not
   applicable（公开二手数据）。
6. **建议审稿人（3–5 人）**：Jad Salem（École Polytechnique）、Linjun Zhang（Rutgers）、
   Nathan Kallus（Cornell）、Krishnaram Kenthapadi、Harvineet Singh；提交系统要求填写邮箱，
   请从本人邮箱通讯录/公开主页补全（候选池与回避说明见 `notes/referee_prep.md`）。
7. **检查与提交**：预览系统生成的 PDF（页眉/图表/公式是否完整），确认后提交。保存稿号与
   确认邮件，写回 `notes/submission_handoff.md`。

## 4. 备用与特殊情况

- 若系统要求双盲评审：改用 `main_anonymous.pdf`（16 页，匿名版，不含作者与致谢）。
- 若摘要上限为 200 词：当前 235 词需压缩；优先删去方差预算句与 “often the larger” 从句。
- 若系统只接受 Word：先按 PDF + LaTeX 源文件提交；Word 版需另行转换（未生成）。
- 若补充材料要求单一文件：只传 `supplement.pdf`；源文件按系统提示补充。
- 官方模板与格式说明：`submission/test_format_notes.md`；期刊分区与备选刊：`target_journals.md`。

## 5. 提交后

```text
① 收到稿号（Manuscript ID）→ 记入 notes/submission_handoff.md
② 状态跟踪：Editorial office check → Editor assigned → Under review → Decision
③ 审稿意见返回 → 逐条回复（可用 rebuttal 模板），修改稿 + 回复信 + 干净版/标记版 PDF
④ 录用后 → 校样（proof）、Open Choice 选择、最终 DOI 与 Zenodo 归档
```

## 6. 仍待外部输入（仅 2 项）

1. 建议审稿人的邮箱（3–5 个；姓名已在 cover letter 与 referee_prep 中）。
2. 门户账号与最终点击提交（需作者本人操作）。

（Zenodo DOI 为可选项：仓库已公开，若期刊要求永久 DOI，在 Zenodo 关联 `JoffinLu/FUQ` 后把 DOI
补进 Data availability 并重建投稿包即可。）
