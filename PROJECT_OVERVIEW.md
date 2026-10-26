# 项目总览（fuq-fairness）

> 项目：复现 Roy & Mohapatra (UAI 2026) 的公平性不确定性量化论文，并在此基础上完成一篇可投**中科院三区** SCI/SCIE 期刊的原创论文。
> 目标期刊：JCGS（*J. Comput. Graph. Statist.*，中科院 2025 数学 3 区）；作者：Cenfa Lu（桂林电子科技大学）。
> 最后更新：2026-10-27（v1.9 定稿，7 表 4 图）

## 一、一句话结论

原论文的在线乘子 bootstrap 区间**只覆盖训练随机性**，在论文自己的实验里对"总体公平性差距"的覆盖率为 0.00–0.62；
我们提出**联合 bootstrap**（训练轨迹 + 评估集 + 约束集三层重抽样）把覆盖率恢复到 0.98–1.00，并给出"忽略评估噪声却仍报告名义覆盖"的解析条件、方差预算与样本量规划，形成一篇完整的方法论文。

## 二、复现结果（论文 Table 1，固定留出集协议）

| 实验 | T | reps | 对留出估计量覆盖 | **对总体差距覆盖** | CI 宽度 |
|---|---|---|---|---|---|
| Synthetic (DI) | 2e4 | 100 | 0.89 | **0.43** | 0.077 |
| Synthetic (DM) | 2e4 | 100 | 0.86 | **1.00** | 0.208 |
| Adult (DI) | 5e4 | 100 | 1.00 | **0.00** | 0.022 |
| ACSIncome (DI) | 5e4 | 150 | 1.00 | **0.00** | 0.013 |
| COMPAS (DM) | 5e4 | 150 | 1.00 | **0.62** | 0.115 |

复现结论：论文"CI 覆盖留出估计量"的说法成立（0.86–1.00）；
但若把 CI 解读为覆盖**总体**差距 φ(θ*)（更符合应用语义），则严重失效——这正是论文的核心盲区，也是我们的切入点。
完整复现报告：`notes/repro_report.md`（定稿 v3）；证据文件：`results/tables/repro_summary.csv` 及各 `*.json`。

## 三、我们的贡献（原创方法论文，`manuscript/main.tex`）

1. **三源误差分解**：Δ̂_m(θ̄_T) − Δ(θ*) = 训练项 + 评估项 + 约束集项，证明三者渐近独立（Lemma 1/2）。
2. **解析覆盖率衰减**：Theorem 1 给出 √T(Δ̂_m(θ̄_T) − Δ(θ*)) 的 N(0, σ² + λv²) 极限，λ=T/m；Corollary 1 给出论文区间的解析覆盖率 Φ(z_{α/2}·σ_Δ/σ_tot)。
3. **联合 bootstrap**：Theorem 2 证明其渐近有效性（0.98–1.00 实测覆盖）；代价是宽度 ×1.15–5.72（×1.4 在 m≈T 时）。
4. **方差预算**：三个真实审计上训练/评估/约束集方差份额：Adult 3.6%/78.3%/18.1%，ACSIncome 0.8%/60.3%/39.0%，COMPAS 8.3%/37.1%/54.6%（评估与约束集噪声远大于训练噪声）。
5. **样本量规划**：最小可认证半宽 T、m 分配公式 + 最小可检测差距表（Adult 0.053、ACSIncome 0.060、COMPAS 0.133）。
6. **来源消融（新增）**：协议 A 下对比“只重抽样训练”“只重抽样评估”“两者都重抽样”——合成数据两源同量级时单独任一声源都不达名义（DI：0.56/0.85 训练、0.98/0.93 评估；DM：0.57/0.78 训练、0.81/0.71 评估，联合 0.88/0.99），三个真实审计评估源主导时论文区间崩塌到 0.25–0.62 而纯评估 bootstrap 达 0.97–1.00，只有联合区间在两种机制下都有效（稿件表 6 与 Fig. 4）。
7. **收敛速率的实证验证（新增）**：合成 DI 上 T∈{1e3,3e3,1e4,3e4,1e5} 网格（40
   重复、固定 D'、m=100），平均参数距离拟合斜率 −0.47、signed 训练偏差斜率 −0.46
   （理论 −0.50），验证定理 1 的 T^{-1/2} 速率；见补充材料 Table 8。

## 四、文件地图

```
fuq-fairness/
├── paper/                 原始论文 PDF 与抽取文本
├── notes/
│   ├── repro_report.md    复现报告（定稿 v3，含总表/偏离清单/复现命令）
│   ├── verification.md    独立核验（V1–V7，5 通过 / 1 失败[步长] / 1 未完成）
│   ├── theory_sketch.md   理论草稿（引理/定理/推论/证明/数值验证）
│   └── extension_results.md  E1–E6 扩展原始数据（含来源消融、收敛速率）
├── code/
│   ├── core/              fairuq.py 在线乘子 bootstrap；dgp.py 合成 DGP
│   ├── data_prep/         00_all.py（编排）+ 01_adult/02_compas/03_acsincome（原始数据 → npz）
│   ├── exps/              run_synth_di.py, run_synth_dm.py, run_real.py,
│   │                      combined_ci_v2.py, combined_ci_v3_fresh_eval.py,
│   │                      real_joint_ci.py, ablation_sources.py, variance_budget.py,
│   │                      sensitivity_adult.py, rate_check.py, make_figures.py,
│   │                      make_extension_figures.py, make_sample_size_figure.py,
│   │                      make_ablation_figure.py（Fig. 4）
│   └── verify/            ref_impl.py + 6 个独立核验脚本
├── data/{raw,processed}/  processed/*.npz + json + MANIFEST.md
├── results/
│   ├── raw/               逐次重复原始 CSV
│   ├── tables/            所有汇总表 csv/json（稿件数字的唯一来源）
│   └── figures/           repro_*.pdf、extension_main.pdf、sample_size.pdf、ablation_coverage.pdf
└── manuscript/
    ├── main.tex/main.pdf  英文稿件 v1.9（15 页，7 表 4 图，矢量图，附录 A 证明 + 附录 B 复现细节）
    ├── supplement.tex/pdf 补充材料（6 页，表 S1–S9：设置与偏离、完整复现、协议 A、方差预算、κ 敏感性、来源消融、独立核验、经验收敛速率）
    ├── make_supplement.py 由 results/tables 自动生成补充材料（不手填数字）
    ├── refs.bib          18 条参考文献（全部被引用；DOI 已核对，refs_checked.json）
    ├── check_numbers.py   123 个关键数字自动核验（missing 0）
    ├── check_refs.py      OpenAlex 逐条核对参考文献
    ├── README.md          稿件工作区说明、编译命令、期刊选择
    ├── make_review_copy.py / make_anonymous.py / make_combined.py  审稿版/匿名版/合并版
    └── submission/        目标期刊（JCGS/CAS 三区）、cover letter、checklist、title page、投稿包 zip
```

## 五、如何复现（干净环境）

```powershell
cd fuq-fairness
python code\data_prep\00_all.py                 # 原始数据 → npz（缺什么建什么；约 1 分钟）
python code\exps\run_synth_di.py                 # 合成 DI（约 3 分钟）
python code\exps\run_synth_dm.py                 # 合成 DM（约 4 分钟）
python code\exps\run_real.py --dataset adult     # 真实数据（每个 5–20 分钟）
python code\exps\make_figures.py                 # 复现图
python manuscript\check_numbers.py               # 数字核验，exit 0
```

## 六、下一步（v1.9 定稿后）

1. ✅ 作者信息（`main.tex` 作者块：Cenfa Lu，桂林电子科技大学，joffin@163.com，ORCID 0009-0003-3481-3624，通讯作者）。
2. ✅ 分区口径：中科院 2025 三区 → 目标期刊改投 JCGS（详见 `manuscript/submission/target_journals.md`）。
3. ✅ 补充材料 PDF（6 页，S1–S9）、审稿带行号版、匿名版、合并版均已生成。
4. ✅ 包自检 12/12 PASS；发布包端到端验证（light exit 0）；全量重跑逐值一致。
5. 导师逐条审阅 claims–evidence 表（`manuscript/README.md`）。
6. 官方分区表复核（学校订阅版 2025 中科院分区，确认 JCGS 数学 3 区）。
7. 仓库/Zenodo DOI、AI 使用声明、审稿人邮箱填入后按 checklist 投稿。
8. 可选：JCGS 模板套用；MLP/多分类扩展实验（Discussion 已列 future work）。

## 可复现性

已于 2026-10-26 完成全量重跑逐值验证（见 notes/reproducibility_verification.md）。快速正确性检查：`python code/tests/test_invariants.py`（16 项，< 1 s）；环境见 `requirements.txt`。

目标期刊 **JCGS**：中科院 2025 版数学 3 区、SCIE、JCR Q2、IF 1.6，ASA ScholarOne 投稿、single-anonymised；审稿用带行号版 `manuscript/main_review.pdf`（15 页）、匿名版 `main_anonymous.pdf` 与合并阅读版 `manuscript/fuq-fairness_full.pdf`（20 页）已生成。备选同口径（中科院三区）期刊：COAP（优化算法）、DMKD（机器学习应用）。
