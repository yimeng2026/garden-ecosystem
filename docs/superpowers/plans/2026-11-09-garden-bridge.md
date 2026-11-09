# Controlled Garden Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让主花园通过受控 stdio 调用适配项目，并获得真实的 Lean 可用性与分级版本检查回执。

**Architecture:** Python `LeanAdapter` 仅执行 `--version`，`Service` 处理单条白名单 JSON；TypeScript `invokeBridge` 在独立 worktree 中逐请求启动子进程。Next.js Route 只转发四个白名单动作，不开放任意参数。

**Tech Stack:** Python 3.11+ 标准库、Node.js 25、TypeScript、Next.js 16.2.9 Route Handlers、unittest、node:test。

## Global Constraints

- 不使用 shell、eval、exec、任意 Lean 参数或任意文件编译。
- 不继承完整环境变量，不输出密钥、完整 stderr 或用户源文件。
- 输入 16 KiB、stdio 输出 64 KiB、桥接超时 10 秒；Lean 探测短超时。
- 版本检查仅为 `EXECUTED`，不得生成 `machine_checked`。
- 先观察测试失败，再写最小实现；mock 与本机真实探测分开记录。
- 不覆盖主花园当前 `package.json` 改动，不遗留后台进程，不自行合并 PR。

---

### Task 1: 真实 Lean 健康检查适配器

**Files:**
- Create: `src/garden_ecosystem/lean.py`
- Test: `tests/test_lean.py`

**Interfaces:**
- Consumes: `ExternalToolAdapter`、`ToolHealth`、`VerificationReceipt`、`ExternalToolUnavailable`。
- Produces: `LeanAdapter(executable=None, runner=None, timeout=3.0)`，`.health()` 与 `.execute({"operation":"health"})`。

- [ ] **Step 1: 写失败测试**

```python
from garden_ecosystem.lean import LeanAdapter
from garden_ecosystem.receipts import VerificationLevel

adapter = LeanAdapter(executable="definitely-not-a-real-lean")
assert adapter.health().status == "unavailable"

def successful(command, timeout):
    assert command[1:] == ["--version"]
    return SimpleNamespace(returncode=0, stdout="Lean (version 4.31.0, x86_64)", stderr="")
adapter = LeanAdapter(executable="lean", runner=successful)
with patch("garden_ecosystem.lean.shutil.which", return_value="lean"):
    assert adapter.health().status == "available"
    receipt = adapter.execute({"operation": "health"})
assert receipt.level is VerificationLevel.EXECUTED
assert receipt.attested is True
```

另测非零退出、空输出、错误版本文本、超时、其他 operation、timeout 非正数，以及真实默认适配器的状态只可能是 available/degraded/unavailable，不能把本机状态硬编码为 available。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_lean -v`
Expected: `ModuleNotFoundError: garden_ecosystem.lean`。

- [ ] **Step 3: 实现**

```python
class LeanAdapter:
    name = "lean"
    def __init__(self, executable=None, runner=None, timeout=3.0):
        self.executable = executable or os.environ.get("LEAN_EXECUTABLE", "lean")
        self.runner = runner or subprocess.run
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout
```

`_probe` 先解析可执行文件，之后只传 `[resolved, "--version"]`；捕获 `TimeoutExpired` 和 `OSError` 并返回 degraded/unavailable。stdout 必须匹配 `Lean (version …)` 才接受。`execute` 只接受 operation=health，返回 `VerificationReceipt(EXECUTED, "lean", version, stable_hash(...), attested=True)`。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v && PYTHONPATH=src python -c "from garden_ecosystem.lean import LeanAdapter; print(LeanAdapter().health())"`
Expected: 全部测试通过；真实输出按本机实际状态，不强制 available。
Run: `git add src/garden_ecosystem/lean.py tests/test_lean.py && git commit -m "feat: add real Lean health adapter"`。

### Task 2: 单请求 stdio 服务

**Files:**
- Create: `src/garden_ecosystem/service.py`
- Modify: `src/garden_ecosystem/bridge.py`
- Test: `tests/test_service.py`

**Interfaces:**
- Consumes: `LeanAdapter`、`capabilities`、`health`。
- Produces: `Service.handle(request) -> dict`、`Service.handle_safely(request) -> dict`、`main()`。
- 合法 action：capabilities、health、lean_health、lean_receipt。

- [ ] **Step 1: 写失败测试**

```python
service = Service(lean=UnavailableExternalTool("lean"))
response = service.handle({"id": "one", "action": "lean_health", "params": {}})
assert response == {"id": "one", "ok": True,
                    "result": {"status": "unavailable", "reason": "no configured real adapter for lean"}}
unknown = service.handle_safely({"id": "bad", "action": "shell", "params": {}})
assert unknown["ok"] is False and unknown["error"]["type"] == "ValueError"
```

另测四个动作、params 非字典、未知动作、缺 ID、异常不泄露、stdin 非 JSON、stdin 超过 16384 字节；用 `subprocess.run([sys.executable, "-m", "garden_ecosystem.service"], input=...)` 做真实 stdio 往返，等待子进程退出。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_service -v`
Expected: 导入失败。

- [ ] **Step 3: 实现**

```python
ACTIONS = {"capabilities", "health", "lean_health", "lean_receipt"}
def handle(self, request):
    request_id = request.get("id")
    action = request.get("action")
    params = request.get("params", {})
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("id is required")
    if action not in ACTIONS or not isinstance(params, dict):
        raise ValueError("unsupported action or params")
    return {"id": request_id, "ok": True, "result": self._dispatch(action, params)}
```

`handle_safely` 只返回错误类型与安全消息；`main` 限制 stdin 为 16384 字节，stdout 仅一个 JSON。`capabilities()` 的 modules 增加 lean 和 service，其他既有接口保持兼容。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过，stdio 子进程退出。
Run: `git add src/garden_ecosystem/service.py src/garden_ecosystem/bridge.py tests/test_service.py && git commit -m "feat: add whitelisted stdio bridge"`。

### Task 3: 主花园 TypeScript 客户端与 Route

**Files:**
- Create: `.worktrees/garden-ecosystem-bridge/src/lib/garden-ecosystem.ts`
- Create: `.worktrees/garden-ecosystem-bridge/src/app/api/garden-ecosystem/route.ts`
- Test: `.worktrees/garden-ecosystem-bridge/tests/garden-ecosystem.test.mjs`
- Modify: `.worktrees/garden-ecosystem-bridge/.env.example`

**Interfaces:**
- Consumes: stdio JSON 协议与当前 Next.js route/runtime/connection 文档。
- Produces: `invokeBridge(action, params?, options?) -> Promise<BridgeResponse>`、`POST(request: Request) -> Response`。

- [ ] **Step 1: 创建隔离 worktree 并写失败测试**

从 `origin/main` 创建 `.worktrees/garden-ecosystem-bridge`，分支 `feature/garden-ecosystem-bridge`。测试用 EventEmitter 模拟子进程，断言动作、参数、环境变量和错误路径：

```js
test("unknown action never spawns", async () => {
  let spawned = false;
  await assert.rejects(invokeBridge("shell", {}, { spawnImplementation: () => { spawned = true; } }));
  assert.equal(spawned, false);
});
```

另测密钥不进入子进程 env、默认目录为相邻 garden-ecosystem、正常响应、超大输入、进程错误、超时、stdout 超限、无效 JSON、响应 ID 错配。

- [ ] **Step 2: 观察失败**

Run: `node --test tests/garden-ecosystem.test.mjs`
Expected: 找不到 `src/lib/garden-ecosystem.ts`。

- [ ] **Step 3: 实现**

```ts
export async function invokeBridge(action: string, params: Record<string, unknown> = {}, options: BridgeOptions = {}) {
  if (!ACTIONS.has(action)) throw new TypeError("unsupported bridge action");
  const id = options.id ?? randomUUID();
  const payload = JSON.stringify({ id, action, params });
  if (Buffer.byteLength(payload) > 16_384) throw new TypeError("bridge request too large");
  return runProcess(payload, id, options);
}
```

只传白名单环境变量，spawn `python -m garden_ecosystem.service`，无 shell；按 stdout/stderr/timeout 上限关闭进程。Route 使用 `runtime="nodejs"`、`dynamic="force-dynamic"`、`await connection()`，错误按 400/502/503 分类。

- [ ] **Step 4: 验证并提交**

Run: `node --test tests/garden-ecosystem.test.mjs && ./node_modules/.bin/tsc --noEmit`
Expected: 测试通过且类型检查无错误；若类型检查失败，逐项修正，不改无关文件。
Run: `git add src/lib/garden-ecosystem.ts src/app/api/garden-ecosystem tests .env.example && git commit -m "feat: connect controlled ecosystem bridge"`。

### Task 4: 联合验证、文档与推送

**Files:**
- Modify: `garden-ecosystem/README.md`
- Create: `garden-ecosystem/docs/bridge-integration.md`

- [ ] **Step 1: 完整验证**

在适配项目执行 `.venv/Scripts/python.exe -m unittest discover -s tests -v`、`compileall`、`release_audit.py`，更新实际测试数。
在主花园 worktree 执行 Node 测试和 TypeScript 检查，并进行 Next build；若失败，保留完整错误并区分环境/既有问题与本批缺陷。

- [ ] **Step 2: 实际协议验证**

用真实 Python stdio 调用 capabilities 和 lean_health；记录真实 Lean 状态，不用模拟输出替代。确认所有临时子进程退出，不启动或遗留 Next dev server。

- [ ] **Step 3: 文档和最终审计**

README 增加 Node/Next 侧接入方法、环境变量、四个动作、Lean 非证明边界；安全扫描不允许真实 token、模型权重、上游源码或后台进程。更新 `capabilities()` 与文档中的模块清单。

- [ ] **Step 4: 推送与远端核验**

分别推送 `feature/controlled-bridge` 和 `feature/garden-ecosystem-bridge`，创建对应 PR，不合并。读取远端分支 SHA 并与本地 HEAD 比较；如网络失败，明确标记未完成的远端步骤，不伪称成功。
