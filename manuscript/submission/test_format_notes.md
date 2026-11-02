# TEST（Springer）格式笔记与官方模板说明

> 目标期刊 *TEST*（Springer，ISSN 1133-0686）。Springer 期刊统一使用 **Springer Nature LaTeX
> Template v2.1 (April 2023, `sn-jnl.cls`)**；TEST 的参考文献采用 **Springer Basic 风格
> （作者-年份）** —— 依据 Paperpile TEST 引文样式页：正文引作 “(Roy and Mohapatra 2026)”，
> 文末按字母序排列。因此类选项用 `[sn-basic]`、参考文献样式用 `sn-basic.bst`。

## 1. 官方模板来源（本地已保存）

- 官方 Overleaf 模板页：<https://www.overleaf.com/latex/templates/springer-nature-latex-template/myxmhdsbzkyd>
- 本地镜像（v2.1 April 2023，与官方一致）：`tools/sn-jnl/`（`sn-jnl.cls`、`sn-article.tex`、
  `sn-basic.bst`、`user-manual.pdf`、`README.md`）
- 投稿包中附带 `manuscript/sn-jnl.cls` 与 `manuscript/sn-basic.bst`，保证审稿人能直接编译。

## 2. 生成与编译

```powershell
python code/build_test_tex.py           # main.tex → manuscript/main_test.tex
cd manuscript
..\..\tools\tectonic\tectonic.exe -X compile main_test.tex
```

- 类选项：`\documentclass[pdflatex,sn-basic]{sn-jnl}`。**注意**：`pdflatex` 选项在模板中
  仅用于跳过 `breakurl` 宏包（该宏包的 dvips specials 依赖 `\headerps@out`，在 XeTeX/Tectonic
  下会报 Undefined control sequence）。文献 URL 仍由 hyperref 正常链接，仅失去 URL 自动断行；
  在 pdfLaTeX 下提交时该选项同样安全。
- 前置宏包：`graphicx, multirow, amsmath/amssymb/amsthm/mathtools, booktabs, xcolor,
  textcomp, manyfoot`（`manyfoot` 是模板自身 `\AtBeginDocument` 中 `\SetFootnoteHook` 所需）。
- 作者块用模板命令：`\author[1]{\fnm{Cenfa} \sur{Lu}}\email{...}`（另两位 `\author[1]`、 `\author*[1]` 通讯作者）、`\affil*[1]{\orgdiv{...},\orgname{...},\orgaddress{...}}`；\n  三位作者的 ORCID 排在单位块后的斜体行（模板的 `\orcid` 宏需要模板包未附带的 `Orcidlogo.eps`）。\n  `\abstract{...}`、`\keywords{...}`、`\maketitle`。
- 后置部分：正文 `\section*{Declarations}`（Springer 标准声明区），条目用 `\bmhead{...}`：
  Data availability、Code availability、Funding、Competing interests、Ethics approval、
  Consent to participate、Consent for publication、Authors' contributions、Acknowledgements、
  Use of AI tools。生成脚本自动把 `main.tex` 里的 `\paragraph{...}` 声明转为 `\bmhead{...}`。

## 3. 当前编译状态（2026-10-27）

- `manuscript/main_test.pdf`：**18 页**，7 表 4 图，0 undefined reference，2 处 overfull hbox
  （附录 A 证明中的长公式，16.9pt / 34.2pt；可接受，排版时由编辑部微调）。
- `manuscript/main.pdf`（通用版）：17 页，作为内容对照版保留。
- 补充材料：`manuscript/supplement.pdf`（独立 `article` 版，6 页，表 S1–S9）；Springer 接受
  electronic supplementary material，投稿时单独上传（PDF + 源文件）。

## 4. 投稿包清单（TEST 版）

`manuscript/main_test.tex`、`main_test.pdf`、`sn-jnl.cls`、`sn-basic.bst`、`refs.bib`、
`supplement.pdf/tex`、`results/figures/*.pdf`（4 张）、`submission/{cover_letter,title_page,
checklist,target_journals,test_format_notes}.md`。审稿系统要求上传 PDF 时用 `main_test.pdf`；
若要求可编辑源文件，上传 `main_test.tex + refs.bib + sn-jnl.cls + sn-basic.bst + figures/`。

## 5. 门户核对项（官方 INSTRUCTIONS FOR AUTHORS 页面被 Cloudflare/登录墙拦截，
> 提交前必须在 Springer 投稿门户中逐项确认；以下为 Springer 期刊通用要求）

- [ ] 摘要词数上限（Springer 常见 150–250 词；当前摘要 235 词）
- [ ] 关键词数量（当前 5 个）
- [ ] Declarations 各项是否齐全（已按模板列表写全）
- [ ] 是否要求 Highlights / graphical abstract（TEST 通常不需要）
- [ ] 是否允许单栏 article 版式（sn-jnl 默认单栏，符合）
- [ ] 电子补充材料上传方式（PDF 与源文件）
- [ ] ORCID 与通讯作者邮箱在系统中填写（当前作者块已含）

## 刊名与费用（2026-10-27 核实）

- **刊名**：*TEST*（正式题名即 “TEST”；出版方副标题写作 “An Official Journal of the Spanish
  Society of Statistics and Operations Research”，即西班牙统计与运筹学会 SEIO 官方期刊）。
  ISSN 1133-0686（print）/ 1863-8260（eISSN）；Springer 出版，1992 年创刊。
- **版面费**：订阅制（hybrid）期刊，走订阅模式发表**不收取版面费/投稿费**；LetPub 的
  Open Access Info 栏 APC、APC Waiver、Other Charges 均为 N/A。可选 Open Choice 开放获取，
  APC 约 US$3,190（OpenAlex 记录的出版方目录价），不选 OA 则免费。
- **彩图**：电子版彩色始终免费；如选择在**印刷版**使用彩图，Springer 可能在接收后单独收取
  colour charge（以接收时的选项为准，本文 4 张图建议只要求电子版彩色）。
- 来源：<https://portal.issn.org/resource/ISSN/1133-0686>、
  <https://support.springernature.com/en/support/solutions/articles/6000084580-costs-of-publishing-in-springer-nature-journal>、
  <https://support.springernature.com/en/support/solutions/articles/6000137677-are-there-fees-for-publishing-in-an-open-choice-journal->、
  <https://www.letpub.com/journal-selector/journal/7778>。
