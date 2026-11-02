# 复现与论文项目规范（SPEC）

最后更新：2026-10-26
项目根目录：本仓库根目录（即本文件所在目录）

## 0. 项目目标

1. **复现**：Roy & Mohapatra, *Fairness Uncertainty Quantification: A Constrained Stochastic
   Optimization Perspective*, **UAI 2026** (PMLR 337:5845–5865)，官方无代码，按论文公式从零实现。
2. **发表**：在复现基础上做原创扩展，目标 JCR 三区 SCI/SCIE 或 EI 期刊（候选：Knowledge and
   Information Systems、Journal of Applied Statistics、Applied Intelligence 等）。

## 1. 论文核心（一句话）

把"公平约束分类器的训练"看成**带约束的随机优化**，用随机逼近理论证明平均迭代量 $\bar\theta_k$ 渐近正态；
由于协方差依赖未知最优解，提出**在线乘子 bootstrap**（Algorithm 2，单条数据流、可并行）估计该协方差，
从而对测试公平性 $\phi(\bar\theta_k)$（DI 或 DM）给出置信区间。

## 2. 记号与数据

- $\varphi(x)\in\mathbb R^d$：特征映射（含截距项，$d=p+1$）。
- 分类器 $h(x;\theta)=\mathrm{sign}(\theta^\top\varphi(x))$，决策边界 $\delta_\theta(x)=\theta^\top\varphi(x)$。
- 标签 $y\in\{-1,+1\}$，敏感属性 $z\in\{0,1\}$。
- 损失（CE）：$\ell(\theta)=E[\log(1+\exp(-y\varphi(x)^\top\theta))]+\frac{\kappa}{2}\|\theta\|_2^2$，
  $\kappa=10^{-4}$。
- 梯度：$\nabla\ell(\theta;w)=\dfrac{-y\,\varphi(x)}{1+\exp(y\,\theta^\top\varphi(x))}+\kappa\theta$。

### 公平性度量（在独立留出集 $\tilde D$，$|\tilde D|=m$ 上估计）

- DI：$\Delta_{DI}(\theta)=P(h=1\mid z=0)-P(h=1\mid z=1)$，$\phi_{DI}=|\Delta_{DI}|$。
  经验版：$q_i=\mathbf 1[\theta^\top\varphi(x_i)>0]$，
  $\hat\phi_{DI}(\theta)=\left|\frac{\sum_{i\in\tilde D,z_i=0}q_i}{n_0}-\frac{\sum_{i\in\tilde D,z_i=1}q_i}{n_1}\right|$。
- DM（FPR 版）：$\Delta_{DM}(\theta)=P(h=1\mid y=-1,z=0)-P(h=1\mid y=-1,z=1)$，$\phi_{DM}=|\Delta_{DM}|$。

## 3. Algorithm 1：DI-aware 加权随机对偶平均（SDA）

约束集（$\epsilon>0$，$D'$ 为固定的约束集，$n_c=|D'|$，$\bar z=n_c^{-1}\sum_{i\in D'}z_i$）：

$$\tilde x=\frac{1}{n_c}\sum_{i\in D'}(z_i-\bar z)\,\varphi(x_i),\qquad
\Theta=\{\theta:\ |\tilde x^\top\theta|\le\epsilon\}$$

投影（slab 投影，闭式）：令 $P_\Theta(v)=v-\alpha\tilde x$，其中
- 若 $\tilde x^\top v>\epsilon$：$\alpha=(\tilde x^\top v-\epsilon)/\|\tilde x\|_2^2$；
- 若 $\tilde x^\top v<-\epsilon$：$\alpha=(\tilde x^\top v+\epsilon)/\|\tilde x\|_2^2$；
- 否则 $\alpha=0$。

迭代（步长 $\eta_k=0.01\,k^{-0.501}$）：

$$\theta_k=\Pi_\Theta(-u_{k-1}),\qquad u_k=u_{k-1}+\eta_k\nabla\ell(\theta_k;W_k).$$

输出 $\bar\theta_T=\frac1T\sum_{k=1}^{T}\theta_k$。$u_0=0$，$\theta$ 初值 $0$。

## 4. Algorithm 1'：DM-aware 罚函数 SGD

$$\gamma(\theta;D'_-)=\Big(\frac{1}{n_c^-}\sum_{i\in D'_-}(z_i-\bar z)\min(0,\,y_i\varphi(x_i)^\top\theta)\Big)^2$$

目标 $F(\theta)=\ell(\theta)+R^2\gamma(\theta;D'_-)$，其中 $D'_-=\{i\in D':y_i=-1\}$，$\bar z$ 用全部 $D'$ 计算。
$\nabla F=\nabla\ell+R^2\nabla\gamma$，其中

$$\nabla\gamma(\theta)=2\,s(\theta)\cdot\frac{1}{n_c^-}\sum_{i\in D'_-,\,y_i\varphi(x_i)^\top\theta<0}(z_i-\bar z)\,y_i\,\varphi(x_i),\quad
s(\theta)=\frac{1}{n_c^-}\sum_{i\in D'_-}(z_i-\bar z)\min(0,y_i\varphi(x_i)^\top\theta).$$

SGD（无投影）：$\theta_k=\theta_{k-1}-\eta_k\big(\nabla\ell(\theta_{k-1};W_k)+R^2\nabla\gamma(\theta_{k-1})\big)$，
输出 $\bar\theta_T=\frac1T\sum_{k=1}^T\theta_k$。

## 5. Algorithm 2：在线乘子 bootstrap（对 DI 与 DM 一致）

随机扰动 $V^b_k\sim\mathrm{Unif}[1-\sqrt3,\,1+\sqrt3]$（均值 1，方差 1），$b=1,\dots,B$，各轨迹同初值。

- DI：$\theta^b_k=\Pi_\Theta(-u^b_{k-1})$，$u^b_k=u^b_{k-1}+\eta_k V^b_k\nabla\ell(\theta^b_k;W_k)$；
- DM：$\theta^b_k=\theta^b_{k-1}-\eta_k V^b_k\nabla F(\theta^b_{k-1};W_k)$。

平均 $\bar\theta^b_k=\frac1k\sum_{j\le k}\theta^b_j$，输出
$\{\hat\phi(\bar\theta^b_T)\}_{b=1}^B$ 的 $\alpha/2$ 与 $1-\alpha/2$ 分位数作为 CI。
**关键**：所有 $B$ 条轨迹在每步共用同一个 $W_k$（同一数据流），必须向量化实现。

## 6. 实验协议（论文 Table 1，逐项对齐）

| 实验 | $\epsilon$ / $R^2$ | $B$ | $|\tilde D|$ | $|D'|$ | 重复次数 |
|---|---|---|---|---|---|
| Synthetic (DI) | $\epsilon=0.002$ | 100 | 100 | 200 | 100 |
| Adult (DI) | $\epsilon=10^{-5}$ | 200 | 1000 | 1000 | 200 |
| ACSIncome (DI) | $\epsilon=0.01$ | 100 | 1000 | 1000 | 200 |
| Synthetic (DM) | $R^2=500$ | 100 | 100 | 250 | 100 |
| COMPAS (DM) | $R^2=300$ | 200 | 400 | 250 | 200 |

全局：$\eta_k=0.01k^{-0.501}$，$\kappa=10^{-4}$，$T$ 取到 $\bar\theta_T$ 收敛稳定（论文未给，取 $T=10^4$ 起步，
用 $\|\bar\theta_T-\bar\theta_{T/2}\|$ 监控；如未稳再加大）。$\alpha=0.05$。

### 数据划分（每次重复重新抽取）

1. 从全量数据无放回抽 $|D'|$ 个作为**约束集**；
2. 再从剩余数据无放回抽 $|\tilde D|$ 个作为**评估集**；
3. 训练流 $W_1,\dots,W_T$ 从剩余数据中**有放回**独立抽取（i.i.d. 流，匹配 Assumption 4.2）。
4. 若全量数据不足以支撑（合成数据），按 DGP 直接生成独立样本，不共享。

### 合成数据 DGP（照抄论文 6.1.1 / 6.2.1）

DI（Zafar et al. 2019 风格）：
$\rho(x\mid y=1)=\mathcal N((1.5,1.5),\Sigma_1)$，$\rho(x\mid y=-1)=\mathcal N((-1.5,-1.5),\Sigma_2)$，
$\Sigma_1=\begin{pmatrix}0.4&0.2\\0.2&0.3\end{pmatrix}$，$\Sigma_2=\begin{pmatrix}0.6&0.1\\0.1&0.4\end{pmatrix}$；
$P(z=1)=f_1(x')/(f_1(x')+f_{-1}(x'))$，$x'=\begin{pmatrix}\cos\pi/3&-\sin\pi/3\\ \sin\pi/3&\cos\pi/3\end{pmatrix}x$，
$f_y$ 为对应高斯密度。$y$ 取等概率 $\pm1$。

DM（Zafar 风格）：$\rho(x\mid z=0,y=1)=\rho(x\mid z=1,y=1)=\mathcal N((2,2),\Sigma_1)$，
$\rho(x\mid z=0,y=-1)=\mathcal N((1,1),\Sigma_1)$，$\rho(x\mid z=1,y=-1)=\mathcal N((-2,-2),\Sigma_1)$，
$\Sigma_1=\begin{pmatrix}3&1\\1&3\end{pmatrix}$；$y$ 等概率，$z$ 由上述条件分布给出。

## 7. 指标

- **MIS**（均值区间得分，越小越好）：
  $\mathrm{MIS}_N(l,u;\alpha)=(u-l)+\frac{2}{N\alpha}\sum_i(s_i-u)\mathbf 1[s_i>u]+\frac{2}{N\alpha}\sum_i(l-s_i)\mathbf 1[s_i<l]$。
- **Coverage**：以 $\phi(\theta^*)$ 为真值（$\theta^*$ 用独立的超大样本 / 长期训练得到），
  统计重复实验中 CI 覆盖真值的比例，目标 $\approx 1-\alpha=0.95$。
- **W2 收敛**：对每个 $k$，用跨重复的经验分布 $\hat P_k$ 与理论分布 $\mathcal N(\phi(\theta^*),\sigma^2_\Delta/k)$
  （$\Delta(\theta^*)\neq0$ 时）计算 2-Wasserstein 距离（1 维用 `scipy.stats.wasserstein_distance`，
  理论分位数在其 CDF 上取细网格），应随 $k$ 递减。
- **插件法 $\sigma^2_\Delta$**：$\sigma^2_\Delta=g^\top\Sigma g$，$g=\nabla\Delta(\theta^*)$ 用 KDE/有限差分估计，
  $\Sigma$ 用论文公式插件估计（DI：$P_A\nabla^2\ell^\dagger P_A S P_A\nabla^2\ell^\dagger P_A$；DM：论文 (4.2) 式）。

## 8. 复现验收标准（写进复现报告）

1. 合成 DI：200 次独立训练（同数据分布）的测试 DI 均值 $\approx0.025$，97.5% 分位 $\approx0.06$
   （论文 Figure 1 caption，这是可核对的定量锚点）。
2. 五个实验的 bootstrap CI 覆盖率在 $[0.90,0.99]$（100/200 次重复，二项抽样误差内）。
3. MIS 随 $k$ 单调下降（允许末端轻微波动），趋势与论文 Figure 2–6(d) 一致。
4. W2 随 $k$ 下降，且 $k$ 较大时经验密度与理论密度在视觉与数值上重合。
5. 插件 $\Sigma$ 与 bootstrap 估计的协方差（由 $\{\bar\theta^b_T-\bar\theta_T\}$ 的样本协方差×T）相对误差 < 30%
   （插件含非参估计，属定性一致）。

## 9. 目录与所有权（写入范围）

```
fuq-fairness/
  SPEC.md                  # 本文档（项目文档）
  paper/                   # 论文 PDF 与抽取文本
  notes/
    paper_analysis.md      # 论文正式版精读记录（不随仓库发布）
    data_prep.md           # 数据准备说明（data-prep）
    verification.md        # 独立核验记录（独立参考实现）
    repro_report.md        # 复现报告
  code/
    core/                  # 算法与实验驱动
    data_prep/             # 数据准备脚本（data-prep）
    verify/                # 独立核验脚本
  data/
    raw/  processed/       # 原始与处理后数据（data-prep）
  results/
    figures/  tables/  raw/# 图、表、原始结果
  manuscript/              # 稿件
```

**维护范围**：主线实现维护 `code/core/`、`code/exps/`、`results/`、
`notes/repro_report.md`、`manuscript/`。data-prep 只写 `code/data_prep/`、`data/processed/`、
`notes/data_prep.md`；独立核验实现维护 `code/verify/` 与 `notes/verification.md`。冲突时以 SPEC 为准。

## 10. 通用约定

- Python 3.13；只用 numpy/scipy/sklearn/matplotlib/seaborn/pandas（需要新包先说明）。
- 所有随机性显式 seed：`numpy.random.default_rng(seed)`；每个"重复"用独立 seed，seed 公式
  `base_seed + rep`，便于复算。
- 结果一律先落 CSV/JSON 再画图；图用 `matplotlib` 300 dpi PDF+PNG 双份。
- 任何与论文不一致、或论文未说明而自定的地方，必须记录到 `notes/repro_report.md` 的
  "偏离与假设"一节。
- 中文注释可，变量名/图轴/表头用英文（后续要投英文期刊）。
