"""Generate traceable research reports from verified metadata and explicit source reviews."""
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = [
    ("MuLiuSaMa/MeowCode", "GPL-3.0", "9e8e20077acbf85d260bcdcce171757691fac426", "src/agent、LICENSE", "故障分类、预算、上下文与学习治理；不复制 GPL 实现"),
    ("iwana888/AgentWorld", "MIT", "841d3a690e5f5af7b983db2efcd53c73b68daeca", "reliability、life、LICENSE", "四态门禁、世界迁移；建议不执行，回滚失败不隐瞒"),
    ("QwenLM/Qwen-AgentWorld", "Apache-2.0", "cd0aa83dc7a9c733695eb9c4652e0a68b6e6ecde", "README、eval、LICENSE", "七领域评测接口；不下载权重，不冒称复现"),
    ("nv-tlabs/Gamma-World", "Apache-2.0", "6a95de85c439d8ea73eae34c88fbfd4e89ea02e2", "README", "共享 agent 轴和 hub；不复制模型性能声明"),
    ("FudanDISC/SocialAgent", "Apache-2.0", "8ab82fda471f265b441cd546fdc730cb6e352fbd", "README", "社会智能体资料导航，不冒称 AgentWorld 平台"),
    ("dpsnet/universal_fixed_point_framework", "CC-BY-4.0；另有 MIT 文件", "41b3bb4fa582c9fdf0323966f35fdb17ea5aa7ab", "README、LICENSE", "预登记、排除与负结果；理论声明未独立验证"),
    ("microsoft/agent-framework", "MIT", "79db842042442e4d48df216b0d6aa523b4328fde", "README、元数据", "中间件、检查点、恢复、模型路由"),
    ("agentscope-ai/agentscope", "Apache-2.0", "d286c31e4d6d13bfbb065385ad31b901ae10f8c3", "README、元数据", "事件、权限、上下文、沙箱接口"),
    ("camel-ai/oasis", "Apache-2.0", "fced8869353f858de4ebe7b8f60321415f238fad", "README、元数据", "社会情景模拟；不声称本机百万 agent"),
    ("666ghj/MiroFish", "AGPL-3.0", "7657031ac01184afe2cb220f5ee3545573b5e843", "README、LICENSE", "多种子情景与观察者；不复制，不把模拟写成预测事实"),
    ("langchain-ai/langgraph", "MIT", "e5e37b5d70dbfd93c7006bd90a658c6179a95946", "README、元数据", "持久状态、人工中断、恢复"),
    ("psi-oss/get-physics-done", "Apache-2.0", "0f417695ccf1f987af44bb4f4b3cbbdeb5f2c48b", "README、官方仓库", "健康检查、恢复、验证链；不自动安装"),
    ("csml-rpi/Foam-Agent", "MIT", "c0dcbe48bdaae6a2955fa46c783f9e9efbefe248", "README、元数据", "真实求解器、静态审查和运行回执；外部执行"),
    ("ulamai/ulamai", "未声明", "b9ae7a30e1727650d60c6a7285176f48439cfae4", "README、根目录许可检查", "机器验证与搜索；未明确许可不复制"),
]
EXTRA = [
    ("NVIDIA/SkillEvaluator", "技能质量门与行为评测", "仅官方搜索元数据"),
    ("mozilla-ai/any-agent", "跨框架接口与评测", "仅官方搜索元数据"),
    ("Giskard-AI/giskard-oss", "模型与智能体测试", "仅官方搜索元数据"),
    ("coze-dev/coze-loop", "调试、评测与观测", "仅官方搜索元数据"),
    ("future-agi/future-agi", "网关、门禁与仿真", "仅官方搜索元数据"),
    ("scaleapi/agentenv-framework", "可复现 RL 环境", "仅官方搜索元数据"),
    ("pydantic/logfire", "OpenTelemetry 观测", "仅官方搜索元数据"),
    ("mlbio-epfl/HeurekaBench", "数据驱动科研评测", "仅官方搜索元数据"),
    ("allenai/novelty-eval", "新颖性评委的局限研究", "仅官方搜索元数据"),
    ("mikamikasuki/forest", "长程科研图与证据链", "仅官方搜索元数据"),
    ("cloudcell/gnosislab", "科学方法运行时", "仅官方搜索元数据"),
    ("OpenNSWM-Lab/FAROS", "蓝图式科研工作流", "仅官方搜索元数据"),
    ("InternScience/ResearchClawBench", "再发现与新发现评测", "仅官方搜索元数据"),
    ("Qwen/Qwen-AgentWorld-35B-A3B", "世界模型资产", "Hugging Face 元数据；不下载"),
    ("FudanDISC/MASER", "法律情景合成", "未声明许可，不复制"),
    ("yizhengzhang1/agent_world", "机器人场景构建", "未声明许可；不是复旦项目，不复制"),
]


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(headers) + " |",
                       "|" + "|".join(["---"] * len(headers)) + "|",
                       *["| " + " | ".join(cell(value) for value in row) + " |" for row in rows]])


def main() -> None:
    catalog = json.loads((ROOT / "research/project-catalog.json").read_text(encoding="utf-8"))
    selected = json.loads((ROOT / "research/selected-github-projects.json").read_text(encoding="utf-8"))
    gitee = json.loads((ROOT / "research" / "gitee-dpsnet-inventory.json").read_text(encoding="utf-8"))
    counts = collections.Counter(row["site"] for row in catalog["projects"])
    platform_rows = [[site, counts.get(site, 0), note] for site, note in [
        ("github", "十个主题查询；包含镜像、噪声与自我宣传"),
        ("gitee", "公开搜索 API 返回空；王斌 25 项及官方页面另查"),
        ("gitlab", "修正为 search 参数；许可证另核"),
        ("codeberg", "通用词与连字符词补查；噪声较多"),
        ("huggingface", "模型／数据资产，不等同代码仓库"),
    ]]
    selected_rows = [[f"[{r['name']}]({r['url']})", r.get("license") or "未核实",
                      r.get("language") or "—", r.get("pushed_at") or "未核实",
                      "API 元数据已核" if r["metadata_verified"] else f"未核实：{r.get('error')}"]
                     for r in selected]
    upstream_rows = [[f"[{name}](https://github.com/{name})" if not name.startswith("dpsnet")
                      else f"[{name}](https://gitee.com/{name})", license_, commit[:12], review, idea]
                     for name, license_, commit, review, idea in UPSTREAM]
    extra_rows = [[f"[{name}](https://github.com/{name})" if not name.startswith("Qwen/")
                   else f"[{name}](https://huggingface.co/{name})", use, status]
                  for name, use, status in EXTRA]
    gitee_rows = [[f"[{r['full_name']}]({r['html_url']})", r["language"] or "—",
                   r["license"] or "未声明", "是" if r["fork"] else "否", r["description"] or "—"]
                  for r in gitee]
    text = f"""# 千界花园同类开源项目广泛调研与整体设计依据

检索日期：2026-11-09。本文是公开代码生态的可追溯采样，不是“全球所有项目”的穷尽证明。

## 摘要

本轮执行 {len(catalog['queries'])} 组公开 API 查询并全部得到响应，保存 {catalog['records_before_deduplication']} 条记录，按平台与名称去重后得到 **{catalog['unique_projects_or_models']} 个候选项目／模型条目**。另对王斌的 25 个 Gitee 公开仓库逐项盘点，读取 14 个重点上游的实际文件，并对 59 个重点 GitHub 项目发起精确元数据核验。发现池不等于可复用清单：其中混合了代码、模型、镜像、广告和无关命中，未核实的许可证或功能不会被写成已验证事实。

最终设计采用“**公共底座＋受控外部能力**”。主花园保留蜂群、供应商池与 SSE；新仓库承担故障分类、上下文预算、门禁、事务迁移、检查点、评测、研究证据和谨慎学习。Lean、OpenFOAM、沙箱和大型世界模型通过外部适配器调用，必须有健康状态与真实回执，不能用 mock 冒充执行。

![图 1 平台候选条目数量（含噪声，不代表可用项目数）](assets/platform-coverage.png)

图 1：平台候选条目数量。数据来自本次 `project-catalog.json`，只说明检索覆盖，不表示质量或相关性。

## 1. 平台覆盖、局限与排噪

{md_table(['平台', '去重条目', '解释与限制'], platform_rows)}

Gitee 的公开搜索 API 对部分已知项目返回空数组，故不能据此宣称没有项目。GitLab 搜索必须使用 `search` 而不是 `q`；Codeberg 需要通用词与连字符词交叉补查。SourceForge 主要用于发现镜像并回溯官方仓库；ModelScope、AtomGit/GitCode、OpenI 的补充结果同样只作入口。网络失败、403 和缺失许可证分别留痕，不能相互替代。

候选项目按三层处理：实际读取源码／说明与许可证者可形成具体设计约束；只有官方 API 元数据者可作为后续候选；未明确许可证、GPL／AGPL 或仅有二手宣传者不进入代码。星标、更新时间和自述基准都不是正确性证明，本文不将项目宣传中的“预测一切”“零幻觉”“百万智能体”等表述作为本系统能力。

## 2. 已读重点上游与固定版本

{md_table(['项目', '许可证', '固定提交', '实际读取', '采用方式与边界'], upstream_rows)}

这些项目提供的是互补机制，而非需要堆叠的框架数量。Agent Framework、LangGraph 和 AgentScope 对应中间件、持久状态与恢复；AgentWorld 对应执行边界；Qwen-AgentWorld 和 Gamma-World 对应评测与共享世界；GPD、Foam-Agent 和 UlamAI 对应科研验证链。MeowCode 的预算实现和 AgentWorld 的迁移实现还揭示了需要修正的边界：输出预算不足不能继续发请求，回滚失败不能被写成恢复成功。

![图 2 公共底座与受控外部能力](assets/ecosystem-architecture.png)

图 2：整体架构。外部能力仅在门禁、健康检查和回执链均有效时运行；离线示例不冒称真实工具调用。

## 3. 重点 GitHub 元数据核验

{md_table(['项目', 'SPDX／状态', '语言', '最近推送', '核验状态'], selected_rows)}

“NOASSERTION”表示 GitHub 未能确定标准许可证，不等于无版权约束，也不等于当然可复用。部分精确读取遇到网络超时或 403，已单独保留为未核实状态；有本地许可证或官方页面证据的另外标注。此表不提供星标排名，因为星标与适配价值没有必然关系，也不将最近推送等同于稳定性。

## 4. 后续候选与排除项

{md_table(['项目／资产', '候选用途', '当前证据与限制'], extra_rows)}

新设计没有把所有项目打包进花园，而是先实现公共接口，再根据真实任务选择一个外部验证器、一个科研数据源或一个受控执行后端。大型模型、科研数据库和工程求解器需要单独核对硬件、数据许可、隐私、成本和实验有效性；没有证据时不预装、不生成假回执。

## 5. 王斌 Gitee 25 个公开仓库全量盘点

{md_table(['仓库', '语言', '许可证', 'Fork', '简介'], gitee_rows)}

王斌当前与花园研究直接相关的是主框架 `dpsnet/universal_fixed_point_framework`。其余多为历史项目、fork、镜像或未声明许可工具，不能因为属于同一作者就当成当前理论组件。`claude-code-source-code`、`claw-code`、`claude-code` 等未声明许可项目只保留清单，不复制、不运行。

## 6. 对花园的落地决定

公共底座新增 `receipts.py`，将运行清单、检查点与分级验证回执统一起来；`evaluation.py` 除七领域外，还保存多种子情景与观察记录；`research.py` 将预登记、参数来源和负结果结构化；`bridge.py` 只暴露真实健康状态。`MODIFY` 仅是建议，批准票据绑定动作哈希且一次性消费，默认学习关闭，任何 mock 必须有明确标记。

科学声明按 `generated → executed → machine_checked → numerically_reproduced → externally_validated` 分级。箭头表示证据流程而非自动升级，任何一级都不能跳过对应证据。Lean 接受一个形式命题不等于自然语言命题或物理现实成立；数值复现不等于全域定律；LLM 评委和社会模拟都不能代替真实实验。

完整总体设计见 `docs/superpowers/specs/2026-11-09-garden-ecosystem-design.md`。机器可读原始结果位于 `research/project-catalog.json` 与 `research/selected-github-projects.json`；本报告的统计由 `scripts/build_research_reports.py` 重新生成，未验证字段保留原状。
"""
    (ROOT / "research/landscape.md").write_text(text, encoding="utf-8")
    (ROOT / "docs/gitee-dpsnet-inventory.md").write_text(
        "# 王斌 Gitee 公开仓库盘点\n\n" + md_table(["仓库", "语言", "许可证", "Fork", "简介"], gitee_rows) + "\n",
        encoding="utf-8",
    )
    upstream_text = "# 上游版本、许可证与采用边界\n\n" + md_table(
        ["项目", "许可证", "固定提交", "实际读取", "采用方式与边界"], upstream_rows
    ) + "\n"
    (ROOT / "UPSTREAM.md").write_text(upstream_text, encoding="utf-8")
    notice = """# Attribution and implementation boundary

This package contains original Python implementations. No upstream source tree,
model weight, personal homepage corpus, or credential is redistributed here.

The projects below informed problem selection and interface design. Inclusion
is not an endorsement of their scientific claims or benchmark results.

""" + md_table(["项目", "许可证", "固定提交", "采用方式"], [[r[0], r[1], r[2], r[4]] for r in UPSTREAM]) + """

Additional discovery-only candidates and the complete dpsnet inventory are in
`research/landscape.md`. Projects without a verified license, and GPL/AGPL
implementations, are not copied. No legal or scientific certification is implied.
"""
    (ROOT / "NOTICE.md").write_text(notice, encoding="utf-8")
    print(f"Wrote landscape with {len(selected)} selected and {len(EXTRA)} additional entries")


if __name__ == "__main__":
    main()
