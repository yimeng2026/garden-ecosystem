# Garden Ecosystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为千界花园提供可独立验证的供应商、上下文、门禁、世界、学习及证据治理适配层。

**Architecture:** 新建独立 Python 标准库包，接口注入所有副作用，默认离线、拒绝执行。主花园只读取能力/健康接口；源码、密钥、模型权重和上游项目均不进入发布包。

**Tech Stack:** Python 3.11+、`unittest`、`dataclasses`、`enum`、`hashlib`、`json`、`urllib`、Git。

## Global Constraints

- 所有文件限于 `garden-ecosystem/`；不改主花园前端及其他仓库。
- 不复制 GPL 实现、未声明许可证源码、模型权重、密钥或个人主页内容。
- 默认无网络、无 shell、无写操作、无学习；任何 MODIFY 均不可直接执行。
- 真实输入用量必须匹配精确前缀与模型；预算不足必须失败。
- 回滚失败必须显式报告，不能将“尝试回滚”写成“恢复成功”。
- 每项功能先观察预期失败，再做最小实现，再运行完整回归。

---

### Task 1: 可安装标准库骨架与公共工具

**Files:**
- Create: `pyproject.toml`、`.gitignore`、`LICENSE`、`NOTICE.md`
- Create: `src/garden_ecosystem/__init__.py`、`errors.py`、`security.py`
- Test: `tests/test_security.py`

**Interfaces:**
- Produces: `redact(text: str, secrets: Iterable[str]) -> str`、`stable_hash(value: object) -> str`、`GardenError`。
- `redact` 同时处理原始值与 JSON 字符串值，空密钥不得造成异常替换。

- [ ] **Step 1: 写失败测试**

```python
import unittest
from garden_ecosystem.security import redact, stable_hash

class SecurityTests(unittest.TestCase):
    def test_redacts_values_without_empty_replacement(self):
        self.assertEqual(redact("token=abc", ["abc", ""]), "token=[redacted]")

    def test_stable_hash_is_order_independent_for_mapping_keys(self):
        self.assertEqual(stable_hash({"b": 1, "a": 2}), stable_hash({"a": 2, "b": 1}))
```

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_security -v`
Expected: `ModuleNotFoundError: garden_ecosystem`。

- [ ] **Step 3: 最小实现**

```python
# errors.py
class GardenError(Exception):
    """可安全展示给调用方的适配层错误。"""

# security.py
import hashlib
import json
from collections.abc import Iterable

def stable_hash(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def redact(text: str, secrets: Iterable[str]) -> str:
    result = str(text)
    for secret in sorted({item for item in secrets if item}, key=len, reverse=True):
        result = result.replace(secret, "[redacted]")
        result = result.replace(json.dumps(secret)[1:-1], "[redacted]")
    return result
```

`pyproject.toml` 使用 setuptools `src` 布局、`requires-python = ">=3.11"`；`.gitignore` 忽略 `.env*`、`artifacts/`、`upstream/`、缓存和虚拟环境，但保留 `.env.example`。`LICENSE` 为 MIT，`NOTICE.md` 只记录真实读取过的来源及固定提交。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add pyproject.toml .gitignore LICENSE NOTICE.md src tests && git commit -m "feat: add safe package foundation"`。

### Task 2: 供应商故障治理与密钥作用域

**Files:**
- Create: `src/garden_ecosystem/providers.py`
- Test: `tests/test_providers.py`

**Interfaces:**
- Produces: `FailureKind`、`ProviderError`、`ProviderProfile`、`ProviderPool.call(request, transport)`、`scoped_secret(environ, name, value)`。
- `transport(profile, secret, request)` 由调用方注入，返回 JSON 可序列化对象。

- [ ] **Step 1: 写失败测试**

```python
profile_a = ProviderProfile("a", "model-a", secret_env="A_KEY")
profile_b = ProviderProfile("b", "model-b", secret_env="B_KEY")
pool = ProviderPool([profile_a, profile_b], environ={"A_KEY": "sa", "B_KEY": "sb"})
seen = []
def transport(profile, secret, request):
    seen.append(profile.name)
    if profile.name == "a":
        raise ProviderError(FailureKind.RATE_LIMIT, "sa failed")
    return {"content": "ok"}
result = pool.call({}, transport)
self.assertEqual(result["content"], "ok")
self.assertEqual(seen, ["a", "b"])
self.assertNotIn("sa", str(pool.audit))
with self.assertRaises(ProviderError):
    pool.call({}, lambda *_: (_ for _ in ()).throw(ProviderError(FailureKind.AUTH, "bad")))
```

另测：abort/auth/invalid_request/not_found/context_overflow 不切换；重复回退去重；缺失密钥失败；临时环境退出后旧值恢复、新值删除。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_providers -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
class FailureKind(str, Enum):
    ABORT="abort"; AUTH="auth"; INVALID_REQUEST="invalid_request"
    NOT_FOUND="not_found"; CONTEXT_OVERFLOW="context_overflow"
    RATE_LIMIT="rate_limit"; SERVER="server"; TIMEOUT="timeout"; NETWORK="network"

class ProviderError(GardenError):
    def __init__(self, kind: FailureKind, message: str):
        super().__init__(message)
        self.kind = kind

@dataclass(frozen=True)
class ProviderProfile:
    name: str
    model: str
    secret_env: str
    fallbacks: tuple[str, ...] = ()
    context_window: int | None = None
    max_output_tokens: int = 8192
    protocol: str = "chat_completions"
```

`ProviderPool` 按当前及显式 fallbacks 构建去重链，只对 `{RATE_LIMIT, SERVER, TIMEOUT, NETWORK}` 切换；审计只保存 provider、kind、是否成功。`scoped_secret` 为 contextmanager，finally 中恢复原值或 pop。超时和 HTTP 异常转换必须限定具体异常，不将编程错误吞成网络错误。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过，审计不含测试密钥。
Run: `git add src/garden_ecosystem/providers.py tests/test_providers.py && git commit -m "feat: add classified provider failover"`。

### Task 3: 上下文预算与安全工具输出

**Files:**
- Create: `src/garden_ecosystem/context.py`
- Test: `tests/test_context.py`

**Interfaces:**
- Produces: `estimate_tokens`、`UsageAnchor`、`Budget`、`resolve_budget`、`ToolOutputGovernor`、`IntervalCache`。
- 锚点含 `model`、`prefix_hash`、`input_tokens`；窗口不足抛 `BudgetExceeded`。

- [ ] **Step 1: 写失败测试**

```python
messages = [{"role": "user", "content": "检查引力"}]
anchor = UsageAnchor("m", stable_hash(messages), 20)
self.assertEqual(resolve_budget(messages, "m", 100, 40, anchor).source, "measured")
self.assertEqual(resolve_budget(messages, "m", 100, 40,
    UsageAnchor("m", "wrong", 1)).source, "estimate")
with self.assertRaises(BudgetExceeded):
    resolve_budget(messages, "m", 25, 40, anchor, reserve=2, minimum=8)
```

另测中文不被零计、重复区间返回缓存、路径 `../x` 和绝对路径逃逸拒绝、长文本标出省略长度、摘要字段 `kind="summary"`。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_context -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
@dataclass(frozen=True)
class UsageAnchor:
    model: str
    prefix_hash: str
    input_tokens: int

def resolve_budget(messages, model, window, configured, anchor=None,
                   tools=0, reserve=64, minimum=128):
    source = "measured" if anchor and anchor.model == model \
        and anchor.prefix_hash == stable_hash(messages) else "estimate"
    used = anchor.input_tokens if source == "measured" else estimate_tokens(
        json.dumps(messages, ensure_ascii=False))
    available = window - used - tools - reserve
    if available < minimum:
        raise BudgetExceeded(f"output budget unavailable: {available}")
    return Budget(min(configured, available), available, used, source)
```

实现时校验 window/configured/tools/reserve/minimum 为有限正数或允许的非负数。`ToolOutputGovernor` 只在调用方指定的 `Path.resolve()` 工作区内读取；`IntervalCache` 以规范化 `path,start,end,content hash` 为键，不得缓存密钥。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/context.py tests/test_context.py && git commit -m "feat: guard context and tool output budgets"`。

### Task 4: 默认拒绝的四态执行门禁

**Files:**
- Create: `src/garden_ecosystem/reliability.py`
- Test: `tests/test_reliability.py`

**Interfaces:**
- Produces: `Action`、`DecisionType`、`Decision`、`ApprovalTicket`、`Guard.check`、`Guard.execute`。
- `execute` 只在 ALLOW 或票据匹配的 ASK 时调用 executor，返回审计字典。

- [ ] **Step 1: 写失败测试**

```python
calls = []
guard = Guard()
action = Action("agent", "write_file", "notes.md")
decision = guard.execute(action, lambda _: calls.append("bad"))
self.assertFalse(decision.executed)
self.assertEqual(calls, [])
modify = guard.check(Action("agent", "write_file", "tests/test_demo.py"))
self.assertEqual(modify.type, DecisionType.MODIFY)
self.assertFalse(modify.executable)
```

另测只读可 ALLOW；生产部署 ASK；票据的动作 hash、主体、过期及一次性限制；force push 与生产删除 DENY；建议重新走 check；审计脱敏。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_reliability -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
class DecisionType(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; ASK="ASK"; MODIFY="MODIFY"

@dataclass(frozen=True)
class Decision:
    type: DecisionType
    reason: str
    executable: bool = False
    suggested: Action | None = None

# 所有执行统一走这一分支，不在工具函数中另开后门
if decision.type is DecisionType.ALLOW:
    permitted = True
elif decision.type is DecisionType.ASK:
    permitted = ticket is not None and self._consume(ticket, action)
else:
    permitted = False
```

MODIFY 示例只返回指向 `src/` 的建议，但建议仍需再次校验。Guard 不执行 shell 字符串、不解析或运行建议参数；ticket 存入随机 ID 的内存表，消费后删除。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/reliability.py tests/test_reliability.py && git commit -m "feat: enforce four-state runtime guard"`。

### Task 5: 可回滚世界、共享观察与七领域评测

**Files:**
- Create: `src/garden_ecosystem/worlds.py`、`evaluation.py`
- Test: `tests/test_worlds.py`、`tests/test_evaluation.py`

**Interfaces:**
- Produces: `PortableAgent`、`WorldAdapter` Protocol、`MemoryWorld`、`MigrationResult`、`migrate`、`self_test`。
- Produces: `Domain`、`EvaluationItem`、`aggregate`、`SharedWorld.step`。

- [ ] **Step 1: 写失败测试**

```python
source = MemoryWorld("source")
target = MemoryWorld("target", reject={"agent-1"})
source.add(PortableAgent("agent-1", {"role": "reviewer"}))
result = migrate(source, target, "agent-1")
self.assertEqual(result.status, "rolled_back")
self.assertIn("agent-1", source.agents)
self.assertNotIn("agent-1", target.agents)
```

另测成功迁移仅目标持有、源缺失不动目标、目标提交后失败会移除目标、源恢复也失败 `needs_manual_recovery=True`、self_test 不修改实际 agents。评测七领域枚举、五维度宏平均、NaN/缺失拒绝、空报告领域计数为零；共享世界两个 agent 同步版本、hub 消息、排列输入不改变共享状态。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_worlds tests.test_evaluation -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
class Domain(str, Enum):
    MCP="mcp"; SEARCH="search"; TERMINAL="terminal"; SWE="swe"
    ANDROID="android"; WEB="web"; OS="os"

DIMENSIONS = ("format", "factuality", "consistency", "realism", "quality")

@dataclass(frozen=True)
class PortableAgent:
    agent_id: str
    attributes: dict[str, object]
    lifecycle: str = "alive"
    capabilities: tuple[str, ...] = ()
    extensions: dict[str, object] = field(default_factory=dict)
```

`migrate` 保存源快照并跟踪 staged/committed；异常时逆序清除目标，再恢复源，回滚异常与原异常分别记录。评测按每领域求均值后宏平均；`SharedWorld` 按 agent_id 排序生成规范状态，不以输入排列作为隐藏身份。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/worlds.py src/garden_ecosystem/evaluation.py tests/test_worlds.py tests/test_evaluation.py && git commit -m "feat: add transactional worlds and domain evaluation"`。

### Task 5B: 运行清单、检查点与分级验证回执

**Files:**
- Create: `src/garden_ecosystem/receipts.py`
- Test: `tests/test_receipts.py`

**Interfaces:**
- Produces: `RunManifest`、`CheckpointStore`、`VerificationLevel`、`VerificationReceipt`、`ExternalToolAdapter` Protocol。
- `CheckpointStore.append(step, action, state)` 返回哈希链节点；`resume(run_id, previous_hash, action)` 只返回匹配节点。

- [ ] **Step 1: 写失败测试**

```python
manifest = RunManifest.create(project="demo", config={"model": "mock"}, seed=7)
store = CheckpointStore()
first = store.append(manifest.run_id, None, {"tool": "read"}, {"value": 1})
with self.assertRaises(CheckpointMismatch):
    store.resume(manifest.run_id, "wrong", {"tool": "write"})
receipt = VerificationReceipt.machine_checked(tool="mock-lean", version="0", evidence_hash="abc", mock=True)
self.assertTrue(receipt.mock)
self.assertEqual(receipt.level, VerificationLevel.MACHINE_CHECKED)
```

另测运行清单不含密钥、前序哈希正确才能恢复、动作改变拒绝、非有限时间拒绝、无真实工具不得生成未标 mock 的机器回执、外部工具默认 unavailable、不同验证等级不自动升格。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_receipts -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
class VerificationLevel(str, Enum):
    GENERATED="generated"; EXECUTED="executed"
    MACHINE_CHECKED="machine_checked"
    NUMERICALLY_REPRODUCED="numerically_reproduced"
    EXTERNALLY_VALIDATED="externally_validated"

@dataclass(frozen=True)
class VerificationReceipt:
    level: VerificationLevel
    tool: str
    version: str
    evidence_hash: str
    mock: bool = False
    available: bool = True
```

`RunManifest.create` 对配置先脱敏并规范化，不把环境变量内容写入清单；随机种子显式保存。`CheckpointStore` 以 `run_id + previous_hash + canonical(action) + canonical(state)` 计算新哈希，append 检查 previous_hash 是否确为当前末端。`ExternalToolAdapter.health()` 返回 available/degraded/unavailable 与原因；mock 执行结果必须带 `mock=True`。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/receipts.py tests/test_receipts.py && git commit -m "feat: add resumable verification receipts"`。

### Task 6: 谨慎学习账本与研究证据治理

**Files:**
- Create: `src/garden_ecosystem/learning.py`、`research.py`
- Test: `tests/test_learning.py`、`tests/test_research.py`

**Interfaces:**
- Produces: `LearningLedger.record`、`evaluate`、`retire`、`rollback`。
- Produces: `Preregistration.freeze`、`append_observation`、`ParameterRecord`。

- [ ] **Step 1: 写失败测试**

```python
ledger = LearningLedger()
with self.assertRaises(LearningDisabled):
    ledger.record({"text": "keep this", "kind": "guideline"})
ledger = LearningLedger(enabled=True)
item = ledger.record({"text": "run checks", "kind": "guideline"})
ledger.evaluate(item.id, helped=True, task="a", date="2026-11-09")
self.assertEqual(item.status, "tentative")
```

另测两个不同任务/日期才 active、伤害阻止激活、retire/rollback 留痕、代码/shell/env/工具定义拒绝、无 exec/eval/subprocess。研究冻结 hash、冻结内容不可改、观察只追加、负结果排除理由必填、外部标定不冒称内生参数。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_learning tests.test_research -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
FORBIDDEN_KEYS = {"code", "command", "shell", "env", "tool", "config", "secret"}
def activate_ready(item) -> bool:
    tasks = {(e.task, e.date) for e in item.evidence if e.helped}
    return len(tasks) >= 2 and not any(e.harmed for e in item.evidence)

@dataclass(frozen=True)
class ParameterRecord:
    name: str
    origin: str  # endogenous | calibrated | estimated | untested
    physical_meaning: str
```

冻结通过私有只读副本与 `MappingProxyType` 实现；对外返回 deepcopy，防止绕过修改。负结果结构化存储，不写“已证实”标签。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 全部通过。
Run: `git add src/garden_ecosystem/learning.py src/garden_ecosystem/research.py tests/test_learning.py tests/test_research.py && git commit -m "feat: add cautious learning and evidence ledgers"`。

### Task 7: 花园接口、离线演示与上游目录

**Files:**
- Create: `src/garden_ecosystem/bridge.py`、`demo.py`、`__main__.py`
- Create: `README.md`、`UPSTREAM.md`、`docs/gitee-dpsnet-inventory.md`、`examples/demo.py`
- Test: `tests/test_bridge.py`

**Interfaces:**
- Produces: `capabilities() -> dict`、`health() -> dict`、`run_demo() -> dict`。
- 全部返回值可 JSON 序列化，且无密钥与绝对本机路径。

- [ ] **Step 1: 写失败测试**

```python
report = run_demo()
self.assertTrue(report["ok"])
self.assertEqual(report["guard"]["executed"], False)
self.assertEqual(report["learning"]["enabled"], False)
self.assertEqual(set(report["evaluation"]["domains"]), set())
json.dumps(report, allow_nan=False)
```

另测 capabilities 声明协议/默认安全，health 不含密钥，`python -m garden_ecosystem` 返回码 0 且 stdout 是 JSON。

- [ ] **Step 2: 观察失败**

Run: `PYTHONPATH=src python -m unittest tests.test_bridge -v`
Expected: 导入失败。

- [ ] **Step 3: 最小实现**

```python
def capabilities():
    return {"name": "garden-ecosystem", "version": "0.1.0",
            "default_policy": "deny", "network": "injected_only",
            "modules": ["providers", "context", "reliability", "worlds",
                        "evaluation", "learning", "research"]}

def health():
    return {"ok": True, "learning_enabled": False, "secrets_loaded": False}
```

README 给出 `PYTHONPATH=src python -m garden_ecosystem` 和 unittest 命令；UPSTREAM 记录来源、许可证、固定 HEAD、已读文件、实际借鉴及未验证边界；Gitee 目录完整覆盖 25 项并区分主项目、fork、未声明许可。无图片或虚构图表。

- [ ] **Step 4: 验证并提交**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v && PYTHONPATH=src python -m garden_ecosystem`
Expected: 全部通过并输出单个合法 JSON。
Run: `git add README.md UPSTREAM.md docs/gitee-dpsnet-inventory.md examples src tests && git commit -m "docs: connect garden interfaces and verified demo"`。

### Task 8: 全量门禁与 GitHub 发布

**Files:**
- Modify: 仅修复测试证实的缺陷，并增加相应回归测试。

- [ ] **Step 1: 完整验证**

Run: `PYTHONPATH=src python -m unittest discover -s tests -v`
Expected: 所有测试通过，无 skip 掩盖核心负例。
Run: `PYTHONPATH=src python -m compileall -q src tests && PYTHONPATH=src python -m garden_ecosystem`
Expected: 返回码 0，合法 JSON。

- [ ] **Step 2: 安全与许可证检查**

检查 `.gitignore` 生效、`git ls-files` 不含密钥/上游/权重/缓存；扫描 tracked 文本中的已知 token 前缀与私钥头；确认 GPL 与未声明许可源码未被复制；审查 `git diff` 与最终提交。

- [ ] **Step 3: 创建并验证远端**

通过已认证 GitHub 接口确认 `yimeng2026/garden-ecosystem` 是否已存在。若不存在，创建公开空仓库；不得覆盖任何已有历史。设置 `origin=https://github.com/yimeng2026/garden-ecosystem.git`，使用现有凭证管理器推送 `main`，随后读取远端 HEAD 与本地 HEAD 比较。

- [ ] **Step 4: 最终复核**

Run: `git status --short && git log -1 --oneline && git ls-remote origin refs/heads/main`
Expected: 工作区干净，远端 main 等于本地 main；若凭证或网络失败，明确记录“未推送”，不得写成成功。
