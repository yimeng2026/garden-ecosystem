# Floquet 显式误差界语义切片实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 用显式误差界替代 `HasEquiv ℝ`，并真实证明零误差与精确等式的双向关系，而不证明 Floquet 增强命题。

**Architecture:** 独立 `FloquetApproximation.lean` 将 `DriveApprox` 定义为绝对误差不超过 `ε`。先验证定义展开，再证明误差为零时精确等式成立，以及精确等式推出零误差；随后执行真实编译、独立回归和 Word 交付。

**Tech Stack:** Lean 4.35.0、Mathlib `56a005855ea17e0b0958f73ec801ae140b0a1679`、Python `unittest`、D 盘隔离工具链、docx-js。

## Global Constraints

- 原文件只读，哈希必须保持 `1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439`。
- 禁止新增 `axiom`、`postulate`、证明位 `sorry`、`admit`、`native_decide` 或 `HasEquiv` 实例。
- 只证明误差语义和零误差特例；不证明 `∃ T_c_F, T_c_F > T_c_eq`，不验证物理有效性、材料预测或实验复现。
- 每个成功声明必须来自真实 Lean 命令、退出码和 `#print axioms` 输出。
- 最终视图退出 4／5／6 时不重试、不使用 LibreOffice；必须记录实际视觉状态。

---

### Task 1：语义切片失败合同

**Files:**
- Create: `research/lean-proof-slice/test_floquet_approximation.py`
- Create: `research/lean-proof-slice/floquet-run.log`

**Interfaces:**
- Consumes: 原文件哈希与既有 `original-compile.log`。
- Produces: 未来 `floquet-approximation.json`、`FloquetApproximation.lean`、`FLOQUET_APPROXIMATION.md/.docx`。

- [x] **Step 1: 写失败测试**

在 `test_floquet_approximation.py` 写入以下合同，并包含 `run_all_tests()` 零测试保护：

```python
def test_definition_has_error_bound_not_has_equiv(self):
    text = (ROOT / "FloquetApproximation.lean").read_text(encoding="utf-8")
    self.assertIn("def DriveApprox", text)
    self.assertIn("|ω_drive - 2 * Δ / ℏ| ≤ ε", text)
    self.assertNotIn("HasEquiv", text)

def test_zero_error_exact_equivalence(self):
    data = json.loads((ROOT / "floquet-approximation.json").read_text(encoding="utf-8"))
    self.assertEqual(data["compile"]["exit_code"], 0)
    for name in ("driveApprox_zero_exact", "driveApprox_of_exact"):
        self.assertFalse(data["dependencies"][name]["sorryAx"])
        self.assertEqual(data["dependencies"][name]["nonstandard_axioms"], [])

def test_original_and_physical_boundaries(self):
    data = json.loads((ROOT / "floquet-approximation.json").read_text(encoding="utf-8"))
    self.assertEqual(data["original"]["sha256"], EXPECTED_ORIGINAL)
    self.assertEqual(data["original"]["sorry_lines"], [93, 112, 185])
    self.assertFalse(data["open_boundaries"]["floquet_enhancement_proven"])
    self.assertFalse(data["open_boundaries"]["physical_validity_verified"])
```

同时检查 `DriveApprox` 只含一个 `rfl` 展开、两个非 `rfl` 的零误差证明，以及 Word 的真实 TOC、至少三个表格、中文页眉和 PAGE-only 页脚。

- [x] **Step 2: 运行测试，确认 RED**

Run: `python research/lean-proof-slice/test_floquet_approximation.py -v`
Expected: 退出码 1，`FileNotFoundError: floquet-approximation.json`；`Ran 0 tests` 的防呆逻辑记录到 `floquet-run.log`。

- [x] **Step 3: 提交失败合同**

```bash
git add research/lean-proof-slice/test_floquet_approximation.py research/lean-proof-slice/floquet-run.log docs/superpowers/plans/2026-11-11-floquet-approximation.md
git commit -m "test: define Floquet approximation contracts"
```

---

### Task 2：显式误差界与真实证明

**Files:**
- Create: `research/lean-proof-slice/FloquetApproximation.lean`
- Create: `research/lean-proof-slice/audit_floquet_approximation.py`
- Create: `research/lean-proof-slice/verify_floquet_approximation.py`
- Generate: `floquet-approximation.json`、`FLOQUET_APPROXIMATION.md`、`floquet-compile.log`

**Interfaces:**
- Consumes: D 盘 `lake`／`lean` 可执行文件、固定 Mathlib、原文件只读副本。
- Produces: `DriveApprox`、`driveApprox_zero_exact`、`driveApprox_of_exact` 及依赖证据。

- [x] **Step 1: 写独立 Lean 定义与证明**

在 `FloquetApproximation.lean` 写入：

```lean
import Mathlib

namespace Sylva.RoomTempSuperconductivity

open Real

/-- Explicit absolute-error bound, not a HasEquiv instance. -/
def DriveApprox (ω_drive Δ ℏ ε : ℝ) : Prop :=
  |ω_drive - 2 * Δ / ℏ| ≤ ε

/-- Definitional unfolding only; this is not a Floquet enhancement proof. -/
theorem driveApprox_unfold (ω_drive Δ ℏ ε : ℝ) :
    DriveApprox ω_drive Δ ℏ ε = (|ω_drive - 2 * Δ / ℏ| ≤ ε) := by
  rfl

/-- Zero error recovers the exact drive relation. -/
theorem driveApprox_zero_exact (ω_drive Δ ℏ : ℝ)
    (h : DriveApprox ω_drive Δ ℏ 0) :
    ω_drive = 2 * Δ / ℏ := by
  have h_abs : |ω_drive - 2 * Δ / ℏ| = 0 :=
    le_antisymm h (abs_nonneg _)
  exact sub_eq_zero.mp (abs_eq_zero.mp h_abs)

/-- Exact equality gives the zero-error bound. -/
theorem driveApprox_of_exact (ω_drive Δ ℏ : ℝ)
    (h : ω_drive = 2 * Δ / ℏ) :
    DriveApprox ω_drive Δ ℏ 0 := by
  simp [h, DriveApprox]

#print axioms driveApprox_unfold
#print axioms driveApprox_zero_exact
#print axioms driveApprox_of_exact

end Sylva.RoomTempSuperconductivity
```

将同一文件复制到 `D:/migration/lean-proof-slice-build/FloquetApproximation.lean`，字节必须一致。

- [x] **Step 2: 真实编译并检查依赖**

Run（在 D 盘构建副本中）：

```bash
export ELAN_HOME="D:/migration/toolchains/elan/home"
export XDG_CACHE_HOME="D:/migration/cache"
export HOME="D:/migration/home"
export TMP="D:/migration/tmp"
export TEMP="D:/migration/tmp"
export TMPDIR="D:/migration/tmp"
export PATH="/d/migration/toolchains/elan/home/bin:$PATH"
lake env lean -o ".lake/build/lib/lean/FloquetApproximation.olean" "FloquetApproximation.lean"
```

Expected: 退出码 0；三个定理均只出现 `[propext, Classical.choice, Quot.sound]`，没有 `sorryAx`。

- [x] **Step 3: 生成结构化结果与独立复核**

`audit_floquet_approximation.py` 必须：

```python
for name in ("driveApprox_unfold", "driveApprox_zero_exact", "driveApprox_of_exact"):
    line = find_exactly_one_axiom_line(clean_output, name)
    assert "sorryAx" not in line
    assert only_standard_axioms(line)
```

同时验证原文件哈希、静态 `sorry` 行 `[93,112,185]`、两个零误差定理和一个 `rfl`，生成 `floquet-approximation.json`、`FLOQUET_APPROXIMATION.md` 和原始 `floquet-compile.log`。`verify_floquet_approximation.py` 必须独立读取源文件与 JSON，运行四个独立测试并包含零测试保护。

- [x] **Step 4: 运行独立测试与主合同**

Run: `python research/lean-proof-slice/verify_floquet_approximation.py -v`
Expected: `Ran 4 tests; OK`。
Run: `python research/lean-proof-slice/test_floquet_approximation.py -v`
Expected: 此阶段只允许 `FLOQUET_APPROXIMATION.docx` 缺失，其他合同全部通过。

---

### Task 3：原生 Word 与视觉验收

**Files:**
- Create: `research/lean-proof-slice/build_floquet_report.js`
- Create: `research/lean-proof-slice/build_floquet_figure.py`
- Create: `research/lean-proof-slice/record_floquet_qa.py`
- Generate: `FLOQUET_APPROXIMATION.docx`、`floquet-approximation.svg/.png`、`word-qa-floquet/report.json`

**Interfaces:**
- Consumes: `floquet-approximation.json`、`floquet-compile.log` 和实际 `#print axioms` 输出。
- Produces: 原生 Word、对照图和视觉状态。

- [x] **Step 1: 生成双轨图与原生 Word**

图左列出 `DriveApprox`、零误差推出精确等式、精确等式推出零误差；图右列出 `HasEquiv` 未引入、Floquet 增强未证明、原文件未修改。图内使用 ASCII `HasEquiv Real` 和 `DriveApprox`，避免缺字。

Word 必须包含真实 TOC、中文页眉、PAGE-only 页脚、至少三个表格、两个定义／证明表、开放边界表和准确脚注。图件位于语义定义表之后、开放边界之前。使用原生 OMML 表达 `|ω_drive − 2Δ/ℏ| = 0 ↔ ω_drive = 2Δ/ℏ`，不以图片替代公式。

- [x] **Step 2: 构建并运行两套测试**

Run: `python {kimi-word}/scripts/docx.py build <absolute build_floquet_report.js> <absolute FLOQUET_APPROXIMATION.docx`
Expected: `PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)`。
Run: 两套测试。
Expected: 主合同与四个独立测试全部通过。

- [x] **Step 3: 最终视图与状态记录**

Run: `python {kimi-word}/scripts/docx.py render <absolute FLOQUET_APPROXIMATION.docx> <absolute word-qa-floquet`
先读联系表，再读全部页面，检查公式、图件、表格、目录和脚注。退出 4／5／6 时只记录 `visualQA.status=unavailable`、`reviewedPages=[]`、`visualPassClaimed=false`，不重试、不使用 LibreOffice。`record_floquet_qa.py` 写入实际 DOCX SHA-256 和视觉状态。

---

### Task 4：fresh 回归与交付

**Files:**
- Modify: `research/lean-proof-slice/floquet-run.log`
- Modify: `docs/superpowers/plans/2026-11-11-floquet-approximation.md`

**Interfaces:**
- Consumes: 全部结构化结果、日志、测试和 Word。
- Produces: 具名分支 `fix/floquet-approximation` 的提交与远端哈希。

- [x] **Step 1: fresh 全量回归**

Run: 主合同、独立复核、真实 `audit_floquet_approximation.py`、JSON 解析、原文件哈希、DOCX 哈希和 `git diff --check`。
Expected: 全部退出 0；主合同至少 6 项、独立复核 4 项，清洁编译退出码 0，标准公理之外无依赖。

- [x] **Step 2: 提交并推送**

```bash
git add research/lean-proof-slice docs/superpowers/plans/2026-11-11-floquet-approximation.md
git commit -m "feat: add Floquet approximation semantics"
git push -u origin fix/floquet-approximation
git rev-parse HEAD
git ls-remote origin refs/heads/fix/floquet-approximation
```

Require: 本地与远端哈希一致、工作区干净、未合并主分支。

- [x] **Step 3: 记录交付边界**

以 `docs: record Floquet approximation delivery` 记录最终提交、验证、视觉状态和未竟工作。继续 Floquet 物理推导、材料预测和实验复现，保持全库目标 active；不得把语义切片当作 Floquet 增强或项目级证明。

## Plan Self-Review

- 规格中的 `HasEquiv` 已由显式绝对误差界替代，未构造实例。
- 零误差双向关系包含实际 Lean 证明，不是只写定义或静态注释。
- Floquet 增强命题、原文件直译和物理验证均明确排除在完成范围之外。
- 所有路径、版本、测试、原始日志、视觉状态和远端哈希均有可执行验收命令。
