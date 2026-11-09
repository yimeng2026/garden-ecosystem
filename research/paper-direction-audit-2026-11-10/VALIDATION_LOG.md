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
