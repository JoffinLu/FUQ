# 投稿检查清单（Journal of Computational and Graphical Statistics / 中科院 2025 三区 版）

## 技术项（提交前必须全部打勾）

- [x] 目标期刊分区核实（2026-10-27）：JCGS 中科院 2025 版数学 3 区（来源见 `target_journals.md`；官方分区表提交前复核）

- [x] 用 tectonic/LaTeX 编译通过，无 undefined reference（2026-10-26：tectonic exit 0，仅 bbl 重跑提示）
- [x] 参考文献逐条核对 DOI/卷期页：`check_refs.py` → 18/18：14 exact、3 near（已修正）、roy2026uq 用其 2023 版核对；结果 `refs_checked.json`
- [x] 所有图以矢量 PDF 提交（`results/figures/repro_synth_di.pdf`、`repro_compas.pdf`、`sample_size.pdf`、`ablation_coverage.pdf`），正文按顺序引用（Fig. 1–4）
- [x] 所有表可编辑（LaTeX 表格，7 张）
- [x] 数值与结果文件一致：`check_numbers.py` → 123 个数字串，missing 0
- [x] T^{-1/2} 收敛速率的经验验证：supplement Table 8（T=1e3…1e5；‖θ̄−θ*‖ 斜率 −0.47、signed 训练偏差 −0.46，理论 −0.50），正文 Section 6 引用
- [x] 二遍通读（v1.7）：Neither…nor 语法、notation 表正文引用、消融表小数统一
- [x] 两栏排版演练（notes/format_rehearsal/，Tectonic 9 页，表格 resizebox 可读；长公式 7 处 overfull 留给正式模板）
- [x] 摘要长度：约 223 词（<= 250）
- [ ] 主文页数：当前单栏 15 页（7 表 4 图，0 overfull/0 undefined）；JCGS/T&F 模板与门户页数要求待套用后确认
- [x] 作者列表、单位、通讯作者邮箱、ORCID 已写入 `main.tex`（Cenfa Lu；桂林电子科技大学数学与计算科学学院；joffin@163.com；0009-0003-3481-3624；通讯作者）
- [x] 关键词 5 个（fairness auditing; uncertainty quantification; constrained stochastic optimization; online bootstrap; distribution-free inference）
- [ ] 公式编号连续；定理/引理/推论/假设编号风格符合期刊要求
- [x] 符号表：Table 1 (Notation)

## 声明项

- [x] Data availability statement（正文 Statements 已写，待填仓库 URL）
- [x] Code availability statement（正文 Statements 已写，待填 Zenodo DOI）
- [x] Funding statement（正文 Statements：no specific grant）
- [x] Conflict of interest statement（正文 Statements）
- [x] Ethics statement（正文 Statements：公开二手数据）
- [ ] AI 使用声明（若期刊要求；如实说明 AI 辅助了代码与文字起草，作者对内容负责）

## 投稿包

- [x] Cover letter 已填作者信息（`cover_letter.md`；仅日期/仓库 DOI/AI 声明待补）
- [ ] 建议审稿人 3–5 名（候选池与理由已列于 `notes/referee_prep.md` §建议审稿人；**邮箱待作者补填**；避免建议 Roy/Mohapatra）
- [x] 标题页（`title_page.md`：作者、单位、ORCID、通讯作者、声明）
- [x] 盲审版本：`manuscript/main_anonymous.pdf`（`python manuscript/make_anonymous.py`；作者块=Anonymous Authors）
- [ ] 图表源文件单独打包（如需；矢量 PDF 已在 `results/figures/`）
- [x] 补充材料：`manuscript/supplement.pdf`（6 页，表号 S1–S9：设置偏离、完整复现表、协议 A、方差预算、κ 敏感性、来源消融（含 COMPAS）、独立核验、经验收敛速率、有限样本标定；由 `make_supplement.py` 自动生成）
- [x] 复现报告：`notes/repro_report.md`（中文内部记录，可作 repository 文档）

## 内部复核（投稿前 48 小时）

- [ ] 与导师逐条过 claims–evidence 表（每条主张都有证据支撑，强度匹配）
- [x] 复现命令在干净环境跑通：release zip 解压 + 预置 `data/processed/` 后 `--scale light` 22.4 s exit 0；仓库内 `--scale full` 重跑约 2 h，results/tables 48 个文件除 `elapsed_sec` 外逐值一致（`notes/reproducibility_verification.md`）
- [ ] 论文中无夸大表述（"first"/"novel"/"prove" 等词逐处检查）
- [x] 所有数字与 `results/tables/*.csv/json` 一致（`check_numbers.py`：123 个数字，missing 0）
- [x] 包一致性：`python manuscript/check_package.py` 12/12 PASS；投稿包 zip v1.9（20 entries）解压后自包含编译 exit 0
- [x] 快速不变量测试：`python code/tests/test_invariants.py` → 16 checks PASS（< 1 s，无需数据）；环境固定于 `requirements.txt`
- [x] 全量重跑逐值复现（full 驱动，约 2 h；0 新增/0 删除，19 个变化文件仅 elapsed_sec）
- [ ] 查重（Turnitin/iThenticate，按学校要求）
