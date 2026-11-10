# 主论文与手册审计：原始来源定位

## Song 等正向实验预印本

- arXiv:2510.01273，v2：2025-10-06。
- URL：https://arxiv.org/abs/2510.01273
- 本地 PDF：`song-2510.01273.pdf`
- 本地全文：`song-2510.01273-fulltext.txt`
- lines 21–28：实验合成、271–298 K／195–266 GPa、零电阻、磁场抑制、XRD、13 次可重复实验。
- lines 150–162：Meissner 的重要性与磁场抑制；不是直接 Meissner 测量。
- lines 258–263：作者把高于 200 GPa 的直接磁测量列为未来工作。

## Semenok 等负向复现预印本

- arXiv:2605.29985，v2：2026-08-20。
- URL：https://arxiv.org/abs/2605.29985
- 本地 PDF：`semenok-2605.29985.pdf`
- 本地全文：`semenok-2605.29985-fulltext.txt`
- lines 18–27：7 次实验未成功、250–280 GPa 下未见 245–300 K 超导、前驱体可能关键。
- lines 38–56：理论上讨论 Tc>300 K at 300 GPa；不是对全部理论可能性的否定。
- lines 405–413：可重复性、7 次失败与前驱体工程。

## Nature 卷页错配

- Crossref API：https://api.crossref.org/works/10.1038/s41586-024-07036-5
- DOI：`10.1038/s41586-024-07036-5`
- 实际题名：`Twisted-layer boron nitride ceramic with high deformability and strength`
- 实际期刊卷页：Nature 626, 779–784 (2024)
- 裁决：该卷页不是 LaSc₂H₂₄ 论文。手册 [C1] 是确认的书目错配。

## PNAS 理论预测

- URL：https://www.pnas.org/doi/10.1073/pnas.2401840121
- PNAS 121(26), e2401840121。
- 167 GPa 预测最高 316 K；250 GPa 预测最高 331 K。
- 该论文的理论预测角色不变，但不能用它否定或替代后续实验预印本。

## 2026 年方法综述的边界

- URL：https://iopscience.iop.org/article/10.1088/1361-648X/ae7ccd
- 题名：Hydrogen-rich superconductors under extreme pressure: challenges, progress, and opportunities。
- 2026-07-10。
- 原文同时记载 Song 的 298 K 报告，并明确写出 `While independent verification of experiments is obviously critical`，支持“独立验证仍关键”，不是独立正向复现证明。

## 临界流形数值反例

- 来源：`.worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json`
- SHA-256：`f9438c770c1125c68b42a67778458d551f3694d1954b112bdf61d6942bac970b`
- 三个锚点温度均低于 300 K；936 组根、38,376 个直接点分类不一致为 0。
- 只适用于 simplified Allen-Dynes/McMillan formula，f1=f2=1；不是材料预测，不否定完整 Eliashberg 理论。
