# TBC 无序振幅勘误

日期：2026-11-11。状态：`double_kick_diagnostic_superseded`。

## 错误范围

无序检查点曾把 `2*r*beta` 作为 `K` 矩阵的 onsite 参数。既有开链协议 `disordered_floquet(..., strength=r)` 的半 kick 是 `chemical_kick(r*beta)`，因此与其匹配的 `K` 参数应为 `r*beta`。在对称协议 `H F H` 中，`H=expm(-2K(r*beta))` 的半 kick 旋转角为 `r*beta`，完整对称旋转角为 `2*r*beta`。

这导致早期无序 TBC winding 与同一行保存的开链端点量使用不同驱动强度。相关结果不得用于无序拓扑结论。

## 数值确认

N=8、seed=0、r=0.1 的逐矩阵探针：

- `K` 参数 `r*beta`：与既有半 kick 的最大矩阵元差 `1.387778780781e-17`；
- `K` 参数 `2*r*beta`：最大矩阵元差 `9.758418929583e-02`。

复核脚本：`probe_kick_amplitude.py`。

## 处置

- 双倍振幅检查点及合并文件原样保留在 `diagnostics/double-kick/`，不删除、不改写其数值。
- 提交 `69cb862` 和 `8502a5f` 中的无序检查点属于该错误协议；历史提交保留，但结论被本勘误取代。
- 静态与洁净 kicked 基准不使用这个无序倍乘映射，`fd8d7ab` 的基准结论不受影响。
- 新实现逐实现计算 `half_kick_convention_error`，大于 `1e-12` 即停止；使用相同 seed 和强度从头重算，不从错误结果插值或修正。

正确结果的科学判据不变：N=80、seed 0–3、r=0.05/0.1/0.2、名义 θ 步长 0.05/0.025，所有失败和未收敛项保留。
