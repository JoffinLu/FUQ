# fuq-fairness：项目总览（v2.0，2026-10-27，目标期刊 TEST）

一句话：**复现 Roy & Mohapatra（UAI 2026）的公平性不确定性量化论文，并写成一篇有理论、有实验、
可复现、可投稿的中科院三区原创论文**——稿件、补充材料、投稿包、发布包和本地 git 仓库均已就绪，
目标期刊定为 **TEST**（Springer，中科院 2025 三区）。

## 复现表（论文 Table 1，5 组实验全部复现）

| 实验 | 设置（已按论文精确参数） | 复现结果（留出/总体覆盖率） |
|---|---|---|
| Synthetic DP | ε=0.002，T=2×10⁴，B=100，100 reps | 0.89 / 0.43（论文 0.97 / 0.43） |
| Synthetic EO | R²=500，T=2×10⁴，B=100，100 reps | 0.86 / 1.00 |
| Adult | ε=10⁻⁵，T=5×10⁴，B=200，100 reps | 1.00 / 0.00 |
| ACSIncome | ε=0.01，T=5×10⁴，B=100，150 reps | 1.00 / 0.00 |
| COMPAS | R²=300，T=5×10⁴，B=200，150 reps | 1.00 / 0.62（论文 0.62） |

## 五项贡献（稿件与补充材料一一对应）

1. **三源方差分解**：报告差距 = 训练（优化轨迹）+ 评估（留出样本）+ 约束集（D′）三源，
   渐近独立。实验显示训练噪声只占总不确定性 **0.8%–8.3%**，评估 37%–78%、约束集 18%–55%。
2. **解析覆盖率定理**：固定评估集时 √T 尺度下训练与评估误差比值 λ 决定覆盖损失；推导
   Corollary 1 的精确覆盖率公式，给出“忽略评估误差”的有效条件 m ≫ T·v²/σ²。
3. **联合 bootstrap**：同时重抽样三源（B 条训练轨迹 + R 次评估重抽样 + S 个约束集副本），
   协议 A 下真实数据覆盖率 0.30/0.25/0.62 → **0.98/1.00/1.00**；定理 2 给出渐近有效性。
4. **审计预算规划**：T/m 最优分配与样本量公式；三数据集“最小可认证差距” 0.053/0.060/0.133，
   其中两个数据集在实际预算下**无法认证差距非零**。
5. **来源消融 + 有限样本网格**：证明“重抽样哪个源决定覆盖率、忽略哪个源决定失效”；
   3×3 网格（T=10³/3×10³/10⁴ × m=100/300/1000）显示 m 越小联合区间越有价值。

另复现两个独立发现：论文步长 η_k=0.01k^−0.501 在给定迭代数下离约束最优约 10 个单位（需 ~10⁹
步才收敛）；合成 DGP 近乎退化（分类器 accuracy≈0.62），该生成器不宜单独用来展示公平性机制。

## 文件地图

- `manuscript/main_test.tex/.pdf`：**TEST 投稿版**（官方 Springer Nature 模板，18 页，7 表 4 图）
- `manuscript/main.tex/.pdf`：通用版内容对照（16 页）
- `manuscript/supplement.tex/.pdf`：补充材料（6 页，表 S1–S9，自动生成）
- `manuscript/main_review.pdf`（行号版 16 页）、`main_anonymous.pdf`（双盲 16 页）、
  `fuq-fairness_full.pdf`（合并 22 页）
- `manuscript/submission/fuq-fairness_submission_v2.0.zip`：投稿包（25 entries，约 1.11 MB，
  含 TEST 版/通用版/补充材料/官方模板类文件/4 张矢量图/投稿文档，自包含编译校验通过）
- `release/fuq-fairness-v1.0-source.zip`：发布包（173 文件，2.05 MB，含 code/notes/results/manuscript）
- `code/`：复现代码（fairuq.py、dgp.py、optimum.py；exps/*；verify/*；tests/*；reproduce_all.py；
  build_test_tex.py；make_release.py）
- `notes/`：复现报告、独立核验、理论草稿、扩展结果、审稿预案、可复现性验证、投稿交接单
- `README.md`（GitHub 首页）、`LICENSE`、`CITATION.cff`、`PROJECT_OVERVIEW.md`（本文件）

## 一键复现

```powershell
cd fuq-fairness
python code/data_prep/00_all.py                 # 公开数据 → npz（约 1 分钟）
python code/reproduce_all.py --scale light      # 25 s 冒烟测试（已验证）
python code/reproduce_all.py --scale full       # 全量（约 2 小时，单 CPU）
python manuscript/check_numbers.py              # 123 个数字串，missing 0
python manuscript/check_package.py              # 13/13 包一致性
```

## 已核验（2026-10-26/27）

- 5 组论文实验：全量重跑与 canonical 结果**逐值一致**（仅 elapsed_sec 不同；48 张表 0 新增/0 删除）；
- 独立实现核验：投影/KKT、乘子分布、MIS、约束最优解 4 项 PASS；步长收敛性 FAIL（作为复现发现记录）；
- 稿件数字一致：123 个数字串 missing 0；参考文献 18 条全核对；
- 包一致性 13/13 PASS（页数/表数/图数/数字/参考文献/zip/发布包/审稿版/合并版）；
- 环境：Python 3.13.15、numpy 2.2.4、scipy 1.18.1、scikit-learn 1.9.1、pandas 3.0.6；
  单 CPU（AMD Ryzen 7 8845H，27.8 GB RAM，无 GPU）。

## 投稿状态与下一步

**已完成**：作者信息（Cenfa Lu（第一作者）、Shuda Wu（通讯作者）、Xun Liu，桂林电子科技大学花江校区数学与计算科学学院；
ORCID 0009-0003-3481-3624 / 0009-0003-2590-9608 / 0009-0005-4230-3047）、
目标期刊 TEST、官方模板套用、AI 使用声明、GitHub 仓库本地提交（226 文件，待推送）。

**待作者本人完成（外部输入）**：
1. GitHub 新建仓库 `fuq-fairness` 并推送（步骤见 `notes/submission_handoff.md` §二）；
2. 官方中科院分区表复核 TEST = 三区；
3. Springer 投稿门户逐项提交（`manuscript/submission/checklist.md` §提交系统）；
4. 建议审稿人邮箱（候选池 `notes/referee_prep.md`）；查重；保存稿号。

## 关键提醒

- 论文贡献是**统计方法学**（三源分解 + 联合 bootstrap + 预算规划），不是“挑战原论文的正确性”；
  审稿回复已按此定位准备（`notes/referee_prep.md`）。
- 所有数字可从 `results/tables/*` 重建：`check_numbers.py` 是唯一数字来源；补充材料表格由
  `make_supplement.py` 自动生成，禁止手填。
- 发布包已通过端到端验证：解压后 `python code/reproduce_all.py --scale light` 22 秒 exit 0。
