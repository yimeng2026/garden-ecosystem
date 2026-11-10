# 实验验证与材料预测：原始来源定位

## Grockowiak 等，Hot Hydride Superconductivity Above 550 K

- URL：https://www.frontiersin.org/journals/electronic-materials/articles/10.3389/femat.2022.837651/full
- DOI：10.3389/femat.2022.837651
- 原文摘要：初始 Tc 为 294 K；后续热循环使 Tc onset 不可逆地达到 556 K。
- 原文结构角色：扭曲的 LaH10 骨架，暗示 La 和／或 H 位点被取代，形成三元或更高阶化合物。
- 原文边界：没有 Meissner 测量；材料持续发生化学变化，380 K 以上无法获得可靠 H–T 相图；还存在非零电阻背景、混合相与电极／污染问题。
- 审计角色：真实论文和真实实验宣称，但不能并入二元 LaH₁₀ 的常规验证百分比，也不能把 556 K 写成独立确认。

## Zeng 等，Superconductivity in infinite-layer nickelate La1−xCaxNiO2 thin films

- URL：https://pmc.ncbi.nlm.nih.gov/articles/PMC8856608/
- 原文摘要：未掺杂和低掺杂 La1−xCaxNiO2 薄膜从 300 K 到 2 K 均绝缘；超导穹顶位于 0.15 < x < 0.3。
- 原文结果：0.2 ≤ x ≤ 0.27 的样品表现超导；x ≥ 0.3 过掺杂区正常态电阻上升并呈弱绝缘行为。
- 审计角色：必须把化学式和掺杂范围写清，不能把未掺杂 LaNiO2 写成 20–40 K 已验证超导体。

## Nakanishi、Ishikawa、Shimizu，First-principles study on superconductivity of P- and Cl-doped H3S

- URL：https://arxiv.org/html/1804.08224v3
- 原文摘要：6.25% P 掺杂在 200 GPa 将 Tc 从 189 K 提高到 212 K；6.25% Cl 掺杂将其降至 161 K。
- 原文结果表：12.5% Cl 掺杂在 200 GPa 时为 136 K；Cl 掺杂削弱超导，但降低 Im-3m 相的稳定压力。
- 审计角色：不能用来支持 H3S0.8Cl0.2 的 320 K 提升预测；也不能把 Cl 降低压力误写成提高 Tc。

## 文内公式独立复算

公式：`T_c = (ω_log / 1.2) exp[-1.04(1+λ)/(λ-μ*(1+0.62λ))]`，不另加 f1/f2。

- H3S 表内参数 ω_log=1200 K、λ=2.0、μ*=0.13：复算约 161.081843791778823 K，表中写 203 K。
- H-S-Cl 表内参数 ω_log=1500 K、λ=2.5、μ*=0.12：复算约 237.894818964651591 K，表中写 320 K。

复算只证明“表内参数—公式—结果不一致”，不替代真实 Allen–Dynes 修正、Eliashberg 求解或第一性原理计算。

## 验证度百分比与星级

两份文档给出 92%、88%、45% 等验证度和星级／9.5/10 等排序，但没有给出指标定义、权重、样本集、误差模型或复算公式。当前只能标为无计算规则的研究治理标签，不能称为定量科学验证结果。
