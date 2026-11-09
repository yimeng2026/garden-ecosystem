"""回写数学基础21的 K1a 编译证据，不把 K1b–K4 标为完成。"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
TOE = WORKSPACE / ".worktrees/toe-k0-universal"
PANEL = TOE / "papers/数学基础强化_系列/_panel_records"
ID = "toe-sylva:papers/数学基础强化_系列/21_代数K理论_从向量丛到普适不变量.md"


def main() -> None:
    result = json.loads((PANEL / "k0_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["axioms"] == ["propext", "Classical.choice", "Quot.sound"]
    assert not result["general_k0_completed"] and not result["cancellation_iff_completed"]
    review_path = AUDIT / "strength-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    matches = [record for record in review["records"] if record["id"] == ID]
    assert len(matches) == 1
    record = matches[0]
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    record["resolution_2026_11_10"] = {
        "status": "K1a_verified_K1b_to_K4_open",
        "theorem": result["theorem"],
        "upstream": "Algebra.GrothendieckAddGroup.lift（mathlib 已有同态等价）",
        "compile_exit_code": 0,
        "checks": "10/10",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k0_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k0_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K0_UNIVERSAL_PROPERTY_VERIFICATION.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K0_UNIVERSAL_PROPERTY_VERIFICATION.docx").relative_to(WORKSPACE)),
        "scope": "仅 K1a 泛性质接口；消去性充要条件、投射模、环、拓扑 K 理论和 Bott 周期性仍开放。",
        "external_novelty": "无：复用 mathlib 已有等价，只验证 ∃! 接口。",
    }
    for key, value in original.items():
        assert record[key] == value
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k1a_resolution"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "10/10",
        "full_k1_completed": False,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K1a 群完备化泛性质复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K0_UNIVERSAL_PROPERTY_VERIFICATION.md'))}&text={quote('K1a：Grothendieck 群完备化泛性质的真实编译验证')}"
        text += "\n" + heading + "\n\n"
        text += f"- [验证报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K0_UNIVERSAL_PROPERTY_VERIFICATION.docx'})。\n"
        text += "- `SylvaK0Probe.universal_property` 真实编译退出码 0，10/10 检查通过，公理仅 Lean 标准三项。\n"
        text += "- 本项只完成 K1a；K1b 消去性充要条件、K2–K4 与整篇论文的未竟工作不变。mathlib 已有 `Algebra.GrothendieckAddGroup.lift`，不主张外部数学首创。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k1a_resolution"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
