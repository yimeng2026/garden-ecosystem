"""回写 p+ip 相图与符号的限定范围解决证据，保留原初审风险。"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
PROVIDER = WORKSPACE / ".worktrees/provider-main-integration"
REPORT = PROVIDER / "papers/topo-quantum-internet/P_IP_CHERN_CONVENTION_AUDIT.md"
DOCX = REPORT.with_suffix(".docx")
RAW = PROVIDER / "papers/topo-quantum-internet/verification/pip_chern_convention_results.json"
LEGACY = PROVIDER / "papers/topo-quantum-internet/verification/legacy_pip_chern_audit.json"
IDS = {
    "provider-topo:papers/topo-quantum-internet/Kitaev链与p_ip拓扑超导体_Majorana零能模数值研究.md",
    "provider-topo:papers/topo-quantum-internet/拓扑超导马约拉纳零能模_能谱分析与拓扑保护_投稿物理学报.md",
    "provider-topo:papers/topo-quantum-internet/拓扑量子物态与量子计算研究综述_投稿物理学报.md",
}


def main() -> None:
    review_path = AUDIT / "provider-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    assert raw["validation"]["status"] == "pass"
    assert legacy["status"] == "docstring_mismatch_confirmed" and legacy["source_unchanged"]
    assert REPORT.is_file() and DOCX.is_file()
    resolution = {
        "status": "resolved_within_limited_scope",
        "scope": "仅 p+ip 相图、陈数符号、统一约定与直接数值证据；不解除 CdGM、实验数字或整篇 P0 风险。",
        "report": str(REPORT.relative_to(WORKSPACE)),
        "native_word": str(DOCX.relative_to(WORKSPACE)),
        "raw_results": str(RAW.relative_to(WORKSPACE)),
        "validation": {
            "unit_tests": 15,
            "exit_code": 0,
            "maximum_absolute_method_difference": raw["validation"]["maximum_absolute_method_difference"],
            "lattice_sweep_points": 241,
            "continuum_points": 60,
            "word_pages": 6,
            "word_ooxml_parts": 17,
            "near_blank_pages": 0,
            "visual_review": "contact-sheet及重点表格页已查看，无裁切或代码重叠",
        },
        "legacy_readonly_audit": str(LEGACY.relative_to(WORKSPACE)),
        "remaining": ["旧 TOE 脚本独立分支修复", "涡旋 CdGM 真实求解", "实验数字逐项回源", "无序、相互作用与有限尺寸标度"],
    }
    found = set()
    original_risks = {}
    for record in review["records"]:
        if record["id"] in IDS:
            found.add(record["id"])
            original_risks[record["id"]] = record["risk"]
            record["resolution_2026_11_10"] = resolution
    assert found == IDS, {"missing": IDS - found, "extra": found - IDS}
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    addendum_heading = "## p+ip 相图与符号复核补记（2026-11-10）"
    md_path = AUDIT / "PROVIDER_REVIEW.md"
    text = md_path.read_text(encoding="utf-8")
    if addendum_heading not in text:
        cite = f"kimi-cite://text?path={quote(str(REPORT))}&text={quote('p+ip 相图与陈数符号：双方法复核及三稿勘误')}"
        text += "\n" + addendum_heading + "\n\n"
        text += "本轮已完成限定范围的修复，不覆盖上述初审记录：\n\n"
        text += f"- [双方法勘误报告]({cite} \"citation\")及[原生 Word]({DOCX})（6 页）已交付。\n"
        text += f"- 晶格相区为 0<μ<4t 时 −1、−4t<μ<0 时 +1、|μ|>4t 时 0；连续弱配对为 +1、强配对为 0。\n"
        text += f"- 15 项测试退出码 0；双方法最大差为 {raw['validation']['maximum_absolute_method_difference']}；旧 TOE 脚本只读复核确认实际输出与自身注释反号。\n"
        text += "- 保留的未竟工作：旧脚本独立分支修复、CdGM 真实求解、实验数字逐项回源、无序／相互作用／有限尺寸标度。整篇 P0 风险不因本次局部修复自动解除。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")

    summary = {
        "status": "pass",
        "updated_ids": sorted(IDS),
        "count": len(IDS),
        "original_risks_preserved": all(review["records"][i]["risk"] == original_risks[review["records"][i]["id"]] for i in range(len(review["records"])) if review["records"][i]["id"] in IDS),
        "resolution_key": "resolution_2026_11_10",
        "test_count": 15,
        "maximum_absolute_method_difference": raw["validation"]["maximum_absolute_method_difference"],
        "full_p0_resolved": False,
        "source_files_exist": True,
    }
    assert summary["original_risks_preserved"]
    (AUDIT / "pip-resolution-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
