# 稿件工作区（manuscript/）

## 当前状态（2026-10-27，v1.11）

- ✅ **全量重跑逐值复现**（`notes/reproducibility_verification.md`）：`python code/reproduce_all.py --scale full`
  从零重跑约 2 小时；`results/tables/` 48 个文件 **0 新增/0 删除**，19 个 MD5 变化的文件中
  18 个 JSON 仅 `elapsed_sec` 不同、`rate_check` CSV 去时间列后逐格一致——即除运行耗时外**逐值复现**。
  驱动参数已固定为论文精确设置（`--tag paperdgp/k01`，不再依赖脚本默认值）。

- ✅ **全文完成并编译**：`main.pdf`（**15 页**，0.22 MB，矢量图无位图；**7 表 4 图**，附录 A 证明 + 附录 B 复现细节）+ `supplement.pdf`（**6 页**补充材料：完整复现表、协议 A、方差预算、κ 敏感性、**来源消融（7 组：合成 DI/DM × m=100/1000、Adult、ACSIncome、COMPAS）**、独立核验、**经验收敛速率（T=1e3–1e5）**、**有限样本标定（3×3 网格）**）
- ✅ **二遍通读完成**（v1.7）：修正 Neither…nor、正文引用 notation 表、消融表小数统一；两栏排版演练通过（`notes/format_rehearsal/`，9 页，表格自动缩放可读）
- ✅ **数字一致性核验**：`python manuscript/check_numbers.py` → **123 个数字串**，missing 0
- ✅ **参考文献零错误编译**：无 undefined reference / 未定义引用
- ✅ **参考文献 DOI 核对**：`python manuscript/check_refs.py` → 18 条全部有据可查：
  14 条 exact、3 条 near（已修正 DOI/年份）、`roy2026uq` 为 UAI 2026 新论文未被 OpenAlex 收录
  （用其 2023 版 `roy2023uq` 核验，exact）。结果落盘 `refs_checked.json`
- ✅ 投稿材料：`submission/target_journals.md`、`submission/cover_letter.md`（已定稿草稿）、`submission/checklist.md`
- ✅ 模拟审稿意见与回复预案：`notes/referee_prep.md`（8 条 major + 6 条 minor + 大改风险点）
- ✅ 投稿包 zip：`submission/fuq-fairness_submission_v1.9.zip`（**418 KB，20 个文件**；由 `build_submission.py` 生成并**自动解压实测**：`cd manuscript && tectonic main.tex/supplement.tex` 均 exit 0；含稿件+补充材料+矢量图+复现报告+投稿材料+title page/JCGS 格式说明）
- ✅ **双盲版本**：`main_anonymous.pdf`（15 页；`python manuscript/make_anonymous.py` 生成，作者块替换为 Anonymous Authors）
- ✅ 包一致性自检：`python manuscript/check_package.py` → **12/12 PASS**（15/6 页、7 表 4 图、123 数字、18 refs、S1–S9 表号、投稿包 20 entries、发布包 157 files、审稿版 15 页、合并版 21 页）
- ✅ **审稿用带行号版**：`manuscript/main_review.pdf`（15 页，`lineno` 连续行号，`make_review_copy.py` 生成；作者信息已填（Cenfa Lu））
- ✅ **合并阅读版**：`manuscript/fuq-fairness_full.pdf`（21 页 = 主稿 15 + 补充 6，`make_combined.py`）
- ✅ **目标期刊（2026-10-27 确认口径：中科院三区）**：首选 **JCGS**（*J. Comput. Graph. Statist.*）——中科院 2025 版数学 3 区、小类统计学与概率论 3 区；SCIE；JCR Q2；IF 1.6；ASA ScholarOne 投稿；scope=统计计算与图形方法，与本文（约束优化 + 在线/联合 bootstrap + 计算实验）契合（详见 `submission/jcgs_format_notes.md`）
- ✅ **快速正确性测试**：`python code/tests/test_invariants.py` → **16 项检查全通过、< 1 s**（投影/KKT、乘子矩、DI/DM 泛函、有限差分梯度、训练确定性、生成器可复现）；环境由 `requirements.txt` 固定
- ✅ 源码发布包：`release/fuq-fairness-v1.0-source.zip`（**1.25 MB，157 个文件**，含 MANIFEST.tsv、README/LICENSE/DATA_NOTES；不含原始数据与 png；**已端到端验证**：解压后 `--scale light` 22.4 s exit 0，数据可用 `FUQ_RAW_DIR` 指向或预置 `data/processed/`）
- ✅ 作者信息（2026-10-27）：Cenfa Lu，桂林电子科技大学数学与计算科学学院，joffin@163.com，ORCID 0009-0003-3481-3624，通讯作者；`main.tex` 作者块已填
- ⏳ 待办：仓库 URL/Zenodo DOI 填入 Statements、AI 声明、审稿人邮箱、导师审阅 claims–evidence、门户提交

## 文件

| 文件 | 内容 |
|---|---|
| `main.tex` | 全文：摘要、引言、相关工作、setup、三源分解（Lemma/Theorem/Corollary/Remark）、方法（joint bootstrap）、样本量、实验（7 表，含来源消融与 notation）、讨论、结论、Statements、附录 A 证明、附录 B 复现细节 |
| `supplement.tex` / `supplement.pdf` | 补充材料（6 页，表号 S1–S9 独立编号）：S1 设置与偏离、S2 完整复现表、S3 协议 A、S4 方差预算、S5 κ 敏感性、S6 来源消融、S7 独立核验、S8 经验收敛速率、S9 有限样本标定、S10 复现命令 |
| `make_supplement.py` | 由 results/tables/* 自动生成 supplement.tex（不手填数字） |
| `refs.bib` | 18 条参考文献，全部被正文引用，DOI 已核对（见 `refs_checked.json`） |
| `check_numbers.py` | 把稿件中 123 个关键数字与 `results/tables/*` 逐一比对，exit 0 = 一致 |
| `check_refs.py` | 用 OpenAlex 逐条核对 refs.bib 的标题/作者/年份/venue 并记录 DOI（网络不可达时回落到上次 verdict） |
| `submission/` | 目标期刊匹配（JCGS/CAS 三区）、cover letter、投稿检查清单、title page、JCGS 格式笔记 |

## 编译（tectonic 便携版，无需本机 LaTeX）

```powershell
& "D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\tools\tectonic\tectonic.exe" `
  "D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness\manuscript\main.tex" --keep-logs
```

tectonic 会联网下载宏包；首次编译较慢（约 1–2 分钟）。
已知非致命提示：`internal consistency problem when checking if main.bbl changed`
（tectonic 的 bbl 重跑提示，PDF 正常生成）；其余 overfull hbox 已在 v1.2 修复。

## 每次改动后的自检顺序

```powershell
cd D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness
python manuscript\check_numbers.py   # exit 0 = 数字一致
python manuscript\check_refs.py      # 仅在新增/修改参考文献后跑
& "..\tools\tectonic\tectonic.exe" manuscript\main.tex --keep-logs   # exit 0 = 编译成功
```

## 期刊选择

首选 **JCGS**（*Journal of Computational and Graphical Statistics*，中科院 2025 三区；
方法+计算+可复现代码最贴合）。备选 COAP（优化算法视角，三区）、DMKD（ML 应用视角，三区）；
Statistics and Computing（二区）作为理论加强后的进阶目标。
详见 `submission/target_journals.md`。

## 提交前必须做

1. ✅ 作者信息与通讯作者（已填）；2. ✅ 分区口径（中科院 2025 三区，JCGS，提交前官方复核）；
3. 导师逐条审 claims–evidence 表；4. 仓库 URL/Zenodo DOI 填入 Statements 与 cover letter；
5. AI 声明与审稿人邮箱；6. 按 `submission/checklist.md` 打勾并提交。
