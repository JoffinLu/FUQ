# 投稿交接单（JCGS / 中科院 2025 三区版，2026-10-27）

> 用途：把“已完成的内部工作”与“必须由作者本人完成的外部事项”分开，按此单逐项勾选即可投稿。
> 稿件版本 v1.9；主稿 15 页（7 表 4 图）+ 补充材料 6 页（表 S1–S9）。

## 一、目标期刊与作者

- **目标期刊**：*Journal of Computational and Graphical Statistics*（JCGS，T&F/ASA 联合刊）
  - 中科院 2025 版：**数学 3 区**、小类统计学与概率论 3 区（用户口径：中科院三区即可）
  - SCIE；JCR Q2；IF 1.6（2025 JCR）——**分区按中科院口径**（JCR 口径为 Q2，见 `target_journals.md`）
  - 投稿：ASA ScholarOne（`mc.manuscriptcentral.com/amstat`）；single-anonymised
- **作者/通讯作者**：Cenfa Lu，桂林电子科技大学 数学与计算科学学院，joffin@163.com，ORCID 0009-0003-3481-3624（`main.tex` 作者块已填）

## 二、已就绪（无需再动）

| 交付物 | 路径 | 说明 |
|---|---|---|
| 主稿 PDF | `manuscript/main.pdf` | 15 页，7 表 4 图，附录 A（证明）+ 附录 B（复现细节） |
| 补充材料 PDF | `manuscript/supplement.pdf` | 6 页，表号 S1–S9（S6 为 7 组来源消融、S9 有限样本标定） |
| 合并阅读版 | `manuscript/fuq-fairness_full.pdf` | 21 页，主稿+补充材料 |
| 审稿用带行号版 | `manuscript/main_review.pdf` | 15 页，连续行号 |
| 双盲版（可选） | `manuscript/main_anonymous.pdf` | 作者块=Anonymous Authors |
| 投稿包 | `manuscript/submission/fuq-fairness_submission_v1.9.zip` | 20 entries，自包含（解压 `tectonic main.tex` 可编译） |
| 源码发布包 | `release/fuq-fairness-v1.0-source.zip` | 157 files，一键复现（light 约 23 s exit 0） |
| 复现报告 / 独立核验 / 审稿预案 | `notes/repro_report.md` · `notes/verification.md` · `notes/referee_prep.md` | 5 组实验+偏离清单；7 项检查；C1–C8+minor+审稿人候选 |
| 数字一致性 | `manuscript/check_numbers.py` | 123 个数字串，missing 0 |
| 包一致性 | `manuscript/check_package.py` | 12/12 PASS |
| 快速测试 / 环境 | `code/tests/test_invariants.py` · `requirements.txt` | 16 项不变量检查；依赖已 pin |

## 三、必须由作者本人完成（按顺序）

1. **仓库 URL / Zenodo DOI**：`main.tex` Statements 与附录 B、cover letter 中 `[repository URL / DOI]` 占位符；建议把 `release/fuq-fairness-v1.0-source.zip` 上传 Zenodo 得 DOI。
2. **AI 使用声明**：按期刊模板填写（cover letter 中已有占位段）。
3. **建议审稿人邮箱**：从 `notes/referee_prep.md` §建议审稿人 候选池选 3–5 人补邮箱（避免 Roy/Mohapatra）。
4. **导师审阅**：逐条过 claims–evidence C1–C6（`manuscript/README.md`）与 `notes/referee_prep.md`。
5. **官方分区复核**：学校订阅的中科院 2025 分区表确认 JCGS=数学 3 区。
6. **JCGS 模板套用**：当前通用 article 11pt 单栏；模板与页数要求见 `submission/jcgs_format_notes.md`。
7. **提交前 48 小时复核**后，在 ScholarOne 上传：`main.pdf`、`supplement.pdf`、cover letter、title page、suggested reviewers；若要求双盲用 `main_anonymous.pdf`。

## 四、一键复现

```powershell
cd fuq-fairness
python code/data_prep/00_all.py               # 原始数据 → data/processed（缺什么建什么）
python code/reproduce_all.py --scale light    # ~23 s：合成 DI/DM 小规模 + 全部数值校验
python code/reproduce_all.py --scale full     # 全部 29 步（约 2 h，纯 CPU）
```

环境：CPU-only（Ryzen 7 8845H / 27.8 GB），Python 3.13.15，依赖见 `requirements.txt`。

## 五、审稿预案要点

- **“论文没写错为何要改”**：不矛盾，是补全；协议 B（固定评估集）下论文结论仍成立（Remark 2）。
- **“联合 bootstrap 成本”**：重抽评估集便宜、训练轨迹复用；宽度代价见 Table 6 / Fig 4。
- **“为何不解析 CLT”**：三层独立随机性 + 约束集非光滑；Theorem 1 给解析极限，bootstrap 给有限样本实现（附录 A）。
- **“线性/NTK 假设”**：与论文一致；扩展见 Discussion（核方法、多分类、公平性约束族）。
- 详细应答：`notes/referee_prep.md`（C1–C8 + minor + 3 个大改风险点）。
