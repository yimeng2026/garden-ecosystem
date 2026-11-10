# Chen 全局 d 波相图：原始 HTML 证据摘录

- 原始 URL：https://arxiv.org/html/2311.15092
- 本批读取日期：2026-11-10
- arXiv 页面标识：`arXiv:2311.15092v3 [cond-mat.supr-con] 28 Feb 2025`
- 作者：Feng Chen；F. D. M. Haldane；D. N. Sheng
- PNAS 检索元数据：2025，DOI `10.1073/pnas.2420963122`（见 `global-dwave-scholar.csv`）。
- arXiv PDF 一次连接失败，PNAS PDF 一次 403；随后成功读取 arXiv HTML 全文。以下只记录实际读到的原文，不声称下载了 PDF。

## 原文摘录：摘要与模型角色

> Through state-of-the-art density matrix renormalization group calculations using the grand canonical ensemble, we address open issues regarding the ground-state phase diagram of the extended t-J model on a square lattice in the parameter regime relevant to cuprate superconductors. On large 8-leg cylinders, we demonstrate that the pure t-J model with only nearest-neighbor hoppings and superexchange interactions, for a wide range of doping (δ=0.1−0.2), hosts robust d-wave superconductivity possibly coexisting with weak unidirectional pair density wave. Furthermore, a small next nearest neighbor hopping t2 suppresses pair and charge density waves, resulting in a uniform d-wave SC phase in both electron- and hole-doped cuprate model systems.

## 原文摘录：参数范围

> We obtain a phase diagram for Ly=8 systems in the regime of doping level 0.1≤δ≤0.2 and hopping ratio −0.2≤t2/t1≤0.3 as shown in Fig. 1(c).

> We identify three different SC phases: (1) Uniform d-wave SC at both t2/t1≳0.15 and t2/t1≲−0.15, referred to as Uni-SC.

## 原文摘录：有限尺寸与收敛边界

> However, due to the limits of accessible ranges of M and Mc, it is currently not feasible to determine the exact power-law decay exponent of pair-pair correlations in the eight-leg hole-doped system.

> Studies on wider systems utilizing the tensor network method are highly desired to pin down the fate of PDW in the 2D limit.

## 原文摘录：GCE 自然基态含义

> The “natural ground state” is a superposition of low-energy eigenstates (Anderson Tower of states) for a system with the tendency to spontaneous symmetry breaking, and it becomes near degenerate with the true ground state for large systems.

## 原文摘录：代码与数据

> The data for all the figures and the code that produced them are available in the GitHub repository (https://github.com/DongNingSheng/Grand_SQL_tJ/tree/main).

## 审计边界

该文支持 8-leg 圆柱上的基态 d 波与特定参数区间，不是无限二维热力学极限的严格证明。Qu 等的有限温度、宽度不超过 6 的热张量网络研究是另一篇论文，不得与本文混为同一证据对象。
