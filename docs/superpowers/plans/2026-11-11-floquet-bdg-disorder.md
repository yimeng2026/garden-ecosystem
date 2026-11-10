# 弱化学势无序下 Floquet 0／π 候选稳健性实施计划

> 主代理使用 `superpowers:executing-plans` 执行，不使用子代理。设计见 `docs/superpowers/specs/2026-11-11-floquet-bdg-disorder-design.md`。

## Task 1：解析 kick 与失败合同

**文件：** `research/floquet-bdg-disorder/disorder_model.py`、`test_disorder.py`。

- [x] 先写 RED：解析单格点 kick、洁净矩阵指数等价、Floquet 正交性、嵌套随机序列复现、禁止旧矩阵因子。
- [x] 实现 `chemical_kick`、`disordered_floquet`、`beta_sequence` 和逐实现观测；自由部分复用 Fock 校验模型。
- [x] 保存合同失败日志，直至洁净等价和旋转不变量通过。

## Task 2：全部无序实现与集合判据

**文件：** `run_disorder.py`、`results.json`、`realizations.csv`、`disorder_sequences.npz`。

- [x] 计算 N=80、160 各 16 种子及 N=320 前 4 种子，r=0.05、0.1、0.2，逐实现保存 0／π 谱、边缘权重和子空间指标。
- [x] 同时计算对应洁净基线；不平均本征值冒充单个样品，不删除失败实现。
- [x] 主检验只含 r=0.05、0.1；按设计的全实现／多数／不支持三级裁决，r=0.2 只作压力测试。
- [x] 无序链不套用 Bloch winding，不改旧全尺寸 `inconclusive`。

## Task 3：独立验证、图件和原生 Word

**文件：** `verify_disorder.py`、`build_figure.py`、`build_markdown.py`、`build_report.js`、`test_report.py`、`run_verification.py`。

- [x] 独立检查一个无序实现的自由部分、解析 kick、正交性、随机序列和子空间旋转不变性。
- [x] 图件显示全部实现的强度和尺寸分布，不挑选最佳种子；标明主检验与压力测试。
- [x] Word 含真实 TOC、中文页眉、PAGE-only 页脚、`cantSplit`、OMML 和准确脚注；最终视图先联系表后逐页验收，退出 4／5／6 不重试、不用 LibreOffice。
- [x] 重跑全流程，核对 JSON、CSV、图件、Word 和退出码；缓存放 D 盘。

## Task 4：提交与边界

- [x] `git diff --check` 后提交并推送 `research/floquet-bdg-disorder`，核对远端哈希，保留工作树，不合并主分支。
- [x] 报告只声称有限实现的候选稳健性；不宣称无序拓扑不变量、热力学极限、材料 `Tc` 或实验复现。
