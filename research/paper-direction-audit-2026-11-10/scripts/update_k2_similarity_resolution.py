"""新增 K2 普通相似核证据，不把稳定相似或 K0(R) 标为完成。"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
PANEL = WORKSPACE / ".worktrees/toe-k0-universal/papers/数学基础强化_系列/_panel_records"
ID = "toe-sylva:papers/数学基础强化_系列/21_代数K理论_从向量丛到普适不变量.md"


def main() -> None:
    result = json.loads((PANEL / "k2_similarity_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["similarity_core_completed"] and not result["stable_similarity_completed"]
    assert len(result["theorems_audited"]) == 4
    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K1_verified_K2_similarity_core_stable_similarity_open"
    resolution["k2_similarity_core"] = {
        "theorems": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "12/12",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_similarity_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_similarity_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_SIMILARITY_CORE.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_SIMILARITY_CORE.docx").relative_to(WORKSPACE)),
        "scope": "同维普通相似及幂等保持；零扩展稳定相似、投射模同构类、K0(R)、K3、K4 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_similarity_core"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "12/12",
        "theorems_audited": 4,
        "stable_similarity_completed": False,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 普通相似核复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_SIMILARITY_CORE.md'))}&text={quote('K2 相似核：普通相似的等价关系与幂等保持')}"
        text += "\n" + heading + "\n\n"
        text += f"- [相似核验证报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_SIMILARITY_CORE.docx'})。\n"
        text += "- 普通相似的自反、对称、传递与幂等保持真实编译通过，12/12 检查通过。\n"
        text += "- 共轭传递按 `v*u` 顺序展开；普通相似不等于稳定相似，零扩展、投射模同构类和 K0(R) 仍未完成。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_similarity_core"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
