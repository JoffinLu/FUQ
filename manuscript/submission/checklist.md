# 投稿检查清单（TEST / Springer 版）

> 目标期刊：*TEST*（Springer，ISSN 1133-0686）；中科院 2025 版 **3 区**（SCIE、JCR Q2）。
> 目标：一次通过编辑部格式初审，减少因技术原因退修。逐项打勾后提交。

## 技术项（提交前必须全部打勾）

- [x] 目标期刊分区核实（2026-10-27）：TEST = 中科院 2025 基础版 3 区（来源 `target_journals.md`；官方分区表提交前复核）
- [x] 官方模板套用：Springer Nature LaTeX Template v2.1（`sn-jnl.cls`，选项 `pdflatex,sn-basic`）
- [x] TEST 版正文 `manuscript/main_test.pdf`（**18 页**，7 表 4 图，附录 A 证明 + 附录 B 复现细节，0 undefined reference）
- [x] 通用版 `main.pdf`（16 页，内容对照版，随包提交便于审阅）
- [x] 补充材料 `supplement.pdf`（6 页，表 S1–S9，独立编号）
- [x] 所有图以矢量 PDF 提交（`results/figures/`：repro_synth_di、repro_compas、sample_size、ablation_coverage），正文按 Fig. 1–4 引用
- [x] 数字一致性：`python manuscript/check_numbers.py` → 123 个数字串 missing 0
- [x] 参考文献：18 条全部被引用、存在性与 DOI 核对（`refs_checked.json`）；作者-年份格式（sn-basic）
- [x] 包一致性：`python manuscript/check_package.py` → **13/13 PASS**
- [x] 三版 PDF 自包含编译验证（submission zip 解压后 main/main_test/supplement 均 exit 0）
- [x] 摘要约 235 词；关键词 5 个；短标题 ≤40 字符
- [x] Statements → Springer Declarations 全项：Data availability、Code availability、Funding、
      Competing interests、Ethics approval、Consent to participate、Consent for publication、
      Authors' contributions、Acknowledgements、Use of AI tools

## 作者信息

- [x] `main.tex` / `main_test.tex` 作者块：**Cenfa Lu**（第一作者）、**Shuda Wu**（通讯作者）、**Xun Liu**
      School of Mathematics and Computing Science,
      Guilin University of Electronic Technology, Guilin 541004, China
- [x] 邮箱 joffin@163.com / shudawu777@163.com / liuxun0817@163.com；ORCID 0009-0003-3481-3624 / 0009-0003-2590-9608 / 0009-0005-4230-3047（`main_test.tex` 中 `\author*[1]{...}` 标记通讯作者 Shuda Wu + 三个 `\email{}`）
- [x] Title page（`submission/title_page.md`）：标题、短标题、作者、单位、ORCID、通讯作者

## 稿件文档

- [x] Cover letter（`submission/cover_letter.md`，含 TEST 定位、三源贡献、AI 使用声明、5 位建议审稿人）
- [x] 目标期刊匹配与备选（`submission/target_journals.md`：TEST → COAP → DMKD；Statistics and Computing 进阶）
- [x] TEST 格式笔记与门户核对项（`submission/test_format_notes.md`）
- [x] AI 使用声明（正文 Declarations：AI 协助实现与运行数值实验、起草与润色文字；所有结果均对照代码与输出复核，作者对内容负责）

## 数据与代码

- [x] Data availability 声明（公开基准数据 Adult/COMPAS/ACSIncome，来源与预处理见补充材料 S1 与 `notes/data_prep.md`）
- [x] Code availability 声明（开源仓库 GitHub，接收后补 Zenodo DOI）
- [x] GitHub 仓库 <https://github.com/JoffinLu/FUQ> 已推送（master），正文 Data/Code availability 与 cover letter 已含链接

## 提交系统

- [x] 投稿包 zip v2.0 构建完成（`submission/fuq-fairness_submission_v2.0.zip`，25 entries，约 1.11 MB）

## 内部复核

- [x] 包一致性 `check_package.py` 13/13 PASS
- [x] 复现结果与稿件数字逐值核对（`check_numbers.py`）
- [x] 通读 TEST 版 PDF 并逐项核对（页数、标题/作者/ORCID/通讯作者、图 4 张、表 7 张、引用编号无 ??、声明与 AI 披露）
- [x] 投稿交接单（`notes/submission_handoff.md`）更新到 v2.0

## 投稿前作者操作（门户内完成，不计入上述完成度）

- 注册/登录 TEST 的 Springer Nature 投稿系统（Editorial Manager / ScholarOne 入口见 `test_format_notes.md`）
- 上传：`main_test.pdf`（正文）、`supplement.pdf`（补充材料）、cover letter、title page
- 上传可编辑源文件：`main_test.tex`、`refs.bib`、`sn-jnl.cls`、`sn-basic.bst`、`results/figures/*.pdf`
- 在系统内关联 ORCID、确认邮箱、填写作者与通讯信息、勾选声明
- 建议审稿人：可不填（已决定不填）；如系统强制必填，再补 3–5 人（候选见 `notes/referee_prep.md`）
- 提交前完成文本查重（全文相似度 <15%，单源 <5%）
- 保存投稿确认邮件与稿号，并写入 `notes/submission_handoff.md`
- Zenodo DOI 为可选项，仓库公开后可生成，接收后回填正文 Code availability
