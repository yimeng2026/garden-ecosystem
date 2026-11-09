# 千界花园受控桥接与真实 Lean 健康检查设计

日期：2026-11-09
范围确认：上一条建议明确提出“将 bridge 接入主花园受控 Python 服务，并先实现真实 Lean 健康检查适配器”，所有者回复“继续”，视为对该范围的确认。自动权限模式下不重复询问同一选择。

## 1. 目标

在 `garden-ecosystem` 内增加真实 Lean 可执行文件探测、健康状态和 stdio 服务；在 `bloombloomgarden` 的独立 worktree 中增加最小 TypeScript 客户端和 API Route。主花园由此可以真正调用适配项目，而不只是读取一个接口定义。

本批不实现 Lean 证明、文件编译、自然语言形式化或 OpenFOAM，不安装 Lean，不把 mock 版本输出写成真实 Lean 安装。

## 2. 方案比较

1. **常驻 HTTP 服务**：调用开销低，但需要端口冲突处理、鉴权、启停和崩溃恢复，不适合这次窄接口。
2. **纯 TypeScript 重写**：减少进程，但复制规则后会产生两套事实来源，也不是真正调用 Python 适配项目。
3. **逐请求 stdio 子进程（采用）**：一次请求一个进程、一个 JSON 请求、一个 JSON 响应；不监听端口，不遗留后台服务。健康检查频率低，进程成本可接受。

## 3. 组件与数据流

### 3.1 `lean.py`

`LeanAdapter` 实现 `ExternalToolAdapter`：

- 默认通过 `shutil.which("lean")` 查找，也接受显式可执行文件路径和 `LEAN_EXECUTABLE`。
- 仅以参数数组执行 `[resolved_executable, "--version"]`，不使用 shell，不执行 Lean 文件，不读取用户源码。
- 进程返回码为 0 且 stdout 有版本文本时为 `available`；文件不存在为 `unavailable`；超时、非零退出或空输出为 `degraded`。
- 返回的状态原因不含原始环境、密钥或完整 stderr；版本字符串限制长度。
- `execute({"operation":"health"})` 只对可用工具生成 `EXECUTED` 回执，附真实版本和输出哈希。版本检查不能生成 `machine_checked`。
- 其他 operation 一律拒绝，即使 Lean 可用也不开放任意参数或文件。

测试通过注入 runner 模拟返回码、超时与版本文本。模拟 runner 不是 Lean 安装证明；另在本机执行真实 `LeanAdapter().health()`，按实际环境记录结果。

### 3.2 `service.py`

单请求协议：

```json
{"id":"request-id","action":"lean_health","params":{}}
```

动作白名单：

- `capabilities`：现有能力声明，新增 `lean`、`service` 模块名。
- `health`：包含真实 Lean 适配器的健康状态。
- `lean_health`：仅 Lean 健康状态。
- `lean_receipt`：若 Lean 可用，执行版本检查并返回 `EXECUTED` 回执；否则返回安全错误。

`Service.handle` 处理字典并返回响应；`main` 从 stdin 最多读取 16 KiB＋1 字节，超限拒绝。响应包含原请求 ID、`ok` 与 `result` 或结构化 `error`。异常不输出堆栈，不向 stdout 打印调试信息；stdout 只承载一个 JSON 响应。

### 3.3 主花园 `garden-ecosystem.ts`

`invokeBridge(action, params, options)` 进行动作白名单和 16 KiB 输入限制，使用 `spawn` 调用 `python -m garden_ecosystem.service`，工作目录为 `GARDEN_ECOSYSTEM_ROOT` 或主花园相邻的 `garden-ecosystem`，并显式设置 `PYTHONPATH` 为其 `src`。

进程环境只传递运行所需白名单变量，不继承全部 API 密钥。stdout 上限 64 KiB，stderr 上限 16 KiB，进程超时 10 秒；结束、超时、输出上限、无效 JSON 和响应 ID 不匹配均有独立失败路径。测试通过依赖注入 mock spawn 验证，不测试 mock 本身。

### 3.4 主花园 API Route

新增 `POST /api/garden-ecosystem`，使用 Node runtime、`force-dynamic`，并在读取运行时环境前 `await connection()`，遵循当前 Next.js 文档。请求体上限 16 KiB，支持上述四个动作，禁止其他字段触发任意操作。

成功返回服务 JSON；输入错误为 400，桥接失败为 502，真实工具不可用或返回结构化错误为 503。不得因工具缺失返回“已执行”。

## 4. 隔离与既有改动保护

主花园在 `.worktrees/garden-ecosystem-bridge` 的新分支 `feature/garden-ecosystem-bridge` 上实施，从 `origin/main` 建立，避免混入当前研究分支和未提交的 `package.json` 版本改动。适配项目在 `feature/controlled-bridge` 分支实施。两个项目都先写测试再实现，最后分别推送分支并创建 PR，不自行合并。

## 5. 安全与许可证

- 不传递完整环境变量，不记录密钥、完整 stderr 或用户 Lean 源文件。
- 不使用 `shell=True`、字符串拼接命令、eval 或 exec。
- stdio 不打开网络端口；唯一真实外部进程是版本检查，主花园子进程由 API 白名单触发。
- 新代码为原创，沿用各项目现有许可证；不复制 Lean、AgentScope 或其他框架源码。
- 单元测试中的 runner/spawn 模拟与真实本机探测结果分别记录。

## 6. 验证

Python：缺失文件、真实进程返回 0/非零、空输出、超时、其他 operation、stdio 四类动作、未知动作、超大输入、错误 JSON、错误 ID 和不泄密的错误响应。

TypeScript：未知动作不启动子进程、超大请求拒绝、环境白名单不含密钥、正确工作目录和参数、正常响应、进程错误、超时、输出超限、无效 JSON、响应 ID 错配。

联合验证：Python 全量测试与安装、真实 Lean 探测、stdio 实际往返、Node 测试、TypeScript 类型检查、Next 构建或明确披露构建阻塞原因、密钥扫描。临时进程全部等待结束，不保留开发服务器或后台服务。

## 7. 非目标

不证明任何定理，不替代 Lean 编译结果，不自动安装工具链，不开放任意 Lean/MCP/Shell 参数，不修改主花园现有供应商池和蜂群逻辑，不覆盖用户已有 package.json 改动，不合并 PR。
