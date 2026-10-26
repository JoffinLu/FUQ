# 目标期刊匹配（中科院 2025 三区口径；2026-10-27 决策版）

> 口径：用户要求**中科院分区三区**（2026-10-27 确认）。分区数据为第三方聚合的 2025 年中科院
> 期刊分区表（检索日 2026-10-27）；**投稿前必须以中国科学院文献情报中心《期刊分区表》官方平台
> 或学校图书馆版本复核**。本文档记录匹配与“录用率优先”理由，不构成分区承诺。

## 首选：TEST — *TEST*（Springer）

- **分区与指标（2026-10-27 检索）**：**中科院 2025 版 3 区（基础版 3 区 / 新锐 3 区）**；
  SCIE；JCR **Q2**（STATISTICS & PROBABILITY，排名 69/170）；IF **1.5**、5 年 IF 1.7、JCI 0.65；
  ISSN 1133-0686 / eISSN 1863-8260；Springer 出版。
- **why TEST（录用率优先 + 匹配）**：
  1. **口径满足**：中科院三区（基础版 3 区）；JCR Q2 同区间，官方分区表复核即可。
  2. **scope 匹配**：TEST 接收“统计方法学”论文——理论贡献 + 模拟实验 + 真实数据应用。
     本文正是：三源方差分解（理论）、解析覆盖率与联合 bootstrap（理论/方法）、5 组合成+3 组真实
     数据实验、审计预算建议（应用）；方法学贡献与实证证据的比例符合 TEST 的惯例。
  3. **录用难度相对低**：LetPub 作者自报竞争性 “Easy”（投稿量适中、3 期/年、每期约 12 篇文章，
     编辑部反馈快）；相较高区期刊更看重“贡献清晰、结论可靠、可复现”，本文这三项都是强项。
  4. **官方模板可得**：Springer 统一使用 Springer Nature LaTeX 模板（sn-jnl v2.1），已下载并
     完成转换（见 `test_format_notes.md`）；电子补充材料（supplement）受支持。
- **篇幅/格式**：单栏 17 页（7 表 4 图 + 附录 A 证明 + 附录 B 复现细节），补充材料 6 页
  （表 S1–S9）；TEST 对篇幅较宽松（无硬性 20 页限制），补充材料可长。
- **投稿系统**：Springer 期刊统一投稿门户（Editorial Manager / Springer Nature）。
- **审稿周期**：按 3–6 个月规划（TEST 平均审稿周期约 2–3 个月，编辑处理较快）。
- **风险**：TEST 偏好“统计方法学”而非“计算算法”；cover letter 与摘要已按“方法学+应用”定位
  表述（三源分解 → 区间覆盖率 → 审计实践），并把纯计算/工程细节放补充材料。

## 备选（均为中科院 2025 三区）

1. **COAP — Computational Optimization and Applications**（Springer）：中科院 2025 基础版 3 区
   （新锐 2 区）；JCR Q1，IF 2.5。匹配点：约束 SDA/投影算子/乘子法的算法视角；需改写为优化算法
   导向（算法 1 收敛与投影实现、bootstrap 作为在线方差估计），压缩统计推断篇幅。
2. **DMKD — Data Mining and Knowledge Discovery**（Springer）：中科院 2025 3 区；JCR Q1，
   IF 5.5，CCF B。匹配点：公平性审计作为 ML 应用；需突出“审计协议设计与评估数据预算”。
3. **JCGS — Journal of Computational and Graphical Statistics**（T&F/ASA）：中科院 2025 数学 3 区
   （小类统计学与概率论 3 区）；JCR Q2，IF 1.6。计算统计视角匹配，但审稿人更看重算法新颖性，
   录用难度高于 TEST。

## 进阶目标（高于三区要求，若希望冲 2 区）

- **Statistics and Computing**（Springer）：中科院 2025 2 区、JCR Q2、IF 1.8。scope 与本文
  （计算统计、bootstrap、优化）高度契合；可作为“先投更高”的一投目标（需用户决定）。

## 不采用

- **Journal of Applied Statistics**：JCR Q3 但中科院 **数学 4 区**，不满足三区口径。
- **Knowledge and Information Systems（KAIS）**：中科院 **计算机科学 4 区**。
- 纯 ML 会议（NeurIPS/ICML/UAI）：不符合期刊发表要求。

## 投稿策略

1. 首选 **TEST**（分区满足、scope 匹配、录用难度相对低、官方模板与补充材料机制成熟）。
2. 若被拒：按审稿意见改投 **COAP**（优化算法视角）或 **DMKD**（ML 应用视角）；若理论加强后
   可冲 **Statistics and Computing**。
3. 所有版本共用同一代码仓库（GitHub）与结果文件，保证可复现声明一致。

## 证据来源（2026-10-27 检索）

- TEST 分区/指标：<https://ai4paper.pro/journal/test/>（中科院 3 区 / 基础版 3 区；JCR Q2；IF 1.5；
  排名 69/170；Springer）
- TEST 竞争性（作者自报 Easy/Slow 等）：letpub.jp 期刊页 <https://www.letpub.jp/index.php?page=journalapp&view=detail&journalid=7970>
- TEST 引文格式（作者-年份）：<https://cdn.paperpile.com/s/test-citation-style/>
- Springer Nature LaTeX 模板（官方）：<https://www.overleaf.com/latex/templates/springer-nature-latex-template/myxmhdsbzkyd>
  （本地镜像 v2.1 April 2023：`tools/sn-jnl/`；`sn-jnl.cls` + `sn-basic.bst`）
- JCGS / COAP / DMKD / Statistics and Computing 分区：ai4paper 期刊页（见上一版记录）
