# Floquet 综述 P0 修订：主张—来源对照表

> 日期：2026-11-10
> 原则：能回到原始来源的给出明确出处；未核实的保留未核实，不把检索缺失误写为证伪，也不把不同样品、模型或证据等级拼接为同一结论。

## 一、逐条对照

| 主张 | 综述位置 | 原始证据 | 裁决与修订动作 |
|---|---|---|---|
| Floquet-DFPT 于 2023 年提出 | §1.3 | arXiv:2312.12706 的 v1 确为 2023-12-20；期刊正式发表为 2025 年。[arXiv:2312.12706](kimi-cite://web?url=https%3A%2F%2Farxiv.org%2Fabs%2F2312.12706&text=Wed%2C%2020%20Dec%202023 "citation")，[npj Computational Materials](kimi-cite://web?url=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs41524-025-01725-z&text=In%20this%20paper%2C%20we%20present%20a%20dynamical%20method "citation") | **分别标注 2023 预印本与 2025 正式发表**，并补 arXiv 和 DOI `10.1038/s41524-025-01725-z`；不是简单把 2023 改成 2025。 |
| LaH₁₀ 在低压下达到 285／301 K | §4.1.2 | Xie 原文说明 DOS 标度不是精确预测，而是相应下界估计。[Xie 等原文镜像](kimi-cite://web?url=https%3A%2F%2Fquantum.emorychem.science%2Fwp-content%2Fuploads%2F2025%2F07%2FnpjComputMater.11.227.pdf&text=should%20not%20be%20regarded%20as%20an%20accurate%20prediction "citation") | 改为**特定条件下的 DOS 标度下界估计**，不得写成无条件精确值。 |
| Giorgianni 的 Nat. Phys. 15, 341 可支撑 LSCO 瞬态超导 | §3.2.2 | 该文实际研究多带超导体 **MgB₂** 的 Leggett 模，不是 LSCO。[NASA ADS](kimi-cite://web?url=http%3A%2F%2Fui.adsabs.harvard.edu%2Fabs%2F2019NatPh..15..341G%2Fabstract&text=multiband%20superconductor%20MgB2 "citation") | **来源与材料错配**。从 LSCO 段移除该引文，LSCO 结论另找对应原始实验，不能换标题后继续使用。 |
| LSCO 驱动为约 10–100 THz，又为约 800 nm | §3.2.3、§7.1 | 综述内部同时写两个不同量级；本次没有取得能统一二者的原始泵浦参数。 | 标为**内部不一致且待核**，分别固定波长、频率、脉宽和电场；不得用“近红外”笼统覆盖。 |
| Isoyama 的结果可证明 FeSe/STO 单层界面增强 | §3.3.2 | Isoyama 原文明确样品为 **FeSe₀.₅Te₀.₅薄膜**。[Communications Physics](kimi-cite://web?url=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs42005-021-00663-8&text=thin%20film%20of%20an%20iron%20chalcogenide%20FeSe0.5Te0.5 "citation") | **拆分样品**。FeSe₀.₅Te₀.₅单独引用；FeSe/STO 必须使用另一对应来源，不能共享同一实验结论。 |
| YH₁₀ 经类似 Floquet 外推可达 350–400 K | §4.2.1 | Xie 原文虽考察 YH₁₀ 等其他氢化物，但明确并非所有体系都超过室温；现有独立静态理论值常见为 305–326 K，且实验上未观察到 fcc-YH₁₀。[Xie 等原文镜像](kimi-cite://web?url=https%3A%2F%2Fquantum.emorychem.science%2Fwp-content%2Fuploads%2F2025%2F07%2FnpjComputMater.11.227.pdf&text=not%20all%20of%20these%20hydrides%20achieve%20superconductivity%20above%20room%20temperature "citation")，[YH₁₀ 实验研究](kimi-cite://web?url=https%3A%2F%2Farxiv.org%2Fpdf%2F1909.10482&text=305-326 "citation") | **撤回 350–400 K**。静态理论预测、Floquet 估计和实验未见样品必须分三行登记，不能合并成更高数值。 |
| NbSe₂ 的连续波等离子体调控可直接等同 Floquet 稳态工程 | §1.2、§3.3.1 | 原始论文题名确为通过 plasmon coupling 可逆调制薄膜 NbSe₂ 超导性。[Nature Communications](kimi-cite://web?url=https%3A%2F%2Flink.springer.com%2Farticle%2F10.1038%2Fs41467-024-50452-4&text=Reversible%20modulation%20of%20superconductivity%20in%20thin-film%20NbSe2%20via%20plasmon%20coupling "citation") | 保留可逆调制事实，但先标为**连续波近场调控**；是否满足所用 Floquet 稳态定义需另行论证，不能自动归类。 |
| `verify_rtsc.py` 的 3/3 通过可支撑综述定量主张 | 配套脚本 | 实际退出码 0，只有 BCS、Allen–Dynes 和二能级 HFE 三个模块。[run](kimi-cite://text?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Cgarden-ecosystem%5Cresearch%5Cpaper-direction-audit-2026-11-10%5Cfloquet-superconductivity%5Crun.log&text=3%2F3%20modules%20passed "citation") | 仅登记**通用数值工具箱通过**，材料级数值继续逐条回源。 |

## 二、统一修订字段

后续每条定量主张必须使用同一组字段，不允许只写“某某等，某年”：

| 字段 | 必填内容 |
|---|---|
| 样品与结构 | 化学式、薄膜／单层／体相、晶相、压力及衬底 |
| 驱动条件 | 连续波／脉冲、频率或波长、脉宽、场强、注量、极化 |
| 理论模型 | 稳态 Floquet、瞬态光泵浦、静态 DFPT、DOS 标度、BCS／Allen–Dynes 等 |
| 观测量 | 电阻、THz 电导、临界电流、能隙、准能量或计算所得 $T_c$ |
| 来源定位 | 作者、题名、年份、DOI／arXiv、具体页码或图表 |
| 证据等级 | 实验、理论计算、下界估计、外推猜想、二手综述、未核实 |
| 反例与限制 | 加热、寿命、材料替代、模型适用范围、未复现或争议 |

## 三、剩余未决项

- LSCO 的真实泵浦条件及其对应实验结论仍需原文核对。
- FeSe/STO 单层界面需要与 FeSe₀.₅Te₀.₅完全不同的来源链。
- K₃C₆₀、YBCO、NbSe₂ 的其余参数尚未逐条终审，不能因本表而自动转为已核实。
- 原论文尚未修改；本表是 P0 修订输入，不是修订完成证明。
