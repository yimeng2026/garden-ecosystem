# 验证执行记录

## 2026-11-10：两套量子系列的现有脚本

### 量子纠错与容错量子计算

在工作区稀疏检出 `toe-sylva-audit` 中执行：

```bash
MPLBACKEND=Agg python papers/qec_ftqc/verify_qec_ftqc.py
```

实际退出码：**0**。输出包含 `module1_steane_code: PASS` 与 `module2_surface_code_scaling: PASS`，总计 `2/2 PASS`，没有失败行。

证据边界：

- Steane 码模块验证六个稳定子的对易性、编码空间维数 2，以及 21 个单比特 Pauli 错误的非零且唯一 syndrome。
- 表面码模块把预设公式代入不同 `p` 与 `d`，检查单调性和指数斜率；它不是独立蒙特卡洛采样，也不是对真实硬件噪声的验证，不能单独支持论文三的阈值模拟主张。
- 脚本生成 `fig_steane_syndrome.png` 与 `fig_surface_code_threshold.png`。图生成成功不等于全部 15 篇论文的图表已复现。

### 拓扑量子互联网

执行：

```bash
MPLBACKEND=Agg python papers/topo_quantum_internet/verify_topo_qinternet.py
```

实际退出码：**0**。输出为 `3/3 modules passed`，没有失败行，覆盖 Kitaev 链零模、绕数相图与二维 p+ip 陈数。

证据边界：

- `mu=0` 的最低绝对能量为 `2.22e-16`，边缘 20% 区域的波函数权重为 `0.7479`；这些是特定有限尺寸、参数与离散化下的数值结果。
- p+ip 模块在 `mu=+1` 得到 `Ch=1`，而脚本注明论文写作 `Ch=-1`。脚本把其解释为符号约定差，但当前执行只证明两套符号约定存在差异，尚未完成论文、哈密顿量、BdG 基底与陈数符号的逐项统一。
- 三个基础模块不能外推为全部拓扑系列（异质结、编织、非阿贝尔统计、Altermagnet、Parafermion、网络协议等）的验证。

## 总账生成

执行：

```bash
python research/paper-direction-audit-2026-11-10/scripts/inventory_papers.py
```

最终实际退出码：**0**。读取 751 份文档，识别 18 组完全重复。第一次执行因根目录递归进入工具链而失败，随后已将共享目录与论文专属目录的资产扫描分开并重新生成；该失败不计为验证通过记录。

上述 PASS 均来自本次真实执行。它们只覆盖脚本明确检查的命题，不构成论文新颖性、全部数据真实性或外部同行评议证明。

## 主系列初审 Word 交付

执行最终结构验证：

```bash
python <kimi-word>/scripts/docx.py validate PROVIDER_REVIEW.docx
```

实际退出码：**0**，结果为 `PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`。

执行视觉预览：

```bash
python <kimi-word>/scripts/docx.py render PROVIDER_REVIEW.docx <qa-dir>
```

实际渲染 **11 页**，`near-blank pages: none`。已查看联系表，逐篇表格、页眉和原生页码存在；预览引擎仅报告编号级别覆盖的低风险兼容提示，未报告正文内容丢失。

## 真实表面码阈值基准

执行：

```bash
PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python research/paper-direction-audit-2026-11-10/scripts/run_surface_code_threshold.py
PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python research/paper-direction-audit-2026-11-10/scripts/verify_surface_code_threshold.py
PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python research/paper-direction-audit-2026-11-10/scripts/plot_surface_code_threshold.py
```

三条命令实际退出码均为 **0**。28 个点共 **560,000 shots** 全部来自真实 Stim 采样和 PyMatching MWPM 解码。成对交叉中位数为 **0.0067253928077561816**，最小值 **0.006478471377103944**，最大值 **0.00749362675686226**；六个交叉均成功，没有跳过码距对。

独立复验结果：

```json
{"point_count": 28, "mismatches": [], "csv_mismatches": [], "status": "pass"}
```

专项测试命令：

```bash
PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts .tools/qec-venv/Scripts/python -m unittest discover -s research/paper-direction-audit-2026-11-10/tests -p "test_surface_code_*.py" -v
```

实际结果：**14 项测试全部通过**。覆盖 Wilson 边界、合成曲线交叉、协议拒绝规则、零噪声、同种子复现、真实小电路、篡改检测、规范化 JSON 哈希和 SVG 标签。

最终 Word 验证：

```bash
python <kimi-word>/scripts/docx.py validate SURFACE_CODE_BENCHMARK.docx
```

实际退出码：**0**，`PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`。包内确认存在 `word/media/rId20.png`，不是图片说明文字。视觉预览为 **6 页**，`near-blank pages: none`，已查看嵌入曲线、28 点表格和六个交叉结果。首次转换曾因资源路径未嵌入图片，已用显式 `--resource-path` 重新生成并通过上述最终验收；中间版本不作为交付。

跨 worktree 复验曾发现 Git 的 Windows 换行转换导致原始协议字节哈希不同。随后新增 `protocol_digest`，以排序且压缩的 JSON 语义内容计算 SHA-256。LF 与 CRLF 测试先失败后通过，完整重跑的 28 个科学数据点与修复前逐项相同。最终规范化协议 SHA-256 为 `51603b03a4eb108842f8f84ec2d07d2d9e2b4d29aebfcf83df57781cd2612feb`，Word 中的协议标识也已局部更新并重新通过 17 部件验证。

科学边界：该结果只适用于冻结的电路级协议。交叉范围不是 FSS 置信区间，也不是对原稿 1.03% 的直接否证。原稿仍需提供其原始 shots、DEM、种子与拟合协议。

## TOE 核心开放问题证据纠偏

在 `toe-sylva-audit` 主分支 `423836ba6f0c82dfa32dc4dc3f3fb094fbd70a26` 上执行：

```bash
python scripts/build_core_open_report.py
python scripts/verify_honest_repo.py --ci
```

两条命令实际退出码均为 **0**。第一条校验 O1–O10 的 ID 完整性及所有本地证据行和引用文本，输出 6 项理论开放、2 项概念进展、2 项工程未决；第二条输出 `ALL CHECKS PASSED`，仅有三条作者名信息提示，没有失败项。

原生 Word 通过 17 部件验证并嵌入 1 幅状态图。首次五列表格出现长句逐字竖排，调整为专用 `core-open` 列宽后重新渲染为 **8 页**，`near-blank pages: none`，已逐页查看总表、外部基线和逐项证据。

科学边界：本轮完成的是证据纠偏，不是任何核心问题的理论或工程解决。O1–O10 的后续完成声明必须另行提供独立推导、最小算例、真实编译或共同似然检验。

## 强化系列审计 Word 同步缺口（2026-11-10）

本次为只读内容审查，未修改原始 `STRENGTH_SERIES_REVIEW.docx`。执行：

```bash
python "C:\Users\一梦\AppData\Roaming\kimi-desktop\daimon-share\daimon\runtime\kimi-code\home\plugins\managed\kimi-word\skills\kimi-word\scripts\verify\prep.py" "C:\Users\一梦\Documents\kimi\workspace\garden-ecosystem\research\paper-direction-audit-2026-11-10\STRENGTH_SERIES_REVIEW.docx" -o "C:\Users\一梦\Documents\kimi\workspace\garden-ecosystem\research\paper-direction-audit-2026-11-10\strength-review-current-audit"
```

实际退出码：**0**，生成只读审查用 `view.txt`（53,830 字符）。Word 正文止于“附：机器可读证据”，未包含 Markdown 后续补记。

随后实际比较 Markdown 的 K1a／K1b／K2 二级标题与 Word `view.txt`，命令退出码为 **0**，关键输出为：

```text
markdown_supplement_headings 17
present_in_word 0
missing_from_word 17
```

缺失范围为 K1a 群完备化泛性质、K1b 单射性与全消去律，以及 15 个 K2 补记（从幂等矩阵表示例到商层像模同构类）。因此当前 Word 是历史版本，不能作为最新 Markdown 总账的同步交付件。此问题登记为 **P1 文档同步缺陷**；结构验证通过的历史记录不能替代内容完整性检查。

`strength-review-current-audit/` 是未提交的只读审查中间目录，不是交付件。后续更新 Word 时必须保留原文件、重新验证 OOXML／OPC、检查全部页面，并复核这 17 节均实际出现；在完成这些步骤前，不宣称 Word 已同步。

### 验证覆盖与再生成风险补记

在同一缺节状态下执行：

```bash
python "research\paper-direction-audit-2026-11-10\scripts\verify_strength_delivery.py"
```

实际退出码为 **0**，输出 `{"status": "pass", "passed": 16, "total": 16}`；随后独立内容比较仍输出 `missing_from_word 17`。这证明旧验证只覆盖 55 条记录、两张表、目录域、公式、页眉页码、图像资产和历史渲染证据，**没有覆盖后续 17 节正文是否存在**，不能用于否定本次同步缺陷。

只读审查还发现 `scripts/render_strength_review.py` 会分别重写 `strength-review.json`、`strength-review-summary.json` 和 `STRENGTH_SERIES_REVIEW.md`。该脚本生成的是早期基线，不包含后续 resolution 字段和 17 节补记；在 preservation 测试与增量生成设计落地前，直接重跑可能覆盖后续成果。此项登记为 **P1 再生成覆盖风险**。

后续修复必须先添加两类失败测试：其一，Word 缺少任一补记标题时失败；其二，基础再生成不得删除既有 resolution 与补记。测试确认能捕获当前缺陷后，才能修改生成或同步流程；最终仍需独立执行 OOXML 验证和逐页视觉检查。

## 四份哈希变化文档的权威血缘复核（2026-11-10）

对旧库存中四个 SHA-256 不一致项逐文件执行 `git status`、提交前后 `git show` 和换行规范化比较。四份工作区文件均无未提交改动。统一 CRLF／LF 后，每项均同时满足：

```text
inventory_matches_parent_crlf = true
worktree_lf_matches_commit_lf = true
```

| 文档 | 旧库存对应的父提交 | 当前权威提交 | 当前 LF 规范 SHA-256 |
|---|---|---|---|
| Kitaev 链与 p+ip 拓扑超导体 | `5077de6aa4b99c50b14eb96e1a425784877af58e` | `600ff8c28c16b3713cf79a6194709dd0d5401e71` | `1acd4fedf0b6f75ea7228dc757d8de65cbd26cc6c014ed0fa9af0e350501071f` |
| 拓扑超导马约拉纳零能模（投稿物理学报） | 同上 | 同上 | `278825dcc1b24b109e5c4ccaa8d338aa5ed2141d19150797445a72c96a2d12fd` |
| 拓扑量子物态与量子计算研究综述（投稿物理学报） | 同上 | 同上 | `52021e8c10272ca88fdbd9a7493fe5d528619515e76819183e03b72dd060f360` |
| `toe-sylva:papers/OPEN_PROBLEMS.md` | `f33104879c5b2af62095fde7f3556e8e618e0733` | `a5ad6513f218d022caa03323a66d1a01f8833074` | `6b2a69763d53184de653b1ffbbdd76351fe88fec148f5dad046603bbd7ee3220` |

拓扑当前提交主题为 `Unify p+ip phase diagrams and Chern conventions`，核心开放问题当前提交主题为 `audit: correct core open problem evidence status`。因此四项均属于库存建立后的合法提交演进，不是来源不明的脏差异。

工程结论：权威版本映射必须分别保存 `raw_sha256`（原始工作区字节）与 `content_sha256`（CRLF 统一为 LF 后的内容），并同时记录提交、父提交和工作区状态。不得只用跨平台原始字节哈希推断正文漂移，也不得用换行规范化掩盖真实内容差异；两种哈希必须成对出现。

## Floquet 超导单篇方向与证据审计（2026-11-10）

审计对象为 `toe-sylva:papers/room_temp_sc/floquet_superconductivity_deep.md`，全文 735 行已读取。配套 `verify_rtsc.py` 在临时输出目录实际执行 `main()`，退出码 **0**，输出：

```text
[PASS]: BCS Gap Equation Universal Ratio
[PASS]: Allen-Dynes T_c Formula
[PASS]: Floquet High-Frequency Expansion
3/3 modules passed.
```

三个模块分别覆盖 BCS 能隙、Allen–Dynes 公式和二能级高频展开；不覆盖 LaH₁₀、YH₁₀、材料实验参数、相互作用 BdG 或 Floquet-DFPT。完整输出保存为 `floquet-superconductivity/run.log`。

Xie／LaH₁₀ 的 2025 年官方 DOI 页面和原文镜像已核。原文给出潜在 20–30% 提升，并明确低压 DOS 标度不是精确预测，而是相应下界估计。其余未逐条回源的实验数字保留为未核实，未据此判假。

单篇裁决为 **P0（中心证据与引用修复）**，不是独立新物理理论。发现六项问题：Xie 年份、LSCO 参数不一致、FeSe 样品混写、YH₁₀ 无来源高温外推、引用可追踪性不足、缺少结论与局限。另登记三个有边界方向：主张—证据图谱、有限 Floquet-BdG 的 0／π 模验证、相互作用模型 HFE 收敛基准；后两者均需独立设计，未在本轮实现。

交付件：

- `floquet-superconductivity/REVIEW.md`
- `floquet-superconductivity/REVIEW.docx`
- `floquet-superconductivity/review.json`
- `floquet-superconductivity/run.log`
- `floquet-superconductivity/word-qa/report.json`

最终 Word 执行 `docx.py validate`，退出码 **0**，`PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`。最终视图渲染并逐页检查 **5/5 页**，`nearBlankPages=[]`，所有 `clipped=false`；仅低风险 `w:lvlOverride` 目录编号兼容提示。原论文未修改，`word-work/` 与 QA 页面图片不纳入提交。

### Floquet 主张—来源对照补记

在初审基础上继续回源并形成 `CLAIM_SOURCE_MAP.md`、`CLAIM_SOURCE_MAP.json` 与原生 `CLAIM_SOURCE_MAP.docx`，共 8 条主张及 7 个统一修订字段。

新增直接证据：

- Giorgianni《Leggett mode controlled by light pulses》研究对象为 **MgB₂**，不是 LSCO；该引文存在来源与材料错配，不能仅修正频率后继续使用。
- Isoyama 原文样品为 **FeSe₀.₅Te₀.₅薄膜**，不是 FeSe/STO，必须拆分样品和来源。
- Xie 原文虽考察 YH₁₀ 等其他氢化物，但明确并非所有体系都超过室温；YH₁₀ 的 350–400 K 外推已建议撤回。独立实验研究给出静态理论值 305–326 K，同时未观察到 fcc-YH₁₀，三种证据状态不得混写。
- NbSe₂ 原始论文支持可逆等离子体调制，但是否满足本项目所用 Floquet 稳态定义仍需独立论证。

最终对照表 Word 的 OOXML 校验退出码 **0**，`PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`。最终视图 **3/3 页**已逐页检查，`nearBlankPages=[]`，所有 `clipped=false`，`content-loss=0`。页眉写入曾发生 `E_SWAP_FAILED`，已保留并改名交换目录后成功重试，未删除备份；中间工作目录与页面图片不纳入提交。

### Xie 预印本与正式发表时间更正

追加检索 arXiv:2312.12706 后确认：v1 于 **2023-12-20** 发布，2025 年为 npj Computational Materials 正式发表。先前“把 2023 改为 2025”的简化修订建议已撤回，改为**分别标注 2023 预印本与 2025 正式发表**。`REVIEW.md`、`REVIEW.docx`、`CLAIM_SOURCE_MAP.md`、`CLAIM_SOURCE_MAP.docx` 及两份 JSON 已统一这一区分；原论文仍未修改。[arXiv:2312.12706](kimi-cite://web?url=https%3A%2F%2Farxiv.org%2Fabs%2F2312.12706&text=Wed%2C%2020%20Dec%202023 "citation")

两份 Word 经工作副本局部更正后均再次通过 `PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`。`REVIEW.docx` 最终 **5/5 页**无近空白或裁切，QA 为 `review-time-correction-qa-final2/report.json`；`CLAIM_SOURCE_MAP.docx` 最终 **3/3 页**无近空白或裁切且 `content-loss=0`，QA 为 `claim-map-time-correction-qa-final/report.json`。长 URL 曾造成一条孤立末页，已缩短为 arXiv ID 和 DOI 后重新验证；修订顺序中的旧“Xie 改为 2025”也已同步更正。

## “室温超导必然性”反例审计（2026-11-10）

全文读取 `papers/room_temp_sc/manuscript.tex`，以 1 meV = 11.6 K 独立重算稿件 Allen–Dynes 公式，机读结果保存为 `necessity-theorem/counterexample.json` 和 `counterexample.log`：

| 参数 | 独立 $T_c$ |
|---|---:|
| $\lambda=2,\omega_{\log}=100$ meV、$\mu^*=0.15$ | 148.243 K |
| $\lambda=2,\omega_{\log}=100$ meV、$\mu^*=0.10$ | 166.850 K |
| $\lambda=2.5,\omega_{\log}=140$ meV、$\mu^*=0.10$ | 267.453 K |

三组均低于 300 K，第三组还满足稿件所称内部强耦合和声子条件，直接反驳“任何严格内部组合超过 300 K”。另行确认 $\mu_c^*(2)=0.3$（非约 0.15），以及 Kiessling sharp constant 为 $0.1827262477\ldots$，约 0.371 接近原文 2.034 倍上界而非该 sharp constant 本身。

裁决为 **P0：中心命题与自身推导冲突**。后续方向改为 300 K 临界流形、降维—屏蔽映射证明或否证、反例优先的 Lean／数值验收。其他实验数字保留未核实，不据此判假。

交付件：`necessity-theorem/REVIEW.md`、`REVIEW.docx`、`review.json`、`counterexample.json`、`counterexample.log`、`word-qa/report.json`。Word 校验退出码 **0**，`PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`；最终 **4/4 页**已逐页检查，无近空白或裁切，仅低风险目录编号兼容提示。原稿未修改。

TOE 勘误簿已登记 FE-18，分支 `audit/necessity-counterexample`，提交 `a610606`。该登记只保留反例与研究方向，不宣称原稿已修订或中心问题已解决。

### 室温超导版本血缘补记

逐项读取 `manuscript.tex`、Science、Nature、arXiv 与主模板，机读 `lineage-review.json` 确认五者属于同一错误研究纲领，独立新方向为 0：

- Science 在同一段先算约 148 K，再直接声称超过 300 K，属于直接内部矛盾；
- Nature 压缩继承同一必然性断言；
- arXiv 的完整证明与参考文献仍为占位；
- 主模板虽有作者名，理论结构、证明、预测、验证、图件、数据和代码仍大量待填；
- `organized/02-主论文` 只有四份 Markdown，无计算脚本、结构文件、求解输出或收敛日志，不能由方法叙事证明 DFT／EPW 已执行。

交付 `LINEAGE_AUDIT.md`、`LINEAGE_AUDIT.docx`、`lineage-review.json`、`lineage.log`、`lineage-word-qa/report.json`。Word 校验退出码 **0**，`PASSED (17 parts XSD + semantic checks; gen: 6 checks clean)`；最终 **3/3 页**已逐页检查，无近空白或裁切，仅低风险目录编号兼容提示。原文件均未修改。

FE-18 已补全受影响版本，提交 `37ea8d0`。后续只设一个反例与临界流形项目，不为 Science、Nature、arXiv 分别立项。
