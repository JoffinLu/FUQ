# 稿件工作区（manuscript/）

**状态：v2.1（2026-10-27，目标期刊 TEST / Springer；已过五视角自审并修订）**

- `main_test.tex` / `main_test.pdf`：**TEST 投稿版**，官方 Springer Nature LaTeX 模板
  （`sn-jnl.cls` v2.1，类选项 `pdflatex,sn-basic`，作者-年份引用 `sn-basic.bst`），**18 页**，
  7 表 4 图，附录 A 证明 + 附录 B 复现细节；2 处 overfull（附录公式，16.9pt/34.2pt，可接受）。
- `main.tex` / `main.pdf`：通用 `article` 内容版（16 页），与 TEST 版正文一致；便于未安装
  Springer 模板时审阅。
- `supplement.tex` / `supplement.pdf`：补充材料（6 页，表 S1–S9；由 `make_supplement.py` 从
  `results/tables` 自动生成，不手填数字）。
- `sn-jnl.cls`、`sn-basic.bst`：官方模板文件（v2.1，2022/2023 官方发行版）。
- `refs.bib`：18 条参考文献（全部被引用；OpenAlex 逐条核对，`refs_checked.json`）。
- `main_review.pdf`：审稿用带行号版（16 页）；`main_anonymous.pdf`：双盲版（16 页，作者块
  “Anonymous Authors”）；`fuq-fairness_full.pdf`：正文+补充材料合并版（22 页）。
- `submission/`：目标期刊匹配（`target_journals.md`，TEST 首选/COAP/DMKD 备选）、cover letter、
  title page、检查清单、TEST 格式笔记（`test_format_notes.md`）、投稿包 zip。

## 构建流程

```powershell
cd D:\Desktop\Data\学习类\硕士研究生\文献阅读\DSH\fuq-fairness
$tec = "..\tools\tectonic\tectonic.exe"

python code/build_test_tex.py          # main.tex -> main_test.tex（自动提取摘要/正文/声明）
& $tec -X compile manuscript/main_test.tex --keep-logs   # TEST 版 PDF（18 页）
& $tec -X compile manuscript/main.tex --keep-logs        # 通用版 PDF（16 页）
python manuscript/make_supplement.py                     # 补充材料 tex
& $tec -X compile manuscript/supplement.tex --keep-logs   # 6 页
python manuscript/make_review_copy.py                    # 行号版
python manuscript/make_anonymous.py                      # 双盲版
python manuscript/make_combined.py                       # 合并版 22 页
python manuscript/build_submission.py --version v2.0     # 投稿包（710 KB / 24 entries，自包含编译校验）
python code/make_release.py                              # 发布包（GitHub/Zenodo）
```

## 每次改动后的自检顺序

```powershell
python manuscript/check_numbers.py    # 123 个数字串，missing 0
python manuscript/check_package.py    # 13 项包一致性（页数/表数/数字/refs/zip/发布包）
# 新增/修改参考文献后：
python manuscript/check_refs.py       # OpenAlex 核对（18 条）
```

## 数字与格式

- `check_numbers.py`：**123** 个关键数字串与 `results/tables/*` 自动比对，missing 0。
- 参考文献 18 条，DOI 全部核对（14 exact / 3 near 已修正 / roy2026uq 用 arXiv 2023 版核对）。
- 补充材料表号独立 S1–S9（`make_supplement.py` 中 `\thetable` 重定义；正文与补充材料可共存）。

## 投稿包（v2.0）

`submission/fuq-fairness_submission_v2.0.zip`：**710 KB，24 entries**，含 TEST 版与通用版正文、
两版 PDF、补充材料与 PDF、官方模板类文件、4 张矢量图、18 条 refs、全部投稿文档；
解压后 `cd manuscript && tectonic main.tex` / `main_test.tex` / `supplement.tex` 均编译通过
（`build_submission.py` 自动做自包含编译校验）。

## 发布包（GitHub / Zenodo）

`release/fuq-fairness-v1.0-source.zip`：**164 文件 / 1.55 MB**，含 code、notes、results、
manuscript、submission、PROJECT_OVERVIEW、README/LICENSE/CITATION；端到端 light 复现已验证。

## 本地 git 仓库

已 `git init` 并提交（226 文件；`data/`、`release/`、`manuscript/submission/*.zip`、`paper/`
被 `.gitignore` 排除）。GitHub 推送步骤见 `notes/submission_handoff.md`。
