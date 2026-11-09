"""新增 K2 幂等矩阵表示例，保持 K2 完整理论开放。"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
PANEL = WORKSPACE / ".worktrees/toe-k0-universal/papers/数学基础强化_系列/_panel_records"
ID = "toe-sylva:papers/数学基础强化_系列/21_代数K理论_从向量丛到普适不变量.md"


def main() -> None:
    result = json.loads((PANEL / "k2_idempotent_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["representation_example_completed"] and not result["general_k0_completed"]
    assert len(result["theorems_audited"]) == 5
    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K1_verified_K2_representation_example_K2_to_K4_open"
    resolution["k2_representation_example"] = {
        "theorems": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "14/14",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_idempotent_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_idempotent_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_IDEMPOTENT_REPRESENTATION.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_IDEMPOTENT_REPRESENTATION.docx").relative_to(WORKSPACE)),
        "scope": "非平凡幂等矩阵表示例；投射模同构类、稳定相似、K0(R)、K3、K4 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_representation_example"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "14/14",
        "theorems_audited": len(result["theorems_audited"]),
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 幂等矩阵表示例复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_IDEMPOTENT_REPRESENTATION.md'))}&text={quote('K2 起点：非平凡幂等矩阵表示验证')}"
        text += "\n" + heading + "\n\n"
        text += f"- [K2 表示验证报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_IDEMPOTENT_REPRESENTATION.docx'})。\n"
        text += "- 五条 `#print axioms` 均仅 Lean 标准三项；14/14 检查通过，编译退出码 0。\n"
        text += "- 本次只验证非平凡幂等矩阵，不宣称投射模同构类、稳定相似或 K0(R) 已完成。K2–K4 的未竟工作不变。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_representation_example"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
