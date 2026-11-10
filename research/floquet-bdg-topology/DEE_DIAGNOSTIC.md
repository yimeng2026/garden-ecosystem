# DEE 方法切片：未通过静态基准，不用于拓扑裁决

> 日期：2026-11-11。状态：`method_not_validated`。本文是负面诊断，不是对文献 DEE 的否定，也不是无序拓扑结论。

## 已核实的定义

采用 Mondal et al., arXiv:2203.16353v3 和 Mondal et al., arXiv:2111.03506v3 的分区：

- A：左半链；
- B：由 `A∩B`（左中 1/4）和 `B\A`（右端 1/4）组成；
- D：右中 1/4，即 `D = complement(A∪B)`；
- `S_D = S_A + S_B − S_(A∪B) − S_(A∩B)`。

Floquet 对数在当前 kicked 模型中为实反对称矩阵，并能以约 `1.8e-15` 的误差重构原 Floquet 算符。关联矩阵必须写为 `A = I + sign(iK)`；漏掉单位项会得到错误的纯态谱。分区原图已下载并核对，见 `sources/partition.png` 和 `sources/partitions-2022.png`。

## 已排除的实现错误

1. 单格点和双格点的完整 Fock 基态与符号函数关联矩阵逐元素一致。
2. 八格点的完整 Fock 基态也与符号函数关联矩阵一致，最大元素差约 `6.2e-14`。
3. 全集纯度成立，静态拓扑和平凡模型不再因缺失单位项而返回零。
4. 两个静态分区图与正文定义一致，没有采用猜测的替代分区。

## 未通过的基准

以下均为真实命令输出，不是文献引用值：

| 方法 | N | μ | 当前 DEE |
|:---|---:|---:|---:|
| Majorana 关联矩阵 | 8 | 0.5 | 0.005325682059 |
| 完整 Fock 偏迹 | 8 | 0.5 | 0.014057209514 |
| Majorana 关联矩阵 | 40 | 0.5 | 0.000000346474 |
| Majorana 关联矩阵 | 80 | 0.5 | 0.000000000007 |
| Majorana 关联矩阵 | 8 | 2.5 | 0.003175644313 |
| 完整 Fock 偏迹 | 8 | 2.5 | 0.000073332330 |
| 完整 Fock 偏迹 | 4／8 | 0.0 | 约 0 |

这些结果未复现所查文献在相应静态拓扑相中的量子化值，且两种实现路径并不完全一致。因此，当前 DEE 管线不能用于宣称候选受到拓扑保护，也不能据此否定文献中的 DEE。剩余问题可能涉及基态／零模选择、关联矩阵与子区偏迹约定或模型映射，尚未完全闭合。

## 处置

- 不将当前 DEE 输出写成拓扑指标，不改判据或参数去凑 `ln2`。
- 保留 `probe_dee.py`、`probe_fock_dee.py`、原始 HTML／SVG 和上述数值作为失败证据。
- 下一步改用独立的 twisted-boundary dynamical winding 路线，先验证静态 SSH／Kitaev 和洁净 kicked 极限，再考虑无序链。
- 原有无序 `not_supported`、均匀参数图和局域尺度结果不因本诊断改写。

## 可复核命令

```bash
python research/floquet-bdg-topology/probe_dee.py
python research/floquet-bdg-topology/probe_fock_dee.py
python research/floquet-bdg-topology/test_dee_diagnostic.py -v
```
