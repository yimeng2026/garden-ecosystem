# Floquet 工程驱动高温超导：单篇方向与证据审计

> 审计日期：2026-11-10
> 对象：`toe-sylva-audit/papers/room_temp_sc/floquet_superconductivity_deep.md`
> 范围：全文结构、内部一致性、配套脚本、Xie 等 LaH₁₀ 原始来源；不是对全部 35 条引文和全部实验数字的逐项终审。

## 一、裁决摘要

这篇文章的价值是提供一张覆盖**周期驱动、光诱导响应、氢化物第一性原理和 Floquet 拓扑超导**的研究地图，而不是一套已经成立的“室温超导必然性”理论。它可以发展成证据组织与数值复核方向，但当前应先修复来源追踪、材料名称、时间线和定量表述，再扩展新稿。

**优先级：P0（中心证据与引用修复）。** 这里的 P0 不表示全文皆假，而是表示若直接引用其 300 K、350–400 K 和实验参数，可能把不同模型、样品和证据等级混成同一结论。

| 维度 | 当前裁决 |
|---|---|
| 方向角色 | Floquet 超导综述与研究路线入口，不是独立新物理理论 |
| 项目内增量 | 将驱动 BCS、光诱导实验、Floquet-DFPT 和 0／π Majorana 放入同一目录 |
| 主要风险 | 瞬态光诱导、稳态 Floquet、连续波等离子体调控和高压理论预测被并列后缺少证据分层 |
| 数值脚本 | 通用公式的 3 个模块通过；不覆盖材料级预测与实验参数 |
| 下一步 | 先建立主张—来源—样品—模型—证据等级表，再决定是否开展数值研究 |

## 二、已实际运行的验证

在临时输出目录执行 `verify_rtsc.py` 的 `main()`，没有覆盖仓库既有图件。实际退出码为 **0**，输出为：

```text
[PASS]: BCS Gap Equation Universal Ratio
[PASS]: Allen-Dynes T_c Formula
[PASS]: Floquet High-Frequency Expansion
3/3 modules passed.
```

完整输出保存于 `run.log`。[run](kimi-cite://text?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Cgarden-ecosystem%5Cresearch%5Cpaper-direction-audit-2026-11-10%5Cfloquet-superconductivity%5Crun.log&text=3%2F3%20modules%20passed "citation")

| 模块 | 实际结果 | 能支持什么 | 不能支持什么 |
|---|---|---|---|
| BCS 能隙方程 | $\lambda=0.3$ 时比值 3.5323；$T_c$ 近似误差 0.0001 | 数值求解与弱耦合公式在该测试点一致 | 不能证明任何材料的 $T_c$ |
| Allen–Dynes | 单调性、线性、临界耦合及 AD／McMillan 比值均通过 | 公式实现和基本性质自洽 | 不能把 DOS 增大直接当成特定材料预测 |
| 二能级 HFE | 高频最大相对误差 0.000947；$\Omega=60$ 时误差 0.0040 | 二能级模型的高频展开与准能量数值传播一致 | 不能验证相互作用 BdG、氢化物 DFPT 或光诱导实验 |

因此，`3/3 modules passed` 只能登记为**通用数值工具箱通过**，不能登记为整篇综述或室温超导主张通过。

## 三、原始来源核查：Xie 与 LaH₁₀

Xie 等的论文确为 2025 年 npj Computational Materials 工作，官方 DOI 页面为 `s41524-025-01725-z`，内容是以中红外激光和 Floquet-DFPT 研究氢化物的超导转变温度。[npj Computational Materials](kimi-cite://web?url=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs41524-025-01725-z&text=In%20this%20paper%2C%20we%20present%20a%20dynamical%20method "citation")

原文摘要给出的量级是**潜在 20–30% 提升**，不是室温超导的实验证实。低压部分的 DOS 标度结果还被作者明确限定：该方法不应视为精确预测，而应看作相应估计的下界。[Xie 等原文镜像](kimi-cite://web?url=https%3A%2F%2Fquantum.emorychem.science%2Fwp-content%2Fuploads%2F2025%2F07%2FnpjComputMater.11.227.pdf&text=should%20not%20be%20regarded%20as%20an%20accurate%20prediction "citation")

由此得到三项修订要求：

1. 将“2023 年提出 Floquet-DFPT”明确标为 **2023 年 arXiv 预印本**，并另注 **2025 年期刊正式发表**，不得把两个时间点混为同一事件。arXiv:2312.12706 的 v1 日期为 2023-12-20，期刊 DOI 页面为 2025 年。[arXiv:2312.12706](kimi-cite://web?url=https%3A%2F%2Farxiv.org%2Fabs%2F2312.12706&text=Wed%2C%2020%20Dec%202023 "citation")，[npj Computational Materials](kimi-cite://web?url=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs41524-025-01725-z&text=In%20this%20paper%2C%20we%20present%20a%20dynamical%20method "citation")
2. 将 285 K、301 K 标为特定条件下的 DOS 标度估计及下界，不写成无条件、精确的 $T_c$ 预测。
3. 不把 LaH₁₀ 的计算直接外推为其他氢化物或其他材料的同级证据。

## 四、需要优先修复的内部问题

### 4.1 LSCO 的频率与波长不能混写

第 3.2.3 节写 LSCO 驱动频率为约 10–100 THz，第 7.1 节又写约 800 nm（约 375 THz）。这两个量级不能作为同一驱动条件并列，必须回到原文分别固定泵浦频率、波长、脉宽和强度。[floquet_superconductivity_deep](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cfloquet_superconductivity_deep.md&line=199&text=10-100%20THz "citation")，[floquet_superconductivity_deep](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cfloquet_superconductivity_deep.md&line=580&text=800%20nm "citation")

### 4.2 FeSe/STO 与 FeSe₀.₅Te₀.₅不是同一样品

第 3.3.2 节先讨论 FeSe 单分子层／SrTiO₃，随后用 Isoyama 等 FeSe₀.₅Te₀.₅的结果支撑。两者化学组成、结构和实验条件不同，不能用后者直接证明前者的单层界面结论。应分设样品行并分别记录来源，或删除不对应的界面超导推断。[floquet_superconductivity_deep](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cfloquet_superconductivity_deep.md&line=234&text=FeSe "citation")，[floquet_superconductivity_deep](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cfloquet_superconductivity_deep.md&line=238&text=Isoyama "citation")

### 4.3 YH₁₀ 的 350–400 K 缺少对应推导与来源

第 4.2.1 节以“类似 LaH₁₀”一句推出 YH₁₀ 可达 350–400 K，但没有给出独立的 Floquet-DFPT 结果、压力、泵浦条件或原始论文。该数值必须撤回，或降级为没有独立证据的外推猜想，不能与 Xie 的 LaH₁₀ 结果并列。[floquet_superconductivity_deep](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cfloquet_superconductivity_deep.md&line=332&text=350-400%20K "citation")

### 4.4 引用可追踪性不足

文中有“相关预印本”、arXiv 号留空和缺少卷期页或 DOI 的条目。文末却称所有引用均标注 arXiv 号或期刊信息，这一自述过强。每条定量主张至少需要作者、题名、年份、DOI／arXiv、具体图表或页码；不能用作者—年份近似匹配代替原文。

### 4.5 缺少真正的结论与局限章节

全文在术语表和文档说明结束，没有独立的结论、证据等级汇总和局限章节。建议新增“结论与边界”，分别列出：

- 稳态 Floquet 理论结果；
- 瞬态光诱导实验响应；
- 连续波等离子体调制；
- 高压氢化物第一性原理预测；
- 尚未复现、存在争议或只有二手来源的条目。

## 五、这篇文章是否代表新方向

**作为综述，它不是独立的新物理方向；作为研究基础设施，它可以派生三个有边界的方向。**

### 方向 A：驱动超导的主张—证据图谱（近期可执行）

把每个数值绑定到材料、样品结构、压力、驱动波形、泵浦条件、观测量、原始图表和证据类型。该方向首先解决可追踪性，不预先支持或反对室温超导。

### 方向 B：有限 Floquet-BdG 模型的 0／π 模验证（独立研究候选）

选择一个有限、可精确对角化的模型，显式计算准能量、0 和 $\pi$ 模、有限尺寸标度及驱动截断收敛。它可与现有 p+ip 符号治理共享约定，但不得直接把静态陈数或旧图当作 Floquet 证明。

### 方向 C：从二能级 HFE 到相互作用模型的收敛基准（独立研究候选）

现有脚本已验证二能级例子。下一步可增加相互作用 BdG 或配对自洽模型，比较精确周期传播、Magnus 截断和稳态占据假设，记录误差随 $\Omega$、驱动强度和截断阶数的变化。通过前必须另行设计，不把本报告当作研究完成。

## 六、建议的修订与验收顺序

1. **P0：修正来源与时间线**：区分 Xie 的 2023 年 arXiv 预印本与 2025 年期刊正式发表，补齐 arXiv、DOI 和原文图表位置。
2. **P0：拆分样品与模型**：FeSe/STO 和 FeSe₀.₅Te₀.₅分开；LSCO 的频率与波长回源。
3. **P0：撤回或降级无来源数值**：YH₁₀ 的 350–400 K 不得保留为预测结论。
4. **P0：加入结论与局限**：明确脚本不覆盖材料预测，LaH₁₀ 标度值不是精确预言。
5. **P1：完成逐条引用表**：其余实验数字未经原始来源核验前统一标为“未核实”。
6. **P1：再选择数值方向**：A 是审计基础，B／C 各自需要独立规格、失败测试和验证协议。

本轮没有修改原论文，也没有把其他未检索条目认定为虚假；它们当前只是**未核实或内部不一致**。只有 Xie／LaH₁₀ 的来源已在本次检索中直接核对。
