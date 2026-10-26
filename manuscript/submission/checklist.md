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
- [x] 参考文献：18 条全部被引用、DOI 核对（`refs_checked.json`）；作者-年份格式（sn-basic）
- [x] 包一致性：`python manuscript/check_package.py` → **13/13 PASS**
- [x] 三版 PDF 自包含编译验证（submission zip 解压后 main/main_test/supplement 均 exit 0）
- [x] 摘要约 223 词；关键词 5 个；短标题 ≤40 字符
- [x] Statements → Springer Declarations 全项：Data availability、Code availability、Funding、
      Competing interests、Ethics approval、Consent to participate、Consent for publication、
      Authors' contributions、Acknowledgements、Use of AI tools

## 作者信息

- [x] `main.tex` / `main_test.tex` 作者块：**Cenfa Lu**（唯一作者，通讯作者）
      School of Mathematics and Computational Science,
      Guilin University of Electronic Technology, Guilin 541004, China
- [x] 邮箱 joffin@163.com；ORCID <https://orcid.org/0009-0003-3481-3624>（`main_test.tex` 中 `\author*[1]{...}` + `\email{}`）
- [x] Title page（`submission/title_page.md`）：标题、短标题、作者、单位、ORCID、通讯作者
- [ ] 投稿系统内 ORCID 关联与邮箱确认（作者本人操作）

## 稿件文档

- [x] Cover letter（`submission/cover_letter.md`，含 TEST 定位、三源贡献、AI 使用声明、5 位建议审稿人）
- [x] 目标期刊匹配与备选（`submission/target_journals.md`：TEST → COAP → DMKD；Statistics and Computing 进阶）
- [x] TEST 格式笔记与门户核对项（`submission/test_format_notes.md`）
- [ ] 建议审稿人邮箱补填（候选池见 `notes/referee_prep.md`；提交系统内填 3–5 人）
- [x] AI 使用声明（正文 Declarations 已写：仅用于英文润色，未生成科学内容/代码/结果）

## 数据与代码

- [x] Data availability 声明（公开基准数据 Adult/COMPAS/ACSIncome，来源与预处理见补充材料 S1 与 `notes/data_prep.md`）
- [x] Code availability 声明（开源仓库，接收后公开并补 DOI；本地 git 仓库已就绪）
- [ ] GitHub 仓库创建 + 推送 + 公开 URL 填入正文与 cover letter（需作者账号操作，步骤见 `notes/submission_handoff.md`）
- [ ] Zenodo DOI（可选，仓库公开后生成）

## 提交系统

- [x] 投稿包 zip v2.0 构建完成（`submission/fuq-fairness_submission_v2.0.zip`，24 entries，710 KB）
- [ ] Springer 投稿门户注册/登录并逐项确认（Editorial Manager / Springer Nature 投稿系统）
- [ ] 上传：main_test.pdf（正文）、supplement.pdf（补充材料）、cover letter、title page
- [ ] 可编辑源文件上传（main_test.tex + refs.bib + sn-jnl.cls + sn-basic.bst + figures/）
- [ ] 填写作者/ORCID/通讯信息、建议审稿人、声明勾选
- [ ] 文本查重（相似度 <15%；单源 <5%）
- [ ] 保存投稿确认邮件与稿号（写入 `notes/submission_handoff.md`）

## 内部复核

- [x] 包一致性 `check_package.py` 13/13 PASS
- [x] 复现结果与稿件数字逐值核对（`check_numbers.py`）
- [ ] 通读 TEST 版 PDF 一遍（版式/图表位置/引用编号）
- [x] 投稿交接单（`notes/submission_handoff.md`）更新到 v2.0
