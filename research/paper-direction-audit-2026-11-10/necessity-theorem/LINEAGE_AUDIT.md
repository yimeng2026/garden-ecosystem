# “室温超导必然性”版本血缘与反例传播审计

> 日期：2026-11-10
> 范围：`manuscript.tex`、Science、Nature、arXiv 与主模板五个版本；判断同源错误、独立方向和未竟工作，不把版本数量当成研究成果数量。

## 一、总裁决

这五个文件属于**同一错误研究纲领的不同版本**，不构成五条独立新方向。核心问题都是“强耦合、优化声子、降维等条件共同保证 \(T_c>300\) K”，而已有反例表明该结论不能由所用公式推出。

| 版本 | 当前角色 | 主要问题 | 独立新方向？ |
|---|---|---|---|
| `manuscript.tex` | 完整推导草案 | 内部温度反例、Coulomb 算术、Kiessling 常数、未证映射 | 否，中心命题被反例推翻 |
| Science | 完整方法叙事版 | 同一段先算 148 K，随后直接声称超过 300 K | 否，直接自相矛盾 |
| Nature | 短格式宣传版 | 用 300 K 必然性概括未成立推导 | 否，继承同一错误命题 |
| arXiv | 技术扩展版 | 完整证明和参考文献仍是占位 | 否，且未完成 |
| 主模板 | A/B/C 集成框架 | 大量待填段，仍预设形式证明成立 | 否，只是未完成模板 |

## 二、Science：最直接的内部矛盾

Science 版在证明中先计算 $\lambda=2$、$\mu^*=0.15$ 时的 $T_c^{\min}\approx148$ K，紧接着声称数值评估超过 300 K。148 K 与 300 K 之间没有任何补充推导，不能靠一句单调性描述跨过。[03-Science版本](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Corganized%5C02-%E4%B8%BB%E8%AE%BA%E6%96%87%5C03-Science%E7%89%88%E6%9C%AC.md&line=92&text=148 "citation")

这不是单位换算问题：同段已经使用 100 meV≈1160 K。真正的问题是**把低于 300 K 的下界误写成超过 300 K 的结论**。

## 三、Nature 与 arXiv：同一命题的压缩和扩展

Nature 版直接声称在相关参数条件下下界超过 300 K，但没有给出能修复反例的新推导。[02-Nature版本](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Corganized%5C02-%E4%B8%BB%E8%AE%BA%E6%96%87%5C02-Nature%E7%89%88%E6%9C%AC.md&line=40&text=exceeds%20300 "citation")

arXiv 版保留同一必然性命题和 $\mu_c^*\approx0.15$ 的错误算术，同时把“Step 2–6 完整证明”留作指向 .tex 的占位；参考文献也仍是“50+ 条待补”。[04-arXiv版本](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Corganized%5C02-%E4%B8%BB%E8%AE%BA%E6%96%87%5C04-arXiv%E7%89%88%E6%9C%AC.md&line=168&text=Step%202-6 "citation")，[04-arXiv版本](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Corganized%5C02-%E4%B8%BB%E8%AE%BA%E6%96%87%5C04-arXiv%E7%89%88%E6%9C%AC.md&line=290&text=Complete%20bibliography "citation")

因此 arXiv 的“完整技术版”不能视为更可靠的独立证明。

## 四、主模板：不是第六种理论

主模板虽将作者写为乔瀚，但理论结构、证明、材料预测、验证、图件、数据和代码仍大量待填。其摘要和结论仍预设“形式证明成立”，所以应在整合前撤回或降级，而不是作为新理论继续扩写。[01-主论文](kimi-cite://md-line?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Corganized%5C02-%E4%B8%BB%E8%AE%BA%E6%96%87%5C01-%E4%B8%BB%E8%AE%BA%E6%96%87.md&line=50&text=Theorem%2FProof%20structure "citation")

Science、Nature 和 arXiv 则仍保留作者与单位占位，均不能按已完成投稿稿处理。

## 五、计算与实验证据边界

`organized/02-主论文` 目录目前只有四份 Markdown，没有配套计算脚本、结构文件、求解输出或收敛日志。VASP、PHONOPY、EPW 等计算只以方法叙事出现，当前无法据此验证其已实际执行。

因此：

- “完成了某种 DFT／EPW 计算”与“有相应输入、输出和收敛证据”必须区分；
- H$_3$S、LaH$_{10}$、YH$_6$ 等预测表不能反推必然性定理成立；
- 未逐项回源的材料参数继续标为未核实，不借此全部判假。

## 六、统一未竟工作

1. **共享反例处置**：所有版本撤回或降级“必然超过 300 K”的中心命题，不能只修 `manuscript.tex`。
2. **共享参数核对**：修正 $\mu_c^*(2)=0.3$、Kiessling 常数角色和各版本不一致的参数表。
3. **临界流形**：用同一组公式与单位计算 300 K 边界，避免不同版本各自宣称不同必然区。
4. **降维映射**：先证明或否证 $\eta$ 与 $\mu^*_{\mathrm{eff}}$ 的关系，再决定是否保留降维条件。
5. **证据补齐**：补作者、参考文献、原始计算输入输出和逐条实验来源，否则保持草案状态。

## 七、建议的统一路线

- 只设一个“反例与临界流形”研究项目，不为 Science、Nature、arXiv 分别立项。
- 在各版本保留历史原文的同时，用勘误表链接 FE-18 和数值反例。
- 若未来得到新的条件化结论，先通过三组反例和边界测试，再同步回所有版本。
- 在新证明通过前，任何版本都不得继续使用“形式证明已建立”“共同保证”或“实验已验证必然性”作为当前结论。

原文件均未修改；本报告完成的是血缘与反例传播审计，不是论文修订完成。
