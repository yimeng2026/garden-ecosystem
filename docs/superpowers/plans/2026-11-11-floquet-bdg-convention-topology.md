# Floquet–BdG 物理约定修复与联合拓扑诊断实施计划

> 主代理按 `superpowers:executing-plans` 执行，不使用子代理。设计来源：`docs/superpowers/specs/2026-11-11-floquet-bdg-convention-topology-design.md`。

**目标：** 用独立 Fock 空间确定正确 Majorana 矩阵，修复旧实现因子问题，随后计算 Bloch winding、0／π 端点计数和修正后的开放链候选。

**边界：** 旧 `research/floquet-bdg/` 原始结果和报告不覆盖；只新增勘误。新代码和结果位于 `research/floquet-bdg-convention/`。不把模型结果外推为材料 `Tc` 或实验结论。

## Task 1：独立 Fock 失败证据

**文件：**
- `research/floquet-bdg-convention/fock_reference.py`
- `research/floquet-bdg-convention/probe_legacy_convention.py`
- `research/floquet-bdg-convention/test_convention.py`
- `research/floquet-bdg-convention/convention-red.log`

步骤：

- [ ] 用 Jordan–Wigner 构造一／双格点费米子算符、Fock Hamiltonian 和 Majorana 算符；不得调用旧 `majorana_k` 生成参考值。
- [ ] 写旧实现探针：比较单格点 `sin(2μt)` 与旧 `sin(4μt)`，并比较双格点 `H_Fock` 与 `iΣK_legacyΓΓ`，输出实际矩阵差异。
- [ ] 运行探针，预期退出码 1；记录旧实现的实际错误，不用静态零模结果掩盖。
- [ ] 新模块合同包含逐元素 Fock 一致性、单格点 Heisenberg 演化、矩阵反对称性和旧零空间基准；先因 `convention_model` 缺失而 RED。

## Task 2：正确矩阵与 Bloch 拓扑

**文件：**
- `research/floquet-bdg-convention/convention_model.py`
- `research/floquet-bdg-convention/test_convention.py`
- `research/floquet-bdg-convention/test_topology.py`

步骤：

- [ ] 实现 `K[a,b]=−μ/2`、`(Δ−γ)/4`、`−(Δ+γ)/4` 及 `U=expm(-4KT)`，直到 Fock 逐元素和演化合同全部通过。
- [ ] 实现 `h(k)=2(−γcosk−μ0)τ_z+2Δsinkτ_y`、对称化 kick、`U(k)`、`b0/bπ` 和限定域端点计数。
- [ ] 用 `φ∈(0,π)` 的 `U=cosφI−i sinφ n·τ` 提取 `n_y,n_z`，对 `atan2(n_y,n_z)` 解卷绕计算 winding；`sinφ` 过小时返回 `gapless_or_undefined`。
- [ ] 合同固定主算例 `|W|=2`、静态控制 `W=0`、`p0=pπ=1`；`Nk=512,1024,2048,4096` 的整数偏差和相邻差均 `<1e-6`。抽样点用 `logm` 复核矢量方向。
- [ ] 修正前后端点计数分开保存；不得把旧参数有效倍增产生的额外模当成当前目标参数结论。

## Task 3：修正后的开放链与独立验证

**文件：**
- `research/floquet-bdg-convention/run_topology.py`
- `research/floquet-bdg-convention/results.json`
- `research/floquet-bdg-convention/candidates.csv`
- `research/floquet-bdg-convention/spectra.npz`
- `research/floquet-bdg-convention/verify_topology.py`

步骤：

- [ ] 重算 `N=40,80,160`，若最近候选仍不分离则加 `N=320`；矩阵指数与 eigensolver 容差均记录。
- [ ] 每个目标输出最近四对共轭本征值及距离、两端权重、左右权重和 IPR，保留完整谱，防止误标第二对边缘模。
- [ ] 旧 `separation<0.1`、`edge_weight>0.5` 阈值只作对照；先根据修正后的全部近零对和体不变量判断候选归属，不事后修改阈值。
- [ ] 独立验证重新构造 Fock 参考、计算选定动量点、重算至少一个开放链尺寸，并检查旧结果 SHA-256 未变。
- [ ] 所有测试含 `run_all_tests()` 和零测试保护；记录 NumPy／SciPy／Python 版本与真实退出码。

## Task 4：勘误、图件、原生 Word 与交付

**文件：**
- `research/floquet-bdg/ERRATA.md`（新增，不改旧结果）
- `research/floquet-bdg-convention/README.md`
- `research/floquet-bdg-convention/REPORT.docx`
- `research/floquet-bdg-convention/topology.svg/.png`
- `research/floquet-bdg-convention/run_verification.py`
- `research/floquet-bdg-convention/run.log`

步骤：

- [ ] 勘误写明旧矩阵因子、受影响参数、旧 π／0 结论暂停范围、旧文件哈希和新交付位置；不删除旧证据。
- [ ] 图件包含 Bloch 轨迹、winding 网格收敛、修正后候选距离和端点权重；所有数据来自当前结果。
- [ ] Word 使用 docx-js，含真实 TOC、中文页眉、PAGE-only 页脚、`cantSplit`、OMML 和准确脚注；最终视图先联系表后逐页验收，退出 4／5／6 不重试、不用 LibreOffice。
- [ ] 全流程重跑并检查结果、Word、日志哈希；构建依赖和临时缓存放 D 盘。
- [ ] `git diff --check` 后提交并推送 `fix/floquet-bdg-convention`，核对远端哈希，保留工作树，不合并主分支。

## 完成口径

只有 Fock 一致性、Bloch 不变量、开放链重算和独立验证均通过，才可报告修正后的 0／π 结果。若 0 模仍不满足原判据，必须保留 `inconclusive` 并列出剩余差异；不得为了闭合任务而改阈值或沿用旧结论。
