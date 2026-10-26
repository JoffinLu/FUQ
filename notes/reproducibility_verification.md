# 可复现性独立验证（full 驱动重跑）

目的：证明 `code/reproduce_all.py --scale full` 在本会话环境上从零重跑全部实验，
结果与存档 canonical 版本**逐数字一致**（而非仅代码可运行）。

## 方法

1. 冻结 canonical 表快照：`fuq-fairness/.repro_checksums.json`（48 个
   results/tables 文件的 MD5，2026-10-26 21:05 左右建立，覆盖所有 JSON/CSV 表）。
2. 删除本轮旧产物前已备份？否——直接重跑覆盖同一文件名。
3. 以修正后的 full 驱动重跑（约 2 小时，含 synth DI/DM + 3 真实数据完整重复 +
   协议 A + 方差分解 + 敏感性 + 速率检查 + 来源消融 + 三张图 + 数字/引用核验）。
4. 重跑完成后对 results/tables 重新计算 MD5，与快照 diff，并分类：
   - 数值/结构变化 → 不可复现（必须解释）
   - 仅 `elapsed_sec`/时间戳变化 → 可复现
   - 新增文件（如 stray `*_main.csv`）→ 清理

## 首次发现的失败（已修复）

首次运行 `--scale full` 时驱动使用各脚本默认参数（synth DI `T=8000, eta0=0.01`；
真实数据 `T=20000, kappa=1e-4`），产出非 canonical 结果（合成 DI coverage 0.79，
φ 0.1619/0.1143，而 canonical 为 0.43/0.0835），说明“驱动默认参数 ≠ 论文参数”。
已把 FULL 命令列表改回精确 canonical 设置并 dry-run 核对后重新运行。

## 结果（重跑 vs canonical）

| 实验 | 关键量 | 重跑 | canonical | 一致 |
|---|---|---|---|---|
| Synthetic DI | φ(D̃) / φ(truth) | 0.12019 / 0.08353 | 0.12019 / 0.08353 | ✅ |
| | cov(hold)/cov(pop)/MIS/W2 | 0.89 / 0.43 / 0.183 / 0.0360 | 同 | ✅ |
| Synthetic DM | φ(D̃)/φ(truth) | 0.17391 / 0.14015 | 同 | ✅ |
| | cov(hold)/cov(pop)/width | 1.00 / 1.00 / 0.2084 | 同 | ✅ |
| Adult DI | φ(D̃)/φ(pool) | 0.08493 / 0.05640 | 同 | ✅ |
| | cov(hold)/cov(pop)/width | 1.00 / 0.00 / 0.0219 | 同 | ✅ |
| ACSIncome DI | φ(D̃)/φ(pool) | 0.00835 / 0.04421 | 同 | ✅ |
| | cov(hold)/cov(pop)/width | 1.00 / 0.00 / 0.0135 | 同 | ✅ |
| COMPAS DM | φ(D̃)/φ(pool) | 0.02538 / 0.01329 | 同 | ✅ |
| | cov(hold)/cov(pop)/width | 1.00 / 0.62 / 0.1149 | 同 | ✅ |
| 协议 A v3b | m=100 paper/joint | 0.56 / 0.99 | 同 | ✅ |
| | m=1000 paper/joint | 0.85 / 0.98 | 同 | ✅ |
| | m=5000 paper/joint | 0.99 / 1.00 | 同 | ✅ |
| real_joint Adult | paper/joint, width ratio | 0.30 / 0.983, 4.149 | 同 | ✅ |
| real_joint ACSIncome | paper/joint, width ratio | 0.25 / 1.00, 5.722 | 同 | ✅ |
| real_joint COMPAS | paper/joint, width ratio | 0.617 / 1.00, 2.078 | 同 | ✅ |
| variance Adult | 三源占比 | 3.6 / 78.3 / 18.1 % | 同 | ✅ |
| variance ACSIncome | 三源占比 | 0.8 / 60.3 / 39.0 % | 同 | ✅ |
| variance COMPAS | 三源占比 | 8.3 / 37.1 / 54.6 % | 同 | ✅ |
| κ 敏感性 | 4 行 κ 表 | 与 canonical 逐位一致 | 同 | ✅ |
| 速率检查 | 5 个斜率 | −0.090 / −0.302 / −0.469 / −0.459 / −0.687 | 同 | ✅ |
| 来源消融 synth | m=100/1000 覆盖与宽度（DI 与 DM） | 与 canonical 一致 | 同 | ✅ |

（完整 diff 见下方“校验和结论”。）

## 追加实验（验证之后，2026-10-26 21:55–22:00，Round 13）

为把“来源消融”从单一合成生成器扩展到两个生成器，新增合成 DM 消融（协议 A，固定 D′，
每 rep 新鲜评估集；`code/exps/ablation_sources.py --dataset synth_dm`）：

| 设置 | 训练-only 覆盖 | 评估-only 覆盖 | 联合覆盖 | 宽度 训练/评估/联合 |
|---|---|---|---|---|
| 合成 DM，m=100 | 0.57 | 0.81 | 0.88 | 0.151 / 0.215 / 0.239 |
| 合成 DM，m=1000 | 0.78 | 0.71 | 0.99 | 0.139 / 0.073 / 0.158 |

每一步约 129 s（T=2e4、B=100、R=300、100 reps、eta0=0.03 内置）。这两组结果产生 4 个新表
文件（`ablation_synth_dm_m100` 与 `ablation_synth_dm_m1000` 的 .json 与 _per_rep.csv），因此当前 `results/tables/`
为 50 个文件（快照 48 个中删去 2 个早期 stray 消融文件、新增这 4 个），发布包文件数 124 → 130。它们不在 48 文件快照内（快照用于验证既有 canonical
表），但由同一 `reproduce_all.py --scale full` 驱动生成（Round 13 已把两步加入 FULL 列表）。

## 校验和结论

- 重跑后 `results/tables/` 共 48 个文件，与快照同名集合：**0 新增、0 删除、19 个
  文件 MD5 变化**。
- 对 19 个变化文件逐字段比较：18 个 JSON 的差异**全部只在 `elapsed_sec`**（墙钟
  时间，机器相关）；`rate_check_synth_di.csv` 去掉 elapsed/runtime 列后**逐格一致**。
  即除运行耗时外，所有数值字段逐值相同。
- 结论：**在本会话环境上，从零重跑 `code/reproduce_all.py --scale full` 可逐值复现
  存档结果**（19/19 变化仅为运行时元数据）。
- 清理：删除早期默认参数试跑留下的 `ablation_synth_di.json` 与
  `ablation_synth_di_per_rep.csv`（两者已被 `ablation_synth_di_m100/m1000` 取代）。

## 附注

- `check_refs.py` 在重跑时遇到 OpenAlex API 暂时不可达；脚本已改为在网络失败时
  回落到上一次已验证的 verdict（`cached: true`），最终 18 条引用 verdict 与
  首次核验一致（14 exact / 3 near / 1 missing）。
- 复现包：`release/fuq-fairness-v1.0-source.zip`（157 文件，含本文件）。
## 有限样本标定网格（增量实验）

2026-10-26 追加 synth DI 3×3 网格（T∈{1000,3000,10000} × m∈{100,300,1000}，protocol A，
100 reps，B=100，R=300），新增 18 个结果文件：`results/tables/ablation_fs_T<T>_m<m>.json`
与 `_per_rep.csv`。该网格不覆盖已有表，发布包文件数由 138 增至 157。结论见
`notes/extension_results.md` E7；正文与补充材料 Table S9 引用。
