# 理论草稿：三源分解与合并 bootstrap 的渐近有效性

（草稿，供扩展论文 Section 3 使用；记号与 SPEC.md 一致）

## 1. 设定

- 数据流 $\{W_k\}_{k\ge1}$ i.i.d. $P$；留出评估集 $\tilde D$ i.i.d. $P$，$|\tilde D|=m$，
  与数据流独立；约束集 $D'$，$|D'|=n_c$。
- 平均迭代 $\bar\theta_T=T^{-1}\sum_{k\le T}\theta_k$ 由论文 Algorithm 1/1' 生成。
- 约束最优解 $\theta^*=\arg\min_{\theta\in\Theta(P_{D'})} l(\theta)$（给定 $D'$）。
- 真实（总体）公平性 $\phi(P)=\phi(\theta^*)$；留出估计量 $\hat\phi_m(\theta)$。
- 被报告的是 $\hat\phi_m(\bar\theta_T)$。

## 2. 分解

记 $\Delta(\theta)=P(h=1\mid z=0)-P(h=1\mid z=1)$（DM 同理），$\phi=|\Delta|$。则

$$\hat\Delta_m(\bar\theta_T)-\Delta(\theta^*)=
\underbrace{\Delta(\bar\theta_T)-\Delta(\theta^*)}_{\text{(i) 训练}}+
\underbrace{\hat\Delta_m(\bar\theta_T)-\Delta(\bar\theta_T)}_{\text{(ii) 评估}} .$$

$\text{(i)}$ 与 $\text{(ii)}$ 独立（$\tilde D$ 与数据流独立）。

**引理 2.1（训练项，论文定理的直接推论）** 在论文 Assumption 4.1–4.4 下，
$\sqrt T(\Delta(\bar\theta_T)-\Delta(\theta^*))\Rightarrow N(0,\sigma_\Delta^2)$，
$\sigma_\Delta^2=g^\top\Sigma g$。

**引理 2.2（评估项）** 固定 $\theta$，$\sqrt m(\hat\Delta_m(\theta)-\Delta(\theta))\Rightarrow N(0,v^2(\theta))$，
其中对 DI
$$v^2(\theta)=\frac{p_0(1-p_0)}{P(z=0)}+\frac{p_1(1-p_1)}{P(z=1)},\qquad p_j=P(h=1\mid z=j).$$
（对 DM 把条件换成 $y=-1$ 并相应替换分母。）由 Donsker 性（VC 类），该收敛对 $\theta\in\Theta$ 一致。

## 2.5 两种覆盖率协议（关键区分）

同一个区间，在两种实验协议下覆盖率含义不同：

- **协议 A（部署视角）**：每次重复都重抽评估集 $\tilde D$。评估误差是随机变量，
  覆盖率由 $\sigma_\Delta^2/T$ 与 $v^2/m$ 的相对大小决定（定理 3.1）。
- **协议 B（论文模拟视角）**：$\tilde D$ 在重复间**固定**。此时评估误差退化为一个
  **常数偏差** $b=\hat\Delta_m(\theta^*)-\Delta(\theta^*)$，重复间只有训练噪声在变：
  $$\mathrm{Cov}\approx\Phi\!\left(z_{\alpha/2}-\frac{|b|}{\sigma_\Delta/\sqrt T}\right)
  -\Phi\!\left(-z_{\alpha/2}-\frac{|b|}{\sigma_\Delta/\sqrt T}\right).$$
  因此**任何区间在协议 B 下的覆盖率不能直接当作其频率学有效性**：偏差固定时，
  加宽区间可以让覆盖率趋近 1（过覆盖），而窄区间会因偏差而崩塌。
  论文的 0.43/0.00/0.00/0.62 正是"$|b|$ 与 $\sigma_\Delta/\sqrt T$ 同量级或更大"的结果。

**推论**：论文的"覆盖率实验"若采用固定测试集（协议 B），其报告的覆盖率会混合两个来源，
不能证明区间对总体公平性有效。复现报告与扩展论文应同时报告 A/B 两种协议。

## 3. 主要结论：论文区间的适用条件

**定理 3.1** 若 $\Delta(\theta^*)\neq0$，且 $T/m\to\lambda\in[0,\infty)$，则
$$\sqrt T\big(\hat\Delta_m(\bar\theta_T)-\Delta(\theta^*)\big)\Rightarrow N\!\big(0,\ \sigma_\Delta^2+\lambda v^2\big).$$
于是本文固定时间区间（半宽 $z_{\alpha/2}\sigma_\Delta/\sqrt T$）的渐近覆盖率为
$$\mathrm{Cov}_{\text{paper}}\to 2\Phi\!\left(z_{\alpha/2}\frac{\sigma_\Delta}{\sqrt{\sigma_\Delta^2+\lambda v^2}}\right)-1 .$$

**推论 3.2（何时可以忽略评估误差）** $\mathrm{Cov}_{\text{paper}}\to1-\alpha$ 当且仅当
$\lambda v^2/\sigma_\Delta^2\to0$，即
$$\boxed{\ m\ \gg\ T\,v^2/\sigma_\Delta^2\ }$$
论文的实验设定（$m=100\sim1000$，$T\ge10^4$）在典型数据上不满足该条件：
我们的复现中 $v/\sigma_\Delta\cdot\sqrt{T/m}$ 达到 $1.5$–$5$，覆盖率为 0–0.62。

**定理 3.3（合并 bootstrap 的一致性）** 记
$D^*_{b,r}=[\hat\Delta_m(\bar\theta^b_T)-\hat\Delta_m(\bar\theta_T)]+[\hat\Delta_{m,r}(\bar\theta_T)-\hat\Delta_m(\bar\theta_T)]$。
在引理 2.1–2.2 与 $\bar\theta_T\to\theta^*$ 下，
$\sup_x|P^*(D^*\le x)-P(\hat\Delta_m(\bar\theta_T)-\Delta(\theta^*)\le x)|\to0$，
故分位数区间渐近有效；对 $\phi=|\Delta|$，当 $\Delta(\theta^*)\neq0$ 时用映射法（fold）保持渐近覆盖；
当 $\Delta(\theta^*)=0$ 时用 $\Delta$ 的区间包含 0 的判定，保证覆盖率不低于名义水平。

**注** 观察到的偏差还需 $T\to\infty$ 使 $\bar\theta_T\to\theta^*$（复现中 $\eta_0$ 标定）；
若 $\bar\theta_T$ 未收敛，则 (i) 项含 $\Delta(\bar\theta_T)-\Delta(\theta^*)$ 的**非零均值**，
任何方差估计都无法修复，需偏差校正或报告 $\eta$ 敏感性。

## 4. 第三源：约束集 $D'$

若部署者关心的是"对给定审计约束集 $D'$"的公平性，$\theta^*$ 视为固定，第三源不进入。
若关心"换一个 $D'$ 重新审计"的总体公平性，则 $\theta^*=\theta^*(D')$ 随 $D'$ 随机，需再加
$s_{D'}^2=\mathrm{Var}(\Delta(\theta^*(D')))$。可用外层无偏重抽样：重抽 $D'$（$R$ 次），
每次直接解约束优化得 $\hat\theta^*_r$（无需重训），估计 $s_{D'}^2$。这与训练/评估两项独立。

## 5. 样本量规划

给定目标总半宽 $w$ 与水平 $\alpha$：
$$z_{\alpha/2}^2\left(\frac{\sigma_\Delta^2}{T}+\frac{v^2}{m}\right)\le w^2 .$$
成本 $c_T T+c_m m$ 最小时
$$\frac{m}{T}=\sqrt{\frac{v^2c_T}{\sigma_\Delta^2c_m}},\qquad
T=\frac{z_{\alpha/2}^2}{w^2}\left(\sigma_\Delta^2+\sqrt{\sigma_\Delta^2v^2c_T/c_m}\right).$$
**实践含义**：评估样本的边际成本 $c_m$（标注/隐私审批）通常远高于一次 SGD 迭代 $c_T$，
但 $v^2$ 与 $\sigma_\Delta^2$ 同量级，故 $m/T$ 虽小，$m$ 的**绝对值**仍需满足 $v^2/m\lesssim w^2$。
以 Adult 为例：$v\approx0.03$，若要 $w=0.02$，仅评估项就要求 $m\ge(v/w)^2\approx2.25$（可满足），
但 $w=0.005$ 时需 $m\ge36$——仍需 $T$ 同步增大以压低训练项。给出 $(T,m)$ 的可行域图。

## 6. 数值验证（协议 A：每次重复重抽评估集；合成 DI，T=2e4，B=100，100 次重复）

固定约束集 $D'$（故 $\phi(\theta^*)=0.0212$ 固定），只改变 $m$：

| m | 论文 CI 覆盖率 | 联合 bootstrap 覆盖率 | 论文宽度 | 联合宽度 | 宽度比 | 训练 se | 评估 se |
|---|---|---|---|---|---|---|---|
| 100 | 0.56 | 0.99 | 0.107 | 0.283 | 2.65 | 0.037 | 0.100 |
| 1000 | 0.85 | 0.98 | 0.077 | 0.116 | 1.50 | 0.028 | 0.032 |
| 5000 | 0.99 | 1.00 | 0.074 | 0.085 | 1.15 | 0.028 | 0.014 |

结论与定理 3.1 一致：$m$ 增大时评估项消失，论文 CI 覆盖率单调回升到名义水平，联合区间宽度
趋近论文宽度（比值 →1）。联合区间在所有 $m$ 下有效（略保守，覆盖率 0.98–1.00）。

**次级发现**：论文的乘子 bootstrap 方差估计本身在小 $m$ 下被污染（$m=100$ 时 se_train 0.037，
$m=5000$ 时 0.028）——评估集的指示函数离散性给 $\hat\Delta(\bar\theta^b)-\hat\Delta(\bar\theta_T)$
注入了额外方差。因此小 $m$ 不仅让区间错过目标，还会让论文区间**偏宽**（却仍不够宽）。

## 7. 数值预测（已被 v3b 验证）

1. ✅ 论文覆盖率随 $\lambda v^2/\sigma_\Delta^2$ 增大而下降（0.99→0.85→0.56 对应 m=5000→1000→100）。
2. ✅ 联合 bootstrap 覆盖率在所有 m 下 ≥0.98。
3. ✅ 宽度比 →1（m=5000 时 1.15）。

