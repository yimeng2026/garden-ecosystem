"""新增 K1b 证据，保留 K1a 历史与 K2–K4 开放状态。"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
PANEL = WORKSPACE / ".worktrees/toe-k0-universal/papers/数学基础强化_系列/_panel_records"
ID = "toe-sylva:papers/数学基础强化_系列/21_代数K理论_从向量丛到普适不变量.md"


def main() -> None:
    result = json.loads((PANEL / "k0_cancellation_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["cancellation_iff_completed"] and not result["general_k0_completed"]
    assert set(result["axioms"]) <= {"propext", "Classical.choice", "Quot.sound"}
    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    matches = [record for record in review["records"] if record["id"] == ID]
    assert len(matches) == 1
    record = matches[0]
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    assert resolution["status"] == "K1a_verified_K1b_to_K4_open"
    resolution["status"] = "K1a_K1b_verified_K2_to_K4_open"
    resolution["k1b"] = {
        "theorem": result["theorem"],
        "upstream": "AddSubmonoid.LocalizationMap.top_injective_iff",
        "compile_exit_code": 0,
        "checks": "11/11",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k0_cancellation_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k0_cancellation_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K0_CANCELLATION_VERIFICATION.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K0_CANCELLATION_VERIFICATION.docx").relative_to(WORKSPACE)),
        "scope": "单射性当且仅当全消去律；K2–K4 继续开放。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k1b_resolution"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "11/11",
        "axioms": result["axioms"],
        "k1_interfaces_completed": True,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K1b 单射性与全消去律复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K0_CANCELLATION_VERIFICATION.md'))}&text={quote('K1b：标准映射单射性当且仅当全消去律')}"
        text += "\n" + heading + "\n\n"
        text += f"- [K1b 验证报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K0_CANCELLATION_VERIFICATION.docx'})。\n"
        text += f"- `inclusion_injective_iff` 编译退出码 0，11/11 检查通过，实际公理为 `{', '.join(result['axioms'])}`。\n"
        text += "- K1a＋K1b 接口闭合；K2–K4 未竟工作不变。标准局部化定理复用不构成外部数学首创。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k1b_resolution"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
