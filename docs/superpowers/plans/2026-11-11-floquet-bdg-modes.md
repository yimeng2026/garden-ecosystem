# 有限 Floquet–BdG 0／π 模数值切片实施计划

> 执行方式：主代理使用 `superpowers:executing-plans` 逐任务实现；不使用子代理。先写失败合同，再实现和验证，不能用预设标签代替谱与局域性计算。

**目标：** 在一个显式、有限、可精确对角化的 Kitaev 链中计算 Floquet 算符，检验周期化学势脉冲下的 0／π 边缘模；提供静态解析基准、端点不变量、有限尺寸和独立稀疏谱交叉检验。

**非目标：** 不证明 Floquet 超导增强、不计算材料 `Tc`、不模拟耗散或真实实验、不把准能量边缘模当成 Meissner 或独立实验证据。

**依据：** Kitaev 开放链及 δ 脉冲协议见 Thakurathi et al., Phys. Rev. B 88, 155133 (2013), arXiv:1303.2300；Mondal et al., arXiv:2203.16353v3 的 Eq. (4)–(6) 明确相同模型、约定和 `+1/-1` 边缘模判据。

## 固定模型与验收口径

取 Majorana 基 `(a1,b1,...,aN,bN)`，`a=c+c†`，`b=-i(c-c†)`。实反对称矩阵 `K` 定义为：

```text
H = i Σ_rs K_rs Γ_r Γ_s
K[a_j,b_j] = -μ
K[a_j,b_(j+1)] = (Δ-γ)/2
K[a_(j+1),b_j] = -(Δ+γ)/2
```

其余元素由反对称性给出。`ℏ=1`，`T=2π/ω`。半脉冲对称化 Floquet 算符为：

```text
F = expm(-4 K(μ0) T)
S = expm(-2 K(μ1))
U = S @ F @ S
```

这里没有 Fourier 截断：分段自由演化与 δ 脉冲均用矩阵指数精确计算。不得伪报 Fourier 截断收敛。`U` 必须为实正交矩阵，静态 `μ=0, γ=Δ` 必须使 `a1` 和 `bN` 成为解析零空间向量。

主算例固定 `γ=Δ=1, μ0=2.5, μ1=0.2, ω=7`，`N=40,80,160`。端点量：

```text
b0  = 4(μ0-γ)/ω + 2μ1/π = 0.984467...
bπ  = 4(μ0+γ)/ω + 2μ1/π = 2.127324...
```

在 `μ0>γ` 且 `0<μ1<π/2` 时，二者之间的偶／奇整数分别给出每端 `p0=1`、`pπ=1`。此解析计数必须与开放链数值分开计算，不得拿预期计数覆盖实际本征值。

候选边缘模采用 `λ=+1`（0 模）和 `λ=-1`（π 模）最近的两个本征值，并同时报告：

1. `distance=|λ-target|`；
2. 最近非候选本征值到同一目标的距离 `bulk_distance`；
3. `separation_ratio=distance/bulk_distance`；
4. 两端各 10% 格点上的总概率 `edge_weight`；
5. 尺寸增大时的距离和局域性变化。

正判需候选有端点局域性、与体模分离，并在尺寸增大时与目标趋近；否则标 `inconclusive` 或 `not_supported`，不能仅凭不变量宣布数值边缘模。控制组 `μ1=0, μ0=2.5` 为静态平凡相，不得沿用驱动组边缘模标签。

## Task 1：解析基准与失败合同

**文件：**
- `research/floquet-bdg/test_floquet_bdg.py`
- `research/floquet-bdg/floquet_bdg.py`

步骤：

- [ ] 创建合同：静态开放链两个解析零空间向量；Floquet 实正交性；端点量严格给出 `p0=pπ=1`；输出含原始本征值、候选距离、边缘权重、尺寸、独立方法与物理边界。
- [ ] 先运行 `python research/floquet-bdg/test_floquet_bdg.py -v`，保留模块缺失导致的 RED 日志。
- [ ] 实现 `majorana_k`、`static_null_vectors`、`kicked_floquet`、`endpoint_mode_counts`、`quasienergy_spectrum`、`site_weights`，不写硬编码候选本征值。
- [ ] 用 `numpy.linalg.eig`／`scipy.linalg.expm` 计算；保存环境版本和完整命令退出码。

## Task 2：尺寸、控制组与独立谱验证

**文件：**
- `research/floquet-bdg/run_study.py`
- `research/floquet-bdg/verify_floquet_bdg.py`
- `research/floquet-bdg/results.json`
- `research/floquet-bdg/candidates.csv`

步骤：

- [ ] 计算 `N=40,80,160` 全部本征值和候选表；先保存原始值，再按预注册分离比和边缘权重判定，失败不得改阈值“凑过”。
- [ ] 独立使用 `scipy.sparse.linalg.eigs` 在 `σ=+1/-1` 附近求本征值，与稠密谱比较，记录容差、失败和维度限制。
- [ ] 运行静态平凡控制组；分离“解析不变量预测”和“开放链有限尺寸数值观察”。
- [ ] 明确有限尺寸不是热力学极限证明；模型没有相互作用、耗散、自洽配对或材料参数。

## Task 3：图表、原生 Word 与交付

**文件：**
- `research/floquet-bdg/build_figure.py`
- `research/floquet-bdg/quasienergy.svg/.png`
- `research/floquet-bdg/README.md`
- `research/floquet-bdg/REPORT.docx`
- `research/floquet-bdg/run_verification.py`
- `research/floquet-bdg/run.log`

步骤：

- [ ] 图件显示实际准能量相位、候选目标距离随尺寸变化、边缘概率分布；不能用示意点冒充数值结果。
- [ ] 按 `kimi-word` 生成原生 Word：真实 TOC、中文页眉、PAGE-only 页脚、`cantSplit`、OMML 公式、准确脚注；先联系表后逐页视觉验收。视图退出 4／5／6 不重试、不用 LibreOffice。
- [ ] `run_verification.py` 重跑合同、独立验证和数值研究，真实记录每项退出码；结果 JSON 哈希一致。
- [ ] `git diff --check` 后提交并推送当前具名分支；核对本地与远端哈希，保留工作树，不合并主分支。

## 自查

- 若数值结果不支持预期，仍交付负面／不确定结果，不修改物理定义或筛选规则。
- 本切片只覆盖无相互作用二次型 Kitaev 链，不支撑 `Tc_F>Tc_eq`、LaH10、光诱导超导或材料实验结论。
- 不把精确分段矩阵指数误称为连续高频极限，也不把静态陈数或旧 p+ip 图当作 Floquet 证明。
