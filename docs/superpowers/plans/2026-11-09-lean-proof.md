# Controlled Lean Proof Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为花园增加可实际运行的受限 Lean 编译与公理回执，并贯通 stdio 和 Next.js API。

**Architecture:** `LeanProofAdapter` 先做静态白名单与路径检查，再以短生命周期临时包装文件调用真实 Lean。`Service` 和 TypeScript 只新增一个 `lean_check` 动作，复用现有进程边界、鉴权和回执结构。

**Tech Stack:** Python 3.11+ 标准库、真实 Lean 4.35.0、unittest、TypeScript、Node test、Next.js 16.2.9。

## Global Constraints

- 只允许自包含 `.lean` 文件，不允许 import、#指令、sorry、危险声明或额外参数。
- 源码最多 64 KiB/2000 行；使用真实路径约束与嵌套注释扫描。
- 不用 shell，不执行 `#eval` 或宏，不把 subprocess 称为完整沙箱。
- 编译失败为负结果；公理输出不可识别不得当作无公理。
- 注入 runner 一律 mock=True、attested=False；只有真实 runner 可产生真实回执。
- 临时包装必须清理；真实工具不可用时不得启动编译。
- 每项功能先观察失败，再实现，再全量回归。

---

### Task 1: 白名单、临时编译与分级回执

**Files:**
- Create: `src/garden_ecosystem/proof.py`
- Modify: `src/garden_ecosystem/lean.py`
- Modify: `.gitignore`
- Test: `tests/test_proof.py`、`tests/test_lean.py`

**Interfaces:**
- Consumes: `LeanAdapter`、`VerificationReceipt`、`ExternalToolUnavailable`。
- Produces: `LeanProofAdapter(workspace, executable=None, runner=None, timeout=10.0)`、`.health()`、`.execute(action) -> ProofReport`。
- `ProofReport` 包含 `ok`、`receipt`、`declaration`、`path`、`depends_on_axioms`、`axioms`、`stdout`、`stderr`、`source_hash`。

- [ ] **Step 1: 写失败测试**

```python
report = LeanProofAdapter(workspace=tmp, executable="lean", runner=fake_runner).execute({
    "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
})
self.assertTrue(report.ok)
self.assertEqual(report.receipt.level, VerificationLevel.MACHINE_CHECKED)
self.assertFalse(report.depends_on_axioms)
self.assertTrue(report.receipt.mock)
self.assertFalse(report.receipt.attested)
```

另测危险指令逐类拒绝、嵌套注释与字符串不误判、路径逃逸、超大源码、编译失败、输出不可识别、公理列表、路径脱敏、超时、临时目录清理和工具不可用。`test_lean.py` 将注入 runner 的预期改为 mock=True、attested=False。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_proof tests.test_lean -v`
Expected: proof 模块不存在，且旧 Lean mock 预期失败。

- [ ] **Step 3: 最小实现**

```python
@dataclass(frozen=True)
class ProofReport:
    ok: bool
    receipt: VerificationReceipt
    declaration: str
    path: str
    depends_on_axioms: bool | None
    axioms: tuple[str, ...]
    stdout: str
    stderr: str
    source_hash: str
```

实现嵌套块注释、行注释和字符串感知扫描；校验 path、declaration 和动作参数；以临时包装调用 `[resolved_lean, temporary_file]`。真实公理输出可识别且 returncode=0 才给 `MACHINE_CHECKED`，否则 `EXECUTED`。注入 runner 一律 mock=True。`LeanAdapter` 同步记录 runner 是否为测试替身。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/proof.py src/garden_ecosystem/lean.py tests/test_proof.py tests/test_lean.py .gitignore && git commit -m "feat: add controlled Lean proof receipts"`。

### Task 2: stdio `lean_check` 与能力清单

**Files:**
- Modify: `src/garden_ecosystem/service.py`、`bridge.py`
- Test: `tests/test_service.py`

**Interfaces:**
- Produces: `Service(lean=None, proof=None)`；`lean_check` 仅接受 `path`、`declaration`。
- `capabilities()["modules"]` 增加 `proof`。

- [ ] **Step 1: 写失败测试**

```python
response = service.handle({"id":"proof", "action":"lean_check",
    "params":{"path":"LeanSmoke.lean", "declaration":"one_add_one_eq_two"}})
self.assertTrue(response["ok"])
self.assertEqual(response["result"]["receipt"]["level"], "machine_checked")
```

另测额外参数、错误 path、非法声明、真实 Lean 不可用以及完整 stdio 返回。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_service -v`
Expected: unsupported action or params。

- [ ] **Step 3: 最小实现**

`Service.__init__` 注入 `proof` 并使用 `LeanProofAdapter` 默认值。`lean_check` 只接收两个键，不接收 operation 或其他透传；`asdict(proof.execute(...))` 返回报告。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/service.py src/garden_ecosystem/bridge.py tests/test_service.py && git commit -m "feat: expose Lean checks over stdio"`。

### Task 3: 主花园 `lean_check` 接口

**Files:**
- Modify: `.worktrees/garden-ecosystem-bridge/src/lib/garden-ecosystem.ts`
- Modify: `.worktrees/garden-ecosystem-bridge/tests/garden-ecosystem.test.mjs`

**Interfaces:**
- `BRIDGE_ACTIONS` 增加 `lean_check`；参数仍复用现有 JSON 对象，不改变进程环境或路由。

- [ ] **Step 1: 写失败测试**

```js
const result = await invokeBridge("lean_check", {
  path: "LeanSmoke.lean", declaration: "one_add_one_eq_two",
}, options);
assert.equal(result.result.receipt.level, "machine_checked");
assert.equal(captured.request.action, "lean_check");
assert.equal(captured.request.params.declaration, "one_add_one_eq_two");
```

保留未知动作、超时、错误响应和敏感环境测试。

- [ ] **Step 2: 观察失败**

Run: `node --test tests/garden-ecosystem.test.mjs`
Expected: unsupported bridge action。

- [ ] **Step 3: 最小实现**

将 `lean_check` 加入唯一动作集合，不增加任意文件、shell、compile 或其他 operation。

- [ ] **Step 4: 验证并提交**

Run: `node --test tests/garden-ecosystem.test.mjs && ./node_modules/.bin/tsc --noEmit`
Expected: 全部通过且类型检查无错误。
Run: `git add src/lib/garden-ecosystem.ts tests/garden-ecosystem.test.mjs && git commit -m "feat: expose Lean checks through garden bridge"`。

### Task 4: 真实验证、文档与发布

**Files:**
- Modify: `garden-ecosystem/README.md`、`docs/bridge-integration.md`、`docs/bridge-integration.docx`
- Create: `garden-ecosystem/examples/LeanSmoke.lean`

- [ ] **Step 1: 真实编译**

用已校验 SHA-256 的 Lean 4.35.0 执行 `lean_check`，保存 `examples/LeanSmoke.lean`：

```lean
theorem one_add_one_eq_two : 1 + 1 = 2 := by
  rfl
```

验证返回 `MACHINE_CHECKED`、`depends_on_axioms=false`，无残留 `.garden_tmp` 包装，且旧 health 回执仍正确。

- [ ] **Step 2: 全量门禁**

执行 Python 全量测试、安装、compileall、Node 测试、TypeScript、Next build、真实路由验收及 `release_audit.py`。确认无服务器或临时进程遗留。

- [ ] **Step 3: 文档与 PR**

更新模块数、真实测试数、白名单与“非完整沙箱”边界，重建并验证 Word。分别推送 `feature/lean-proof` 和 `feature/lean-proof-api`，创建 PR，不自动合并；Vercel 预览通过后再由所有者明确确认是否合并。

- [ ] **Step 4: 远端核验**

比较远端分支 SHA 与本地 HEAD，确认工作区干净；任何未通过项必须明确披露，不宣称项目级 Lean 验证或部署完成。
