"""Build the eleven-document magazine design audit without modifying sources."""

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from inspect_sources import source_roots

AUDIT = Path(__file__).resolve().parent
INVENTORY = json.loads((AUDIT / "sources/source-inventory.json").read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def luminance(hex_color):
    values = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground, background="#0A0A0F"):
    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def assessment(source_id, title, direction_ids, role, unfinished, next_step):
    return {
        "id": source_id,
        "title": title,
        "represents_new_theory": False,
        "direction_ids": direction_ids,
        "role": role,
        "unfinished": unfinished,
        "next": next_step,
    }


def build_data():
    _, docs, _ = source_roots()
    texts = {path.stem: path.read_text(encoding="utf-8") for path in docs.glob("*.md")}
    pdfs = INVENTORY["assets"]["pdfs"]
    colors = ["#B829DD", "#606070", "#A0A0B0", "#00D9FF", "#FF2A6D"]
    directions = [
        {
            "id": "editorial_evidence",
            "role": "面向公众的科学传播、引文与证据等级治理",
            "closed": "必然性、实验、H₂S 单位、99% 能效、绝对安全和引文风险已定位。",
            "unfinished": "其余历史、价格、引文和案例未逐项回源，编辑证据卡尚未形成。",
            "next": "建立逐句来源—证据等级—允许措辞表，模拟内容明确标记，校验图标不得替代验证。",
        },
        {
            "id": "computational_design",
            "role": "把网格、开本、页数、色彩和版本变成可复算设计合同",
            "closed": "两套网格、页数冲突和两项对比度失败已复算。",
            "unfinished": "DPI、色彩转换、版本页数和唯一设计令牌尚未统一。",
            "next": "先确定版本清单与物理单位，再由脚本生成和检查设计令牌，禁止手工互相照抄。",
        },
        {
            "id": "accessible_media",
            "role": "网页、AR、音频和网聊互动的可访问性与真实数据边界",
            "closed": "普通文本对比度、减弱动效和长按键盘替代缺口已识别。",
            "unfinished": "组件未实现，键盘／读屏／减弱动效和真实互动数据未验收。",
            "next": "以最小网页切片验证键盘等效操作、减弱动效、焦点、对比度和模拟数据标签。",
        },
        {
            "id": "production_provenance",
            "role": "迁移、生成器、PDF、模板、权利和印前交付溯源",
            "closed": "七项 LF-MD5 血缘、六份 PDF、模板／资源包／压缩包缺口和生成器风险已核清。",
            "unfinished": "完整生成链、PDF/X、字体与图像权利、压缩包和印前签字未闭合。",
            "next": "改为只读输入、明确输出目录和失败非零退出，再建立资产哈希与印前验收清单。",
        },
    ]
    documents = [
        assessment("magazine_readme", "01-杂志说明", ["computational_design", "production_provenance"], "设计系统入口与快速开始", "七项原路径缺失，规格与其他文档不一致。", "让入口指向真实资产，区分设计手册、预览 PDF 和完整杂志。"),
        assessment("magazine_intro", "02-杂志简介", ["editorial_evidence", "computational_design"], "首刊公众叙事与规格摘要", "数学必然、13 次实验、6% 和 106 页缺乏当前验收。", "按既有科学审计降级措辞，并建立期号—版本—页数清单。"),
        assessment("pixel_system", "03-黑白像素系统", ["computational_design", "production_provenance"], "黑白像素与印刷工艺方案", "8px／8mm、A4／256×192mm 和字体／互动资产未统一。", "定义 DPI 与物理尺寸，提供可验证字体、图像和交互资源。"),
        assessment("vi_design", "04-VI设计", ["computational_design", "accessible_media", "production_provenance"], "品牌视觉识别与跨媒介令牌", "色值、Pantone、断点、资源链接和联系方式未统一或核实。", "冻结唯一令牌来源，核验资源包、域名与使用授权。"),
        assessment("layout_system", "05-排版系统", ["editorial_evidence", "computational_design", "production_provenance"], "印刷级网格、图表与工艺规范", "12 栏网格算不通，99% 能效和完成标记越界。", "修正几何和示例，完成印前检查前删除生产完成语义。"),
        assessment("content_architecture", "06-内容架构", ["editorial_evidence", "computational_design", "production_provenance"], "栏目、内容分配与编辑流程", "READY_FOR_PRODUCTION 与未核实新闻、案例、页数矛盾并存。", "完成事实核查和真实采访，统一页数后再审议生产状态。"),
        assessment("web_layout", "07-网页风格排版", ["accessible_media", "computational_design"], "响应式网页与数字阅读增强", "两项色值不满足普通文本对比度，动效和组件未做可访问验收。", "加入减弱动效、键盘路径和自动对比度测试，再实现组件。"),
        assessment("chat_culture", "08-网聊文化融入", ["editorial_evidence", "accessible_media"], "网聊语言、引用与互动编辑规范", "引文、绝对安全、坍缩解释和模拟互动数据缺少边界。", "区分直接引语／释义／虚构示例，提供非手势等效操作。"),
        assessment("page_designs", "09-页面设计", ["editorial_evidence", "computational_design", "production_provenance"], "页面模板、数据表和输出规范", "H₂S 单位归类、栏宽、引文、图片权利和占位 ISBN 未闭合。", "先修科学表格和网格，再核验模板、引文与出版信息。"),
        assessment("print_guide", "10-印刷指南", ["production_provenance", "computational_design"], "纸张、成本、供应商和验收建议", "价格、供应商、PDF/X 与实际 PDF 未形成当前验收链。", "保留为询价与打样指南，标注日期并获取真实报价和印前报告。"),
        assessment("design_notes", "11-设计笔记", ["editorial_evidence", "accessible_media"], "品牌理念与跨媒介设计哲学", "SEO、深色护眼和社群设想仍是主张或愿景。", "把价值主张与可测假设分开，以读者研究验证可读性。"),
    ]
    corrections = [
        {"id": "necessity", "severity": "P0", "finding": "02 将简化 McMillan 公式写成严格证明和数学必然。", "action": "按手册审计改为指定模型与参数域内的条件性估算，删除普遍必然性。"},
        {"id": "experimental_roles", "severity": "P0", "finding": "02 复述 13 次实验和仅 6% 误差，容易升级为独立验证。", "action": "并列作者预印本、理论预测和独立复现状态，不写完美实验验证。"},
        {"id": "h2s_units", "severity": "P0", "finding": "09 把 H₂S 的 155 GPa 放在临界磁场列。", "action": "将 155 GPa 移至压力列并补充来源；磁场另列、注明温度条件，不混用单位。"},
        {"id": "production_gate", "severity": "P0", "finding": "06 标 READY_FOR_PRODUCTION，但科学、资产和版本验收未闭合。", "action": "状态退回草案，设置科学、设计、无障碍和印前四道独立验收门。"},
        {"id": "grid_math", "severity": "P1", "finding": "05／09 两套 12 栏计算分别为 212／176mm，与标称 174／165mm 不符。", "action": "采用由文本宽反算的 10.833333／10.083333mm 栏宽，或重定文本宽并统一全库。"},
        {"id": "version_manifest", "severity": "P1", "finding": "106／60／96／48–64 页和多种开本并存，现有 PDF 又为 7–118 页。", "action": "建立期号、媒介、版本、页数、生成器和哈希的唯一清单，禁止相互冒充。"},
        {"id": "generator_contract", "severity": "P1", "finding": "生成器原路径七项缺失，只生成 500 字预览且覆写三份源文档。", "action": "不运行原脚本；重构为只读输入、独立输出、完整内容和失败非零退出。"},
        {"id": "accessibility", "severity": "P1", "finding": "霓虹紫／弱化灰对比度低于 4.5，未指定减弱动效和长按键盘替代。", "action": "调整普通文本色并验证键盘、焦点、读屏和 prefers-reduced-motion。"},
        {"id": "quotes_examples", "severity": "P1", "finding": "直接引语、99% 能效、MRI 比例、无限续航和绝对安全等缺少来源或限定。", "action": "逐项回源并标注释义／示例；不能回源则删除或降级，不凭风格保留科学断言。"},
        {"id": "rights_placeholders", "severity": "P1", "finding": "模板、图像权利、字体授权、占位 ISBN、域名和联系方式未核实。", "action": "发布前建立授权与占位清除清单，示例 ISBN 不得进入正式版权页。"},
        {"id": "simulated_metrics", "severity": "P2", "finding": "点赞、阅读、访谈和田野调查模板可能被误读为真实数据。", "action": "显著标注模拟数据；真实报道需采访记录、同意与可追溯材料。"},
        {"id": "color_tokens", "severity": "P2", "finding": "CMYK、Pantone、灰阶和断点在不同文档中不一致。", "action": "以 ICC／打样和统一令牌为准，不把多套屏幕近似值当作已校准印刷色。"},
    ]
    data = {
        "schema": "magazine-design-audit-v1",
        "date": "2026-11-10",
        "scope": "11 份杂志设计文档及当前生产资产；只审计，不修改原文，不运行危险生成器。",
        "sources": INVENTORY["sources"],
        "source_lineage": {
            "research_program_count": 1,
            "new_theory_count": 0,
            "development_direction_count": 4,
            "decision": "11 份文档共同构成科学传播与制作纲领，不是 11 个新理论；新增的是公众传播与证据治理方向。",
        },
        "directions": directions,
        "document_assessments": documents,
        "evidence": {
            "lineage": {key: value for key, value in INVENTORY["lineage"].items() if key != "rows"},
            "assets": {
                "pdf_count": len(pdfs),
                "pdf_pages": {row["name"]: row["pages"] for row in pdfs},
                "all_first_pages_a4": all(abs(row["first_page_width_mm"] - 210) < 0.001 and abs(row["first_page_height_mm"] - 297) < 0.001 for row in pdfs),
                "any_pdf_x_marker": any(row["pdf_x_marker_present"] for row in pdfs),
                "any_output_intent": any(row["has_output_intent"] for row in pdfs),
                "indd_templates_found": INVENTORY["assets"]["indd_templates_found"],
                "vi_asset_pack_found": INVENTORY["assets"]["vi_asset_pack_found"],
                "claimed_archive_found": INVENTORY["assets"]["claimed_archive_found"],
            },
            "generator": INVENTORY["generator"],
            "layout": {
                "layout_grid_width_mm": 12 * 14 + 11 * 4,
                "layout_claimed_text_width_mm": 174,
                "layout_correct_column_mm": (174 - 11 * 4) / 12,
                "page_grid_width_mm": 12 * 11 + 11 * 4,
                "page_claimed_text_width_mm": 165,
                "page_correct_column_mm": (165 - 11 * 4) / 12,
                "intro_pages": 106,
                "architecture_pages": 60,
                "cover_story_allocated_pages": 14,
                "cover_story_detailed_pages": 16,
            },
            "editorial": {
                "mcmillan_strict_proof_claim": "McMillan公式严格证明" in texts["02-杂志简介"],
                "experimental_13_and_6pct_claim": "13次重复实验" in texts["02-杂志简介"] and "仅6%" in texts["02-杂志简介"],
                "h2s_pressure_under_magnetic_field_column": "临界磁场" in texts["09-页面设计"] and "155 GPa" in texts["09-页面设计"],
                "energy_99pct_unverified": True,
                "direct_quotes_unverified": True,
                "absolute_quantum_security_claim": "绝对安全" in texts["08-网聊文化融入"],
                "production_ready_claim": "READY_FOR_PRODUCTION" in texts["06-内容架构"],
                "production_ready_supported": False,
            },
            "accessibility": {
                "contrast": [{"foreground": color, "background": "#0A0A0F", "ratio_on_dark": contrast(color), "passes_normal_text": contrast(color) >= 4.5} for color in colors],
                "reduced_motion_specified": "prefers-reduced-motion" in texts["07-网页风格排版"],
                "keyboard_long_press_alternative": "键盘长按" in texts["08-网聊文化融入"],
            },
        },
        "corrections": corrections,
        "open_boundaries": {
            "scientific_claims_verified": False,
            "production_ready": False,
            "pdf_print_verified": False,
            "web_accessibility_verified": False,
            "archive_verified": False,
            "full_repository_audit": False,
        },
        "figure": {
            "svg": "magazine-design-evidence.svg",
            "png": "magazine-design-evidence.png",
            "labels": ["LF-MD5 7/7", "500 字预览", "212 mm", "176 mm", "4.137746", "3.202044"],
            "caption": "图 1　设计系统的内容血缘、几何复算与对比度门槛",
            "insert_after": "资产与血缘表",
            "insert_before": "逐文档裁决",
            "completion_percentage_plotted": False,
        },
        "verification_scope": {
            "source_documents_modified": False,
            "generator_executed": False,
            "pdf_x_certified": False,
            "external_fact_check_complete": False,
            "full_repository_audit": False,
        },
    }
    return data


def build_figure(data):
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(16, 9), facecolor="#F7F8FA", constrained_layout=True)
    grid = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.15, 1.25])
    axes = [fig.add_subplot(grid[0, index]) for index in range(3)]
    for ax in axes:
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_color("#CFD8DC")
    fig.suptitle("设计规范需要同时通过血缘、计算与可访问性验收", fontsize=22, fontweight="bold", color="#263238")

    ax = axes[0]
    ax.axis("off")
    ax.set_title("A. 内容保留 ≠ 生产链闭合", fontsize=15, fontweight="bold", color="#37474F", pad=16)
    rows = [
        ("LF-MD5 血缘", "7/7 一致", "#DFF2E1"),
        ("原始 Markdown 路径", "7 个缺失", "#FCE8E6"),
        ("生成器内容", "仅 500 字预览", "#FFF4D6"),
        ("现有 PDF", "6 份 · 7–118 页", "#E4EEF5"),
        ("PDF/X 与 Output Intent", "当前未检出", "#FCE8E6"),
        ("InDesign／资源包／压缩包", "未找到", "#FCE8E6"),
    ]
    for index, (label, value, color) in enumerate(rows):
        y = 0.89 - index * 0.145
        ax.add_patch(plt.Rectangle((0.03, y - 0.085), 0.94, 0.115, transform=ax.transAxes, facecolor=color, edgecolor="#B0BEC5"))
        ax.text(0.06, y, label, transform=ax.transAxes, fontsize=10.5, color="#455A64", va="center")
        ax.text(0.94, y, value, transform=ax.transAxes, fontsize=11, fontweight="bold", color="#263238", va="center", ha="right")
    ax.text(0.03, 0.01, "原脚本不运行：会覆写三份源文档。", transform=ax.transAxes, fontsize=10, color="#8A4B4B")

    ax = axes[1]
    ax.set_title("B. 12 栏网格复算", fontsize=15, fontweight="bold", color="#37474F", pad=16)
    labels = ["05 排版系统", "09 页面设计"]
    claimed = [174, 165]
    actual = [212, 176]
    y = np.arange(2)
    ax.barh(y + 0.17, claimed, height=0.28, color="#90A4AE", label="标称文本宽")
    ax.barh(y - 0.17, actual, height=0.28, color="#7E57C2", label="栏宽＋间距复算")
    for index, value in enumerate(claimed):
        ax.text(value + 2, index + 0.17, f"标称 {value} mm", va="center", fontsize=10)
    for index, value in enumerate(actual):
        ax.text(value + 2, index - 0.17, f"复算 {value} mm", va="center", fontsize=10, fontweight="bold")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 245)
    ax.set_xlabel("宽度（mm）")
    ax.grid(axis="x", alpha=0.18)
    ax.text(0.02, 0.04, "若保留文本宽：栏宽应分别为 10.833333 / 10.083333 mm", transform=ax.transAxes, fontsize=9.5, color="#455A64")

    ax = axes[2]
    ax.set_title("C. 深色背景普通文本对比度", fontsize=15, fontweight="bold", color="#37474F", pad=16)
    rows = data["evidence"]["accessibility"]["contrast"]
    names = [row["foreground"] for row in rows]
    ratios = [row["ratio_on_dark"] for row in rows]
    bars = ax.barh(np.arange(len(rows)), ratios, color=names, edgecolor="#607D8B")
    ax.axvline(4.5, color="#C62828", linestyle="--", linewidth=1.6, label="普通文本门槛 4.5:1")
    for bar, value in zip(bars, ratios):
        if value < 4.5:
            ax.text(value - 0.12, bar.get_y() + bar.get_height() / 2, f"{value:.6f}", va="center", ha="right", fontsize=9.5, color="white", fontweight="bold")
        else:
            ax.text(value + 0.15, bar.get_y() + bar.get_height() / 2, f"{value:.6f}", va="center", fontsize=9.5)
    ax.set_yticks(np.arange(len(rows)), names)
    ax.invert_yaxis()
    ax.set_xlim(0, 13)
    ax.set_xlabel("对 #0A0A0F 的 WCAG 对比度")
    ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="x", alpha=0.18)
    fig.text(0.01, 0.005, "只显示已复算证据，不显示完成百分比，不把 PDF 存在等同于印刷验收。", fontsize=10, color="#607D8B")
    fig.savefig(AUDIT / data["figure"]["svg"], format="svg")
    fig.savefig(AUDIT / data["figure"]["png"], dpi=180)
    plt.close(fig)


def build_markdown(data):
    lines = [
        "# 杂志设计系统：科学传播、计算一致性与生产溯源审计",
        "",
        "> 2026-11-10。11 份文档只读；不运行原生成器，不修改原文，不把 PDF 存在当作科学或印刷验证。",
        "",
        "## 一、总裁决与四个方向",
        "",
        data["source_lineage"]["decision"],
        "",
        "| 方向 | 已闭合的局部审计 | 未竟工作与下一步 |",
        "|:--|:--|:--|",
    ]
    for row in data["directions"]:
        lines.append(f"| `{row['id']}`：{row['role']} | {row['closed']} | {row['unfinished']} **下一步：**{row['next']} |")
    lines += ["", "## 二、来源与资产血缘", "", "| 来源 | 只读路径 | SHA-256 |", "|:--|:--|:--|"]
    for source in data["sources"]:
        lines.append(f"| `{source['id']}` | `{source['path']}` | `{source['sha256']}` |")
    lines += [
        "",
        "七份设计文档的 LF 归一化 MD5 与原始清单 **7/7 一致**；七个原始路径缺失不代表内容丢失。六份 PDF 存在，但压缩包、InDesign 模板和 VI 资源包未找到。",
        "",
        "| PDF | 当前页数 |",
        "|:--|--:|",
    ]
    for name, pages in data["evidence"]["assets"]["pdf_pages"].items():
        lines.append(f"| `{name}` | {pages} |")
    lines += [
        "",
        "六份 PDF 首页均为 A4；当前未检出 Output Intent 或 PDF/X 标记。原脚本只读取每份文档前 500 字符，并会覆写三份说明文档，故未运行。",
        "",
        "![图 1：设计系统的内容血缘、几何复算与对比度门槛](magazine-design-evidence.svg)",
        "",
        "**图件插入顺序：图 1 位于资产与血缘表之后、逐文档裁决之前。**",
        "",
        "## 三、11 份文档逐篇裁决",
        "",
        "| 文档 | 方向 | 角色 | 未竟工作与下一步 |",
        "|:--|:--|:--|:--|",
    ]
    for row in data["document_assessments"]:
        lines.append(f"| {row['title']} | {'、'.join(f'`{item}`' for item in row['direction_ids'])} | {row['role']} | {row['unfinished']} **下一步：**{row['next']} |")
    layout = data["evidence"]["layout"]
    lines += [
        "",
        "## 四、可计算设计与科学传播",
        "",
        f"- 05 网格：12×14＋11×4＝**{layout['layout_grid_width_mm']} mm**，不是 174 mm；174 mm 文本宽对应栏宽约 **{layout['layout_correct_column_mm']:.6f} mm**。",
        f"- 09 网格：12×11＋11×4＝**{layout['page_grid_width_mm']} mm**，不是 165 mm；165 mm 文本宽对应栏宽约 **{layout['page_correct_column_mm']:.6f} mm**。",
        "- 页数：简介 106 页、架构 60 页；封面故事分配 14 页，细项却为 16 页。现有 PDF 为 7–118 页，必须建立版本清单。",
        "- 对比度：霓虹紫约 **4.137746**、弱化灰约 **3.202044**，均低于普通文本 4.5:1。",
        "- 科学传播：McMillan 严格证明／数学必然、13 次实验与 6%、H₂S 的 GPa 列入临界磁场、99% 能效和量子通信绝对安全均不能直接发布为已验证事实。",
        "",
        "## 五、十二项分级勘误",
        "",
        "| 级别 | 已观察问题 | 建议动作 |",
        "|:--|:--|:--|",
    ]
    for row in data["corrections"]:
        lines.append(f"| {row['severity']} | {row['finding']} | {row['action']} |")
    lines += ["", "## 六、验证范围与开放边界", "", "| 边界 | 状态 |", "|:--|:--|"]
    for key, value in data["open_boundaries"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines += [
        "",
        "本批使用 17 项冻结来源、七项 LF-MD5 血缘、六份 PDF 只读元数据和独立复算。命令与退出码见 `run.log`；Word 验收见 `word-qa/report.json`。",
        "",
        "未逐项回源的历史、价格、引文与案例仍标未核实。本批没有生成新印刷 PDF，没有进行 PDF/X 认证或实验验证，没有修改 11 份原文。**全库审计尚未完成。**",
        "",
    ]
    return "\n".join(lines)


def main():
    data = build_data()
    (AUDIT / "review.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    build_figure(data)
    (AUDIT / "REVIEW.md").write_text(build_markdown(data), encoding="utf-8")
    print(json.dumps({
        "sources": len(data["sources"]),
        "documents": len(data["document_assessments"]),
        "directions": len(data["directions"]),
        "corrections": len(data["corrections"]),
        "pdf_pages": data["evidence"]["assets"]["pdf_pages"],
        "lf_md5_matches": data["evidence"]["lineage"]["normalized_lf_md5_matches"],
        "review_sha256": sha256(AUDIT / "review.json"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
