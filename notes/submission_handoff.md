# 投稿交接单（v2.0，2026-10-27，目标期刊 TEST）

## 一、已就绪（可直接提交）

| 项目 | 位置 | 状态 |
|---|---|---|
| TEST 版正文（Springer 官方模板） | `manuscript/main_test.pdf`（18 页） | ✅ 编译 exit 0，0 undefined |
| 通用版正文（内容对照） | `manuscript/main.pdf`（17 页） | ✅ |
| 补充材料 | `manuscript/supplement.pdf`（6 页，表 S1–S9） | ✅ 自动生成 |
| 投稿包 | `manuscript/submission/fuq-fairness_submission_v2.0.zip`（24 entries，约 1.09 MB） | ✅ 自包含编译校验 |
| 发布包 | `release/fuq-fairness-v1.0-source.zip`（169 文件，2.00 MB） | ✅ 端到端 light 复现验证 |
| 自审记录 | `notes/review_changes.md`（C1–C6 修订已入稿） | ✅ 13/13 包自检 |
| 本地 git 仓库 | `.`（226 文件已提交，`data/`/`release/`/`paper/` 已排除） | ✅ 就绪待推送 |
| 投稿文档 | cover letter / title page / checklist / TEST 格式笔记 | ✅ |
| 数字核验 | 123 个数字串 missing 0 | ✅ |
| 包自检 | 13/13 PASS | ✅ |

## 二、GitHub 推送步骤（需作者账号）

```powershell
# 1) 在 https://github.com/new 新建仓库：fuq-fairness，Public，不要初始化 README
# 2) 在本地仓库目录执行（把 <account> 换成 GitHub 用户名）：
cd D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness
git remote add origin https://github.com/<account>/fuq-fairness.git
git branch -M main
git push -u origin main
# 3) 首次推送若提示认证：使用 GitHub 用户名 + Personal Access Token（不要用密码）
```

推送完成后：

1. 把仓库 URL 填入 `manuscript/main.tex`（及重新生成的 `main_test.tex`）的 Code availability
   段落与 cover letter 中 `[repository URL / DOI]` 占位；
2. 重新编译 `main.pdf` / `main_test.pdf`，重建 `submission/build_submission.py --version v2.0`
   与 `code/make_release.py`，重跑 `check_package.py`；
3. 可选：仓库打 tag `v1.0.0` 并在 Zenodo 生成 DOI（填 DOI 到正文与 cover letter）。

## 三、外部事项（作者本人/学校资源）

1. **官方分区复核**：中国科学院文献情报中心《期刊分区表》官方平台 / 学校图书馆版本，确认
   TEST 2025 版为数学三区（本文档依据第三方聚合数据，2026-10-27）。
2. **Springer 投稿门户**：注册/登录 Editorial Manager，逐项完成 `submission/checklist.md`
   「提交系统」6 项；上传 main_test.pdf、supplement.pdf、cover letter、title page 与可编辑源文件。
3. **审稿人姓名/邮箱**：从 `notes/referee_prep.md` 候选池选 3–5 位，验证邮箱后填入系统。
4. **AI 使用声明**：正文 Declarations 已写明“AI 仅用于英文润色，未生成科学内容/代码/结果”；
   若 TEST 门户另有勾选/声明字段，按同样口径填写。
5. **语言润色**：如学校要求润色证明，可使用 Grammarly/Wordvice 等；当前英文经两遍通读 +
   AI 润色辅助，无中式英语典型问题（`notes/reproducibility_verification.md` 记录）。
6. 保存投稿确认邮件与稿号，写入本文件第四节。

## 四、投稿后记录

- 投稿日期：待填
- 稿号：待填
- 状态：待填
