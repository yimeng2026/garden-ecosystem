# 受控 Lean 编译与证据回执设计

日期：2026-11-09
范围：落实此前提出的受控编译接口，并修正测试替身可能生成未标 mock 执行回执的问题。当前任务授权包含该接口的实现、验证和同步，不包含任意 Lean 项目、宏或不受控代码执行。

## 1. 方案比较

1. **直接编译任意文件**：功能最广，但 Lean 的宏、外部声明、求值和系统交互可能越过文件边界，不能作为安全默认接口。
2. **完整容器沙箱**：隔离更强，但需要额外的容器、镜像、网络和资源管理；本批不假定其存在，也不把普通 subprocess 说成等价沙箱。
3. **受限核心源码白名单（采用）**：只接受明确可读、无导入、无宏、无求值指令、无危险声明的 Lean 文件，再交给真实 Lean 编译并检查公理输出。覆盖最小可证明流程，边界可测试。

## 2. 输入契约

`LeanProofAdapter.execute` 仅接受：

```json
{"operation":"check_file","path":"LeanSmoke.lean","declaration":"one_add_one_eq_two"}
```

- `path` 必须位于调用方显式给定的工作区，文件存在、是普通文件、扩展名为 `.lean`；拒绝绝对路径、`..`、符号链接逃逸和目录。
- 源码 UTF-8、最多 64 KiB、最多 2000 行；`declaration` 最多 128 字符，只允许 ASCII 字母开头的 Lean 标识符及点号、下划线、数字和 apostrophe。
- 不允许 `import`、以 `#` 开头的编译器指令、`sorry`、`admit`、`axiom`、`unsafe`、`postulate`、`partial`、`opaque`、`extern`、`noncomputable`、`macro`、`elab`、`run_cmd`、`run_elab`、`run_tac` 或 `set_option`。
- 通过保留字符串的嵌套块注释与行注释扫描器去除注释后再判定，避免把注释中的 `#eval` 误当作执行指令。字符串中的 `#` 不是指令。
- 不接受额外参数，不把用户文本拼成可执行命令。

这是一份保守的首批白名单，而不是 Lean 全语言支持。以后扩充语法必须逐项重新评估语义和资源风险。

## 3. 执行与清理

先校验输入，再复用 `LeanAdapter` 探测真实版本。工具不可用时只返回 `ExternalToolUnavailable`，不进入编译。

在工作区的 `.garden_tmp/<随机目录>/Check.lean` 创建临时文件，内容为原源码和 `#print axioms <declaration>`。仅以参数数组调用真实 Lean，不使用 shell，不执行源文件内的求值指令。进程使用短超时、stdout 64 KiB、stderr 16 KiB 上限。上下文管理器在成功或失败后都清理临时目录；不把源文件或临时文件写入仓库跟踪区。

## 4. 回执与负结果

`ProofReport` 包含：

- `ok`：仅当真实编译返回 0 且公理输出可识别时为 true。
- `receipt`：成功时为 `MACHINE_CHECKED`；执行但未满足全部证据条件时为 `EXECUTED`。
- `declaration`、工作区相对 `path`、源码与输出证据哈希、工具版本。
- `depends_on_axioms`：由 `#print axioms` 明确判断，可为 true/false/None；`axioms` 为输出中列出的公理名，不将“未识别输出”解释为无公理。
- 有界且去除本机绝对路径的 stdout/stderr。
- `mock` 与 `attested`：默认真实 runner 产生真实回执；注入 runner 一律 `mock=True, attested=False`。

编译失败返回 `ok=False` 和 `EXECUTED`，不抛出“证明成功”的假象。输入或协议错误在调用前拒绝。`MACHINE_CHECKED` 只表示 Lean 接受对应形式化声明并完成公理检查，不表示自然语言命题、物理理论或实验事实成立。

## 5. 已有测试替身修正

`LeanAdapter` 注入 runner 时也标记 `mock=True, attested=False`，不再让模拟版本输出产生真实 attestation。真实默认 runner 的当前本地验证仍保持真实回执。该修正补充原有测试预期，而不改变真实 Lean 版本命令。

## 6. 协议与主花园

Python `Service` 增加 `proof` 依赖，新增 `lean_check`，仅接受 `path` 与 `declaration` 两个参数并调用 `proof.execute`。返回 `ProofReport` 的可序列化字典。

`capabilities()` 增加 `proof` 模块。TypeScript `BRIDGE_ACTIONS` 同步增加 `lean_check`，沿用已有 16 KiB 输入、64 KiB 输出、10 秒超时、白名单环境和响应 ID 校验。现有 API 鉴权与进程边界不变，不新增其他动作或任意参数透传。

## 7. 验证与发布

- 自包含定理、注释中的危险词、字符串中的 `#`、嵌套注释。
- 路径逃逸、非 `.lean`、缺失文件、超大文件、非法声明和额外参数。
- sorry/import/#eval/unsafe/macro/run_cmd/set_option 等逐类拒绝。
- 编译失败、超时、输出上限、公理列表、无法识别公理输出、路径脱敏和临时目录清理。
- stdio 与 TypeScript 新动作、未知参数、真实工具不可用和响应 ID。
- 使用已校验 SHA-256 的 Lean 4.35.0 执行实际最小编译，确认真实公理输出和回执。
- 全量 Python/Node 测试、安装、Next 构建、Vercel 预览、敏感信息扫描和远端一致性。

不宣称已支持 Mathlib、任意宏、任意项目、完整操作系统沙箱或自动形式化。发布后若有进一步工作，应优先补真正的隔离执行与资源测量，而不是简单扩大字符串白名单。
