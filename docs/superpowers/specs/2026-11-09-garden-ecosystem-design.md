# Garden Ecosystem 独立适配层总体设计 v2

日期：2026-11-09
状态：广泛代码平台调研后的修订版。依据所有者此前“独立新开仓库、借鉴并验证、全面推进”及本轮“查完再从整体设计”的明确指示实施；自动权限模式下不重复询问同一范围。

## 1. 目的、证据与边界

将公开项目中可验证的工程机制，转化为千界花园可调用的轻量接口。调研覆盖 GitHub、Gitee、GitLab、Codeberg、Hugging Face 的 26 组公开 API 检索，另补查 ModelScope、SourceForge、AtomGit/GitCode、OpenI 页面及官方仓库；发现池有 852 条记录、797 个按平台与名称去重的项目／模型条目，其中包含镜像、模型、广告和无关结果，不能视为“797 个可复用项目”。

重点读取 MeowCode、AgentWorld、Qwen-AgentWorld、Gamma-World、FudanDISC/SocialAgent、王斌 MUFPF、Microsoft Agent Framework、AgentScope、OASIS、MiroFish、LangGraph、Get Physics Done、Foam-Agent、UlamAI 的实际文件，并保留精确提交。另核验 59 个重点 GitHub 项目的元数据及更多官方搜索结果。未读源码的项目只作候选，不宣称其机制或质量已经验证。

本仓库不复制整个上游，不替代蜂群、主花园 Next.js/SSE 或已有 provider-pool，不宣称复现任何大模型、百万智能体、物理理论或论文基准。首版只依赖 Python 标准库，上游源码、模型权重、密钥、个人主页内容均不进入发布包。

## 2. 三种总体路线

1. **全家桶移植**：把多个框架拼到一起。重复编排、依赖庞大、GPL/AGPL 传播及供应链风险高，排除。
2. **只建项目导航**：价值止于资料库，不能改善花园行为，排除。
3. **公共底座＋受控外部能力（采用）**：自有模块处理安全、预算、状态、证据和评测；成熟 Lean、OpenFOAM、沙箱、模型服务由显式适配器调用，健康检查和回执证明其真实状态。

## 3. 分层架构

### 3.1 主花园既有层（不重写）

保留多供应商池、7 种蜂群模式、4 级人工干预、会话和 SSE。新仓库通过 Python API 和脱敏字典接口被主花园受控调用；本批不修改主花园前端或数据库，不把 HTTP 服务重复造一遍。

### 3.2 自有公共底座（本批实现）

- `security.py`：规范 JSON、稳定哈希、统一脱敏。
- `providers.py`：能力画像、故障分类、有限回退、环境密钥作用域。
- `context.py`：上下文预算、真实用量锚点、工具输出和区间缓存。
- `reliability.py`：默认拒绝的四态门禁、一次性动作绑定票据。
- `worlds.py`：稳定身份、生命周期、事务迁移、显式回滚结果。
- `evaluation.py`：七领域评测、共享世界、多种子情景报告。
- `learning.py`：默认关闭的谨慎学习账本。
- `research.py`：预登记、负结果、参数来源与验证等级。
- `receipts.py`：可恢复执行检查点、外部验证回执、运行清单。
- `bridge.py`：主花园能力、健康状态和外部工具适配协议。

### 3.3 外部能力层（只定义接口，首版不安装）

Lean/LeanDojo/Pantograph、OpenFOAM/Foam-Agent、沙箱、真实世界模型和 MCP 服务通过 `ExternalToolAdapter` 接入。适配器必须报告 `available / degraded / unavailable`，执行必须经门禁、工作区限制、超时和资源预算。不能用 mock 回执冒称已调用真实工具。

## 4. 核心机制与数据流

### 4.1 供应商、上下文和可观测性

`ProviderProfile` 声明模型、协议、窗口、输出预算、回退顺序。仅 `rate_limit / server / timeout / network` 可切换；认证、非法请求、模型不存在、上下文溢出和用户中止直接失败。错误与审计统一脱敏，密钥配置仅存环境变量名，临时注入退出时恢复或清理。

参考 Microsoft Agent Framework 和 AgentScope 的中间件、模型路由、事件及持久化思想，但主花园已有池不替换。`receipts.py` 记录步骤序号、动作哈希、输入来源、工具版本、状态和时间；模型返回文本不是完成证据。

上下文预算为 `min(配置上限, 窗口-输入-工具-余量)`。真实 token 仅在模型与精确前缀哈希同时匹配时采用；窗口不足抛 `BudgetExceeded`，不强行保留最小输出。工具输出按“小结果保留、长结果头尾并标明省略、超限本地受控引用”治理。区间缓存按规范路径、范围与内容哈希去重。摘要必须标注为摘要。

### 4.2 四态门禁与执行边界

`Action → Guard.check → Decision → Guard.execute → executor`。决策为 `ALLOW / DENY / ASK / MODIFY`。默认读操作可放行，写、shell、部署和付费默认拒绝或审批；`MODIFY.executable=False`，建议必须重新走门禁，不能把修改建议当许可。

ASK 票据一次性、带过期、主体与动作哈希；批准 A 不得执行 B。执行结果含 `executed`，审计不记录密钥。门禁不是操作系统沙箱；真实代码执行仍需外部隔离、资源限制和最小权限，不宣称纯 Python Guard 能抵御恶意原生代码。

### 4.3 共享世界与事务迁移

`PortableAgent` 含稳定 ID、生命周期、属性、能力和扩展字段。`WorldAdapter` 提供校验、暂存、提交、移除和快照。迁移保存源快照，先移除源，再暂存/提交目标；失败时逆序清理目标并恢复源。若恢复也失败，`needs_manual_recovery=True` 且保留原错误与回滚错误，不能仅记录“已尝试”。

`SharedWorld` 保留同步 agent 轴、独立观察、共享版本和 hub 消息，输入顺序不改变规范状态。此机制借鉴 Gamma-World 的显式 agent 轴，不包含其神经网络和性能声明。情景模拟必须保存种子、初始状态和干预记录；多次模拟是情景集合，不是现实预测概率或科学验证。

### 4.4 检查点、恢复与外部回执

`RunManifest` 固定运行 ID、创建时间、项目版本、模型／工具脱敏配置指纹、输入来源和随机种子。`CheckpointStore` 只在当前调用者明确指定的项目目录中追加步骤快照，恢复时必须匹配运行 ID、前一步哈希与动作指纹；拒绝把别的项目状态接入当前运行。

`VerificationReceipt` 区分：

| 等级 | 含义 | 不能推断为 |
|---|---|---|
| `generated` | 模型或程序产生候选 | 已验证 |
| `executed` | 工具确实运行并有退出状态 | 结果正确 |
| `machine_checked` | Lean、测试或确定性校验接受 | 物理真实或自然语言命题等价 |
| `numerically_reproduced` | 固定输入和版本下数值复现 | 全域普遍成立 |
| `externally_validated` | 有明确独立实验或评审来源 | 永久不可推翻 |

无真实外部工具时只能生成 `unavailable` 健康状态或 mock 标记，不能发 `machine_checked`。失败、缺失产物和未完成步骤也保留。

### 4.5 评测、科研和谨慎学习

七领域为 MCP、Search、Terminal、SWE、Android、Web、OS；五维评分为 format、factuality、consistency、realism、quality。评分函数注入，范围 0–100，NaN/缺失报错；按领域均值与宏平均报告，并附模型／judge 脱敏指纹，不能把评委分数当事实。

研究记录包括假设、参数来源、候选域、输入数据、排除理由、负结果和预登记哈希。参数来源为 `endogenous / calibrated / estimated / untested`。冻结后观察只追加，外部标定不得写成内生推导。形式化证明需记录定理声明、工具链、公理／sorry 状态；源码中的“零公理”“实验验证”不自动转为事实。

学习默认关闭。说明性候选经 tentative→active→retired，至少两个不同任务／日期的帮助证据且无未解决伤害才激活；支持正反证据、退役和回滚。禁止代码、命令、工具定义、凭证、环境修改或自动执行学习产物。

## 5. 重点项目如何进入设计

| 来源 | 借鉴点 | 本仓库的边界 |
|---|---|---|
| Agent Framework、LangGraph、AgentScope | 中间件、图状态、检查点、恢复、模型路由、HITL | 不重写蜂群，采用窄接口与回执 |
| MeowCode | 故障分类、输出预算、工具输出与学习治理 | GPL 代码不复制；修正预算不足仍请求等问题 |
| AgentWorld | 四态门禁、世界适配、迁移、自检 | MODIFY 不执行；回滚失败显式暴露 |
| Qwen-AgentWorld、Gamma-World | 七领域评测、共享 agent 轴、hub 通信 | 不下载权重，不宣称模型复现 |
| OASIS、MiroFish、AgentSociety | 多种子情景、个体记忆、干预和观察者 | MiroFish AGPL 不复制；不把模拟写成预测事实 |
| Get Physics Done、Foam-Agent | 项目恢复、医生检查、实验前静态审查、真实求解器 | 外部工具独立验证；成绩不能迁移到新系统 |
| UlamAI、LeanDojo、Pantograph | 提议与机器验证分离、回放、缓存、失败留痕 | UlamAI 未声明许可不复制；Lean 是外部工具 |
| MUFPF | 预登记、候选排除、负结果、参数治理 | 不采信或复用其物理声明 |
| OpenViking、mem0、ReMe 等 | 记忆分层与检索 | 不引入新数据库，先做带来源的记忆接口 |
| observability/eval 项目 | 运行轨迹、失败归因、回归用例、反虚假完成 | 未读源码者只作后续候选 |

## 6. 许可证、隐私与安全

- 原创代码采用 MIT；`NOTICE.md` 列出实际来源、许可证和固定提交。
- MeowCode GPL-3.0、MiroFish/OpenViking AGPL-3.0：只研究公开行为与问题，不复制实现，不把它们链接进本仓库。
- AgentWorld MIT；Qwen-AgentWorld/Gamma-World/AgentScope/GPD 等 Apache-2.0：保留出处；本批不复用其实现代码。
- MUFPF 有 CC-BY-4.0 与 MIT 文件；不复制代码或论文段落，只借鉴证据治理思想。
- UlamAI、MASER、`yizhengzhang1/agent_world` 及其他未明确许可项目不复制或再分发。
- 默认无网络、无 shell、无写操作、无学习、无模型下载。网络、外部工具与写文件由调用方显式注入；真实密钥不落盘、不入审计。
- 不自动克隆所有候选、不运行上游安装脚本、不复制用户个人主页数据。SourceForge 等镜像只用于发现，回溯官方上游。

## 7. 分阶段交付

### 本批：离线公共底座

实现第 3.2 节模块与离线演示；`Bridge.health()` 显示真实可用性，外部工具默认 unavailable。包含供应商故障切换、预算溢出、门禁、迁移回滚、共享世界、多种子报告、七领域空报告、预登记和学习禁用演示。

### 后续独立小步

1. 主花园受控桥接与事件映射，不重写现有前端。
2. 一个真实 Lean 或轻量确定性验证器适配，先健康检查、负例和工具版本回执。
3. 一个只读科研数据源或论文工作流适配，保留来源和参数分层。
4. 经明确许可与安全评审后才接沙箱、OpenFOAM 或大模型；不预设全部安装。

## 8. 验证与发布门禁

标准库 `unittest` 覆盖正常与负例：各故障分类、回退去重、密钥清理、精确锚点、预算溢出、路径逃逸、四态门禁、票据绑定、迁移双重故障、稳定 ID、自检无污染、七领域报告、非有限分数、hub 状态、多种子可复现、学习门槛、预登记不可变、检查点错链、外部回执分级和 mock 标识。

CLI 输出合法 JSON；`compileall` 通过；确认 tracked 文件不含密钥、上游源码、模型权重和缓存；研究数据明确 metadata_only 与源码核查的差别。全量回归、许可证检查和 git diff 审核通过后才提交与推送。

## 9. 非目标

不承诺“全球所有项目”绝对穷尽；不以候选数量替代代码阅读；不继续已取消的长期理论研究；不自动生成可执行学习代码；不把 LLM judge、机器检查或情景模拟分别冒称为事实、实验验证或现实预测；不修改其他未收尾仓库。
