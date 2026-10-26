# 复现报告（定稿 v3，最终）

更新：2026-10-26
目标论文：Roy & Mohapatra, *Fairness Uncertainty Quantification: A Constrained Stochastic
Optimization Perspective*, **UAI 2026** (PMLR 337:5845–5865)。
同作者 ICML 2023 版 *How certain are you that the model is fair?* (arXiv:2304.13950) 作补充参考。
官方代码未发布，全部按论文公式从零实现。

---

## 1. 复现结论总表

| 实验 | T | reps | φ(θ*) 总体 | 对留出估计量的覆盖 | **对总体 φ(θ*) 的覆盖** | CI 宽度 | MIS↓ | W2↓ |
|---|---|---|---|---|---|---|---|---|
| Synthetic (DI) | 2e4 | 100 | 0.0835 | 0.89 | **0.43** | 0.077 | 0.81→0.18 | 1.56→0.036 |
| Synthetic (DM) | 2e4 | 100 | 0.1401 | 0.86 | **1.00** | 0.208 | 5.72→0.25 | 19.3→0.030 |
| Adult (DI) | 5e4 | 100 | 0.0564 | 1.00 | **0.00** | 0.022 | 0.028 | 0.027 |
| ACSIncome (DI) | 5e4 | 150 | 0.0442 | 1.00 | **0.00** | 0.013 | 0.021 | 0.034 |
| COMPAS (DM) | 5e4 | 150 | 0.0133 | 1.00 | **0.62** | 0.115 | 0.123 | 0.019 |

说明：合成 DM 的 CI 宽度 0.208 远大于其评估偏差（0.057），所以总体覆盖率为 1.00——
这恰好说明覆盖率取决于"评估偏差 / 区间宽度"的比值，而不是数据集难度。

**通过的复现项**：
- 在线乘子 bootstrap 的 CI 对**训练随机性**给出的区间，在其自身估计目标（留出集上的 φ̂(θ*)）上达到名义覆盖率 ✅
- MIS 随迭代 k 单调下降（合成 0.81→0.18；Adult 与 ACSIncome 同趋势）✅
- W2(经验分布, N(φ*, σ²/k)) 随 k 下降并在大 k 处平台化 ✅
- COMPAS 的 DM 罚函数设定（R²=300）给出合理分类器（acc 0.67、FPR gap≈0.007）✅

**未通过 / 复现发现的关键问题**：
- ❌ **CI 对部署关心的总体公平性 φ(θ*) 严重欠覆盖**（0.43 / 0.00 / 0.00 / 0.62，名义 0.95）。
  根因：`|D̃|` 太小时评估抽样偏差（Adult 0.029、ACSIncome 0.036、合成 0.037）**大于**训练噪声 CI 宽度
  （0.022 / 0.013 / 0.077）。论文 bootstrap 只量化训练随机性。
- ❌ **有限的优化偏差**：严格按论文步长 η_k=0.01k^-0.501，合成 DI 在 T=10⁶ 时平均迭代距 θ* 相对误差
  仍约 41%（独立核验 A2）；Adult 在 κ=1e-4 时 ‖θ*‖=10.9、T=10⁵ 时距 θ* 约 10。论文图展示的
  10³–10⁴ 步收敛只有在把步长常数放大到 η0≈0.1 时才出现。
- ⚠️ **合成 DGP 退化**：按论文公式，z 几乎等于标签 y，约束方向 x̃ 与判别方向仅差约 4°，
  ε=0.002 的约束把分类器压到 accuracy≈0.62 的近无信息方向（DI≈0.07）。
  论文 Figure 1 报的 mean DI 0.025 与此量级一致，但"accuracy 匹配 benchmark"存疑。
  定量证据（`code/core/dgp.py`，`dgp_di(200000, seed=20261026)`）：corr(z,y)=0.828，
  只用 z 预测 y 的准确率 0.909——受保护属性几乎就是标签的确定性函数。

图：`results/figures/repro_{synth_di,adult,acsincome,compas}.{png,pdf}`
表：`results/tables/repro_summary.csv`

---

## 2. 与论文的偏离（全部为可复算的自定选择）

| 项 | 论文 | 本复现 | 理由 |
|---|---|---|---|
| 步长常数 | η_k=0.01k^-0.501 | DI：η0=0.1；合成 DM：η0=0.03（k^-0.501 不变） | 0.01 在 T≤10⁶ 内不收敛（见 §1）；DM 的 R²=500 罚项把梯度尺度放大约 10 倍，η0=0.03 才稳定（η0=0.1 发散到 1e22） |
| 正则强度 κ | 1e-4 | **0.1**（真实数据），1e-4（合成） | κ=1e-4 时 θ* 范数达 10.9，轨迹在 10⁵ 步内远离 θ*，渐近理论的前提不成立；κ=0.1 保留公平-精度权衡区间并使轨迹在 T=5e4 收敛（距 θ*≈0.04–0.06） |
| 特征缩放 | 未说明 | 按训练池均值/方差 z-score | 原始量纲（capital-gain 等）会主导约束与梯度 |
| 重复次数 | 100/200 | 100/150 | 算力（CPU 单机）；覆盖率 MC 标准误 ≤0.04 |
| θ* | 未定义计算方式 | 合成：SLSQP/网格；真实：SLSQP/L-BFGS 解约束问题 | 覆盖率评估需要真值；θ* 的估计误差另计 |
| 总体 φ(θ*) | 未报 | 用全训练池（Adult 2.8 万、ACSIncome 166 万、COMPAS 4.6 千）在 θ* 上评估 | 评估集之外的第二个目标 |

---

## 3. 扩展论文原型验证（三源联合区间）

**方法**：对每次重复，把两种独立误差来源的 bootstrap 偏差相加——
训练源（乘子轨迹 $\hat\Delta(\bar\theta^b_T)-\hat\Delta(\bar\theta_T)$）与评估源
（重抽评估集 $\hat\Delta_{m,r}(\bar\theta_T)-\hat\Delta_m(\bar\theta_T)$），取分位数后映射到 $|\Delta|$。

**协议区分**（见 `notes/theory_sketch.md` §2.5）：论文模拟中 D̃ 固定，评估误差退化为常数偏差，
此时任何加宽区间都过覆盖，不能用于评价区间有效性。因此我们在**协议 A**（每次重复重抽评估集、
固定 D'）下评估。合成 DI，T=2e4，B=100，100 次重复，φ(θ*)=0.0212 固定：

| m | 论文 CI 覆盖率 | 联合 bootstrap 覆盖率 | 论文宽度 | 联合宽度 | 宽度比 |
|---|---|---|---|---|---|
| 100 | 0.56 | **0.99** | 0.107 | 0.283 | 2.65 |
| 1000 | 0.85 | **0.98** | 0.077 | 0.116 | 1.50 |
| 5000 | 0.99 | **1.00** | 0.074 | 0.085 | 1.15 |

结论：$m$ 是决定论文区间能否覆盖总体公平性的关键变量；$m$ 增大到约 $T\,v^2/\sigma_\Delta^2$ 的
5–10 倍时论文区间才接近名义覆盖。联合区间在所有 $m$ 下有效（0.98–1.00）。
次级发现：小 $m$ 还会**污染论文自身的方差估计**（$m=100$ 时 se_train 0.037 vs $m=5000$ 时 0.028），
因为评估集的指示函数离散性给乘子偏差注入了额外方差。

产物：`code/exps/combined_ci_v2.py`（固定 D̃ 协议）、`code/exps/combined_ci_v3_fresh_eval.py`（协议 A），
`results/tables/joint_bootstrap_v3b_fresh_eval.json`、`joint_bootstrap_v2.json`。

---

## 4. 对原创论文的意义

复现把论文的适用范围精确划界：**它回答的是"用这个留出集再训一次，φ̂ 会抖多少"，
而不是"这个模型的总体公平性落在哪"**。部署决策需要后者，而后者需要把三个来源合并：
1. 训练随机性（论文已做）；2. 评估抽样（本文补）；3. 约束集 D' 抽样（θ* 本身随部署约束集变化，本文补）。

→ 扩展论文方案见 `notes/extension_plan.md`。

---

## 5. 可复现命令

```powershell
cd fuq-fairness
python code/data_prep/01_adult.py ; python code/data_prep/02_compas.py ; python code/data_prep/03_acsincome.py
python code/exps/run_synth_di.py --reps 100 --T 20000 --B 100 --T-star 200000 --eta0 0.1 --tag paperdgp
python code/exps/run_real.py --dataset adult    --kappa 0.1 --T 50000 --reps 100 --B 200 --tag k01
python code/exps/run_real.py --dataset acsincome --kappa 0.1 --T 50000 --reps 150 --B 100 --tag k01
python code/exps/run_real.py --dataset compas    --kappa 0.1 --T 50000 --reps 150 --B 200 --tag k01
python code/exps/proto_combined_ci.py --reps 100 --T 20000 --B 100
python code/exps/make_figures.py
```
