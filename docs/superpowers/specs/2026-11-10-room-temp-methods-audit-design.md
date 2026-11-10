# room_temp_sc 方法与形式化小组：证据角色和未竟工作审计设计

- 日期：2026-11-10
- 分支：`audit/room-temp-methods-batch`
- 审计目录：`research/paper-direction-audit-2026-11-10/room-temp-methods/`
- 对象：五份 room_temp_sc 文档，附查一份独立 Lean 文件
- 本批边界：只生成审计报告，不直接改写五份原文，不新增材料预测、全参数拟合或 Lean 证明

## 1. 来源冻结与只读纪律

以工作区 `toe-sylva-audit/` 中下列文件的当前内容为审计对象，构建时重新计算 SHA-256；若哈希变化则停止生成，防止证据和报告错位。

| ID | 相对路径 | 冻结 SHA-256 |
|:--|:--|:--|
| `latest_digest` | `papers/room_temp_sc/latest_research_digest.md` | `41aea15ed19c68375f29877f7e22deba22394757df178cb67ca827a458a0aa75` |
| `floquet_notes` | `papers/room_temp_sc/organized/13-资料收集-Floquet工程LaH10.md` | `37b5436dc39bada84c3a520943ea94515d5d08e75c27e808aba5070059d48ab9` |
| `eliashberg_notes` | `papers/room_temp_sc/organized/15-资料收集-Eliashberg理论边界.md` | `841c1954c7fea9c41e3179476602c64b47eca936643f383e24215284324d0a20` |
| `lean_markdown` | `papers/room_temp_sc/organized/07-形式化代码/01-Lean形式化代码.md` | `c171f6e5d5e5b6547bddc88d94138b9dc0a87d8c3a6ec59ff696e35746f59141` |
| `si_template` | `papers/room_temp_sc/organized/10-技术文档/06-补充信息.md` | `9d54064ba6089c82de39ddef90afeb82e47d511f95b35dd0490ee50aef63d97f` |
| `lean_standalone` | `papers/room_temp_sc/room_temp_sc_Formalization.lean` | `1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439` |

这些文件属于同一 room_temp_sc 研究纲领，但承载五种不同的方法角色。`research_program_count=1`，不得按五份文档申报五个独立新理论，也不得按章节数膨胀方向数。

## 2. 审计方法与证据等级

采用“证据角色—可复核事实—未竟工作”三层审计：

1. **证据角色**：原始研究、理论预测、数值近似、严格数学界、经验公式、形式化草案、计算模板分别标记。
2. **可复核事实**：数值、卷期、文章号、日期和适用条件必须回到原始论文或官方摘要；检索不到的内容只标“未核实”，不判假。
3. **未竟工作**：把局部错误修正、方向发展与实际计算/证明任务分开，不把纠错本身包装成科学突破。

本地 Xie 全文用于逐行核对高压和低压结果；APS、PNAS 官方页面用于核对 DMRG 和 LaSc₂H₂₄。Nature 网页若受浏览器验证阻挡，不影响使用已下载的同一 DOI 正式 PDF。

## 3. 五个候选方法方向

### A. Floquet 驱动超导的证据分层

- **方向角色**：非平衡第一性原理与近似下界的研究方向，不是实验验证成果。
- **P0 数据错配**：资料表将 220 GPa→322 K、250 GPa→320 K 写反。Xie 正式论文是 220 GPa：258→320 K；250 GPa：237→322 K，均在 E₀=80 mV/Å 的给定泵浦条件下估计。
- **下界角色**：150 GPa：249→285 K；200 GPa：240→301 K 来自 DOS-scaling。原文明确其不是准确预测，而是 Floquet-DFPT 结果的下界，不能与高压直接计算混成同等级精确值。
- **外推边界**：原文明确并非所有被考察氢化物都超过室温；不得从 LaH₁₀ 升格为普遍规律。
- **未竟工作**：样品与泵浦可实现性、热效应、非平衡分布、损伤窗口、独立复算和实验验证。

### B. Eliashberg 严格边界与经验公式分工

- **方向角色**：数学物理严格界与材料估算之间的接口，不是“室温超导必然性”证明。
- **常数分工**：sharp constant `0.1827262477…` 与约为其 `2.034` 倍的非最优渐近上界系数（乘积约 `0.371665…`）不得混写。
- **公式分工**：Kiessling 的严格下界、非最优上界与 Allen–Dynes 经验公式各自保留假设和适用域；不得用经验公式替代严格证明，也不得把非最优上界当 sharp constant。
- **未竟工作**：统一符号和归一化、核对每个不等式的假设、建立可编译的变分命题链，再谈材料级后果。

### C. Lean 草案和证明债务

- **方向角色**：可发展的形式化基础设施，不是已经完成的机器证明。
- **Markdown 草案**：保留大量 `admit`/`sorry`，首行已标“框架草案”。构建器统计证明债务，但不将字符串计数冒充证明困难度。
- **独立 Lean 文件**：至少三个显式证明位 `sorry`，对应 `allenDynes_weak_coupling_limit`、`bcs_isotope_effect`、`floquet_enhanced_tc`。
- **陈述问题**：弱耦合条目把 `λ → 0` 和逻辑箭头当作 Lean 类型/命题使用，不是正确的极限或等式表述；Floquet 条目自身注释给出 `CONFIDENCE: 0.05`。
- **验证边界**：本批不运行 Lean 编译，不声称构建通过；不新增 `axiom`、`postulate`、证明位 `sorry` 或空真定理。
- **未竟工作**：先修正命题类型和物理假设，再逐项清偿证明并记录 `#print axioms`，最后才讨论机器验证级别。

### D. 最新综述的书目修正与未核实内容

- **DMRG**：arXiv:2211.06322 对应 Physical Review Letters 133, 256003，2024-12-19，DOI `10.1103/PhysRevLett.133.256003`；不是 132, 066002。结果限于宽度至多 W=6 的圆柱，最低到 T/J≈0.06；t′/t>0 时最高特征温度约 0.15J，t′/t<0 时配对更弱。不得写成铜氧化物高温超导已被完整解释。
- **LaSc₂H₂₄**：PNAS 121(26), e2401840121；167 GPa 预测最高 316 K，250 GPa 预测最高 331 K；非谐计算使动力学稳定延伸到 150 GPa。它是理论预测，不是当前实验纪录。
- **Lean 外部指标**：15,000 行、845 证明项、127 实例、43 秒及“完整陈数基础设施”缺少精确实现和构建记录，本批只标“未核实”。
- **其余段落**：未逐项回源的实验和文献陈述不一并判真或判假，留给后续审计。

### E. SI 模板与缺失计算资产

- **方向角色**：可复现计算补充材料的待建清单，不是研究完成品。
- **当前状态**：存在 `[To be imported]`、待补充表、未指定软件与空泛数据目录；没有可审计的 DFT 输入、声子谱、收敛日志或材料级结果。
- **禁止升格**：模板中的文件列表不证明这些文件实际存在，不能把 SI 模板写成计算已完成。
- **未竟工作**：冻结材料结构和输入、记录软件版本与赝势、完成 k/q/截断能收敛、保存声子和 Eliashberg 输出、建立独立重跑脚本与哈希清单。

## 4. 范围外缺陷登记

审计检索中若实际读到范围外高风险行，应在 `review.json.out_of_scope_findings` 和报告附表中登记路径、行号、风险与后续动作；本批不修改来源文件，也不把未回源内容判为虚构。

至少登记：

- `organized/08-手册章节/04-第6章_未来展望.md:222,372,384-385` 将 LaSc₂H₂₄ 写成实验实现并附 Nature 文献，和本批已核 PNAS 理论预测角色冲突，列为 P0 候选，待独立回源。
- `organized/02-主论文/02-Nature版本.md`、`03-Science版本.md`、`04-arXiv版本.md` 的“必然性/严格导出/材料预测”高强度措辞与当前 Lean 草案、SI 模板不匹配，列为后续主论文批次的证据角色复核任务。
- `organized/02-主论文/01-主论文.md` 仍有 `[To be imported]`，后续不得当作完整主论文交付。

这些附带发现不扩大本批五份文档的完成范围。

## 5. 交付物和验收合同

交付：

- `review.json`：唯一证据对象，含来源哈希、一个研究纲领、五个方法方向、书目更正、原始证据、范围外登记和开放边界。
- `REVIEW.md`：中文审计正文，明确更正、证据角色、未竟工作和优先级。
- `REVIEW.docx`：由同一 JSON 生成，含原生目录域、中文页眉、PAGE 页码、真正表格和原生公式。
- `test_room_temp_methods_audit.py`：提供 `run_all_tests()`；覆盖压力映射、DOS 下界、DMRG、LaSc₂H₂₄、Kiessling 常数、Lean 债务、SI 模板、来源哈希和 Word 结构。
- `run.log`：记录实际命令、退出码和关键输出，包含有意 RED 与最终验证。

必须显式为 false 的边界：

```json
{
  "global_fit": false,
  "material_prediction": false,
  "lean_proof_verified": false,
  "dft_inputs_available": false,
  "phonon_spectra_available": false,
  "full_repository_audit_completed": false
}
```

TDD 顺序：先写合同并因 `review.json` 缺失得到退出码 1，再实现最小生成器。最终执行合同、JSON 解析、独立来源一致性检查、OOXML 验证、`git diff --check`。Word 最终只运行一次 `docx.py render`；退出 4/5/6 表示视觉 QA 不可用，不重试、不使用 LibreOffice，也不把结构验证称为视觉通过。

## 6. 非目标

- 不重跑 Floquet-DFPT、DMRG、DFT、SSCHA 或 Lean 构建。
- 不提出新的材料 Tc，不做全局拟合，不证明室温超导必然性。
- 不直接修正五份原文；后续 P0 原文修订另开独立分支。
- 不宣称五份文档代表五个新理论，不宣称全库或 room_temp_sc 其余文档已审计完成。
