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
