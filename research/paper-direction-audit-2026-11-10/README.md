# 论文方向与未竟工作总账（2026-11-10）

## 目标

逐篇区分独立新方向、既有方向延伸、教学复现、综述、重复版本和元文档；把未竟工作转化为可执行验证，而不是继续按篇数扩张。外部新颖性、数学正确性、数值可复现性和工程可行性分别裁决。

## 当前基线

- 主研究 worktree：`provider-main-integration`，提交 `a97194e`；保留其中所有既有未提交成果，不覆盖。
- TOE-SYLVA：工作区内稀疏检出 `toe-sylva-audit`，提交 `f331048`；只取 `papers/`、`framework/`、`docs/`、`scripts/`，未取约 32 万个 Lean 文件。
- 前沿共生：`frontier-breakthrough`，提交 `0b470bb`。
- 根目录独立稿件：只读取明确列出的 7 份，不扫描外部符号链接。

## 已完成的第一阶段

- 实际读取 751 份文档，形成 `inventory.json`、`inventory.csv` 与 `INVENTORY.md`。
- 文档类型分为论文、综述、研究报告、评论、审计、索引和方法文档；18 组字节级完全重复已登记。
- 生成 78 个有界阅读包；这些是可再生中间文件，目录已在 `.gitignore` 中排除，不进入版本库。
- 31 篇主花园量子系列已逐篇初审，见 `PROVIDER_REVIEW.md`；P0 10 篇、P1 18 篇、P2 3 篇。另有 `PROVIDER_REVIEW.docx` 原生 Word 版，含目录、页眉、原生页码和真正 Word 表格。
- 外部前沿首轮使用 12 项查询，覆盖 Majorana 2、Google below-threshold、Fibonacci、qLDPC、实时解码、AM–SC、非绝热几何门、Stim／PyMatching、cultivation、离子阱与量子网络标准。
- 两套现有验证脚本已真实运行，命令、退出码和证据边界见 `VALIDATION_LOG.md`。

## 已完成的第二阶段：真实表面码基准

- `surface-code-threshold/protocol.json` 冻结电路、噪声、码距、概率、shots、种子、解码器和交叉估计规则。
- 28 个网格点、560,000 个真实 Stim shots 已完成；PyMatching 逐 shot 解码，无公式生成替代值。
- 成对交叉中位数为 0.006725，范围 0.006478–0.007494；这是本协议下的探索性结果，不是原稿 1.03% 的直接复现或否证。
- `SURFACE_CODE_BENCHMARK.md` 与原生 `SURFACE_CODE_BENCHMARK.docx` 已交付，Word 含真实阈值图、目录、页眉、原生页码和完整结果表。
- 独立复验、14 项专项测试、发布审计和 6 页视觉预览均已通过；主系列 `PROVIDER_REVIEW` 已同步回写。协议哈希使用规范化 JSON 内容，避免 Windows 换行转换造成跨 worktree 假失配。

## 已完成的第三阶段：TOE 核心开放问题纠偏

- 逐项复核 O1–O10 及其桥接文档、治理登记、CI 和外部原始来源，撤回旧“8/10 已解决”，改登记为 6 项理论开放、2 项概念进展、2 项工程未决。
- 修正 CODATA 2022、五次簇 χ=-200、Pardon 归属和 DESI 状态；明确非 BPS 熵分解、最小公理 DAG、eta-DT、p-adic 乘积和费米子质量谱仍未闭合。
- `OPEN_PROBLEMS.md` 已升级为 v2.0，`ERRATA_AND_NEGATIVE_RESULTS.md` 已登记 FE-17。TOE-SYLVA PR #1 已合并，主提交为 `423836ba6f0c82dfa32dc4dc3f3fb094fbd70a26`。
- 交付 `CORE_OPEN_PROBLEMS_AUDIT_2026-11-10.md` 与原生 Word，8 页无空白页，含 1 幅状态图、17 部件验证、逐行证据锚点和真正 Word 表格。

## 重建与核验

```bash
python research/paper-direction-audit-2026-11-10/scripts/inventory_papers.py
python research/paper-direction-audit-2026-11-10/scripts/build_review_packets.py
python research/paper-direction-audit-2026-11-10/scripts/render_provider_review.py
```

`render_provider_review.py` 会验证 31 个 ID 与总账完全匹配，缺漏或多评都会直接失败。

## 下一步

1. 继续 TOE 644 份文档的权威版本映射与方向聚类，优先核心理论、模块强化、数学基础强化、室温超导、落地验证和回应中涉及的实质主张。
2. 逐篇补充外部原始文献，不能把“我们提出”或“已解决”作为新颖性证明。
3. 首先推进表面码真实蒙特卡洛阈值基准，再处理 p+ip 相图、离子阱计数、魔术态资源核算与验证协议。
4. 汇总为总报告和原生 Word 图文版；不把本阶段底账称为全部论文终审。
