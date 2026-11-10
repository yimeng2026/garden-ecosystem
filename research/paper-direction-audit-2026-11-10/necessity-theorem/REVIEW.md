# “室温超导必然性”稿件：数值反例与方向审计

> 日期：2026-11-10
> 对象：`toe-sylva-audit/papers/room_temp_sc/manuscript.tex`
> 范围：核心定理、公式自洽性、Kiessling 常数、证据结构；不是对全部材料数据和参考文献的终审。

## 一、结论

当前“强耦合、优化声子和降维三个条件共同保证 $T_c>300$ K”的必然性定理**不能成立，且被稿件自己使用的 Allen–Dynes 公式直接反驳**。应撤回“形式证明”“必要条件已建立”等表述，而不是仅做文字润色。

**优先级：P0（中心命题为假或与自身推导冲突）。** 这不等于否定强耦合 Eliashberg 研究，也不等于否定具体氢化物数据；它意味着这些数据不能自动升级为当前三条件的普适必然性证明。

## 二、正确单位下的三个直接反例

计算统一采用 $1\,\mathrm{meV}=11.6\,\mathrm K$，并使用稿件的公式

$$
T_c=\frac{\omega_{\log}}{1.2}\exp\!\left[-\frac{1.04(1+\lambda)}{\lambda-\mu^*(1+0.62\lambda)}\right].
$$

独立重算结果保存于 `counterexample.json` 和 `counterexample.log`。

| 参数组合 | 稿件值附近 | 独立重算 $T_c$ | 与 300 K 的关系 |
|---|---:|---:|---|
| $\lambda=2,\ \omega_{\log}=100$ meV，$\mu^*=0.15$ | 148 K | **148.243 K** | 明显低于 300 K |
| $\lambda=2,\ \omega_{\log}=100$ meV，$\mu^*=0.10$ | 166 K | **166.850 K** | 明显低于 300 K |
| $\lambda=2.5,\ \omega_{\log}=140$ meV，$\mu^*=0.10$ | 267 K | **267.453 K** | 明显低于 300 K |

第三组参数满足稿件声称的“内部点”特征 $\lambda>2$ 且 $\omega_{\log}>100$ meV，却仍未达到 300 K。因此，“任何严格内部组合超过 300 K”不是证明，而是与公式矛盾的断言。[manuscript](kimi-cite://text?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cmanuscript.tex&text=any%20strictly%20interior%20combination%20exceeds%20300%20K "citation")

即使接受稿件另行给出的“完整 Eliashberg 边界值 285 K”，它也仍然低于 300 K，不能挽救必然性结论。

## 三、另外两个独立的数学问题

### 3.1 Coulomb 阈值的算术不正确

稿件定义

$$
\mu_c^*(\lambda)=\frac{0.3}{1+0.1(\lambda-2)}.
$$

代入 $\lambda=2$ 得

$$
\mu_c^*(2)=\frac{0.3}{1+0.1(2-2)}=0.3,
$$

而稿件写为约 0.15。该错误会改变后续对允许参数域和临界温度的判断。[manuscript](kimi-cite://text?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cmanuscript.tex&text=0.15 "citation")

### 3.2 Kiessling 常数的角色写错

稿件将 $C_\infty\approx0.371$ 称为渐近常数。Kiessling 原文给出的 sharp constant 是 $0.1827262477\ldots$，而非 0.371；原文另用约 2.034 作为非最优上界与该 sharp constant 的倍率。0.371 接近这一乘积，但不能未经说明替换原常数的定义和最优性地位。[Kiessling 等原文](kimi-cite://web?url=https%3A%2F%2Farxiv.org%2Fpdf%2F2409.00532&text=0.1827262477 "citation")

强耦合渐近增长也不能替代有限参数点穿越 300 K 的证明；还必须检查谱支撑、参数域和实际下界。

## 四、推导链还缺哪些必要环节

1. **$\eta$ 与 $\mu^*_{\mathrm{eff}}$ 的关系未证。** 稿件给出降维参数定义后，直接声称准二维屏蔽使 $\mu^*_{\mathrm{eff}}\lesssim0.10$，没有推导映射、适用范围或反例排除。
2. **严格不等式与边界混用。** 三个条件使用 $>$，证明却依赖边界点和单调外推；即使边界接近，也必须给出统一的下界，而不是假定越过后自动超过 300 K。
3. **单调性被误当穿越性。** $T_c$ 随参数增加并不蕴含任意内部点都超过 300 K；需要计算 $T_c=300$ K 的临界流形。
4. **数据被用来验证尚未成立的模型。** 具体氢化物数据可以支持个别材料研究，但不能自动验证三条件的普适必然性。
5. **数值复算没有覆盖核心命题。** 现有通用 BCS／Allen–Dynes 工具不验证 $\eta$、Coulomb 映射、Kiessling 下界或 300 K 穿越。

## 五、文档与证据状态的附加风险

- 作者和单位仍是注释占位，PACS 未定，材料预测与计算方法均写有 `To be imported from B路`，不能按完成稿处理。[manuscript](kimi-cite://text?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cmanuscript.tex&text=To%20be%20imported%20from%20B "citation")
- “2026 共识验证标准”列出五条标准，但未给出可核的共识来源；不能称为社区统一规范。[manuscript](kimi-cite://text?path=C%3A%5CUsers%5C%E4%B8%80%E6%A2%A6%5CDocuments%5Ckimi%5Cworkspace%5Ctoe-sylva-audit%5Cpapers%5Croom_temp_sc%5Cmanuscript.tex&text=five%20independent%20criteria "citation")
- 氢化物的 $\lambda$、$\omega_{\log}$、同位素系数和实验对应必须逐项回源，不能用“已验证”总称覆盖。
- LaSc$_2$H$_{24}$、同位素表和其他实验数字未在本次逐项终审，当前只标为未核实，不据此判假。

## 六、可保留并发展的新方向

### 方向 A：从“必然性定理”改为临界流形研究

计算并验证

$$
\mathcal M_{300}=\{(\lambda,\omega_{\log},\mu^*,\eta):T_c=300\ \mathrm K\}.
$$

应明确哪些参数域位于 300 K 以上、以下及无法判定处。这比“强耦合必然超过 300 K”更忠实于公式，也能保留参数设计价值。

### 方向 B：证明或否证降维—屏蔽映射

将 $\eta$ 与 $\mu^*_{\mathrm{eff}}$ 的关系作为独立命题，给出可计算模型、适用条件和反例。若无法建立映射，应将 $\eta$ 从必然性条件中移除，而不是继续用它替代独立的 Coulomb 参数推导。

### 方向 C：建立最小反例优先的 Lean／数值验收

先机器检查 $\mu_c^*(2)=0.3$、三个反例和 $T_c<300$ K，再讨论任何更一般的定理。若以后给出新命题，必须先通过这些负例门禁，不能先写 Lean 骨架再反推结论。

## 七、建议处置

1. 撤回摘要、定理和结论中的“形式证明”“必要条件”“共同保证”等措辞，标为中心命题反例。
2. 保留正确单位下的数值计算，不用 148／166／267 K 去支撑超过 300 K 的结论。
3. 修正 $\mu_c^*(2)=0.3$ 与 Kiessling 常数角色，并重新审查参数域。
4. 将全文降级为**带反例的强耦合研究草案**，先完成临界流形和降维映射，再考虑恢复任何条件化定理。
5. 所有材料数据另行逐条回源；未核实数据不得继续作为该定理的“实验验证”。

原稿件未修改。本报告只证明当前核心命题存在直接反例，不主张已经否决所有室温超导研究路线。
