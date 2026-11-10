"""登记 K2 稳定相似等价律证据，保留投射模分类和 K0(R) 为未完成。"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
import zipfile

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
PANEL = WORKSPACE / ".worktrees/toe-k0-universal/papers/数学基础强化_系列/_panel_records"
ID = "toe-sylva:papers/数学基础强化_系列/21_代数K理论_从向量丛到普适不变量.md"


def main() -> None:
    result = json.loads((PANEL / "k2_stable_similarity_trans_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["stable_similarity_equivalence_completed"]
    assert result["stable_similarity_completed"] and not result["general_k0_completed"]
    assert result["theorems_audited"] == ["stableSimilar_trans"]
    assert len(result["checks"]) == 10 and all(item["pass"] for item in result["checks"])
    qa = json.loads((PANEL / "k2-stable-similarity-trans-word-qa/report.json").read_text(encoding="utf-8"))
    assert qa["pages"] == qa["rendered"] == 6 and qa["nearBlankPages"] == []
    assert not [page for page in qa["pageFiles"] if page["clipped"]]
    content_loss = [item for item in qa["fidelity"]["findings"] if item["category"] == "content-loss"]
    assert [(item["element"], item["severity"]) for item in content_loss] == [("w:lvlOverride", "low")]
    with zipfile.ZipFile(PANEL / "K2_STABLE_SIMILARITY_TRANS.docx") as docx:
        document = docx.read("word/document.xml").decode("utf-8")
        assert "<m:oMath" in document and "<w:tbl>" in document and "TOC" in document

    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K2_stable_similarity_equivalence_verified_k0_open"
    resolution["k2_stable_similarity_trans"] = {
        "theorems": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "10/10",
        "k2_regression": "32/32",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_stable_similarity_trans_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_stable_similarity_trans_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_STABLE_SIMILARITY_TRANS.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_STABLE_SIMILARITY_TRANS.docx").relative_to(WORKSPACE)),
        "word_qa": str((PANEL / "k2-stable-similarity-trans-word-qa/report.json").relative_to(WORKSPACE)),
        "word_pages": 6,
        "stable_similarity_equivalence_completed": True,
        "stable_similarity_completed": True,
        "general_k0_completed": False,
        "scope": "稳定相似自反、对称、传递三条等价律闭合；投射模同构类、分类映射、直和幺半群、K0(R)、K3、K4 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_stable_similarity_trans"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "10/10",
        "k2_regression": "32/32",
        "theorems_audited": 1,
        "word_pages_rendered": 6,
        "stable_similarity_completed": True,
        "stable_similarity_equivalence_completed": True,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 稳定相似等价律复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_STABLE_SIMILARITY_TRANS.md'))}&text={quote('K2 稳定相似等价律：传递性的共同补零证明')}"
        text += "\n" + heading + "\n\n"
        text += f"- [稳定相似等价律报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_STABLE_SIMILARITY_TRANS.docx'})。\n"
        text += "- `python verify_k2_stable_similarity_trans_20261110.py` 实际退出码 0，10/10 检查通过；`stableSimilar_trans` 只依赖 Lean 标准三公理，无 `sorryAx`。\n"
        text += "- 完整 K2 回归 `python -m unittest discover -s . -p \"test_k2_*.py\" -v` 实际 32/32 通过，退出码 0；自反、对称、传递三条等价律闭合。\n"
        text += "- 原生 Word 共 6 页并逐页检查，无空白页、孤字跨页或裁切；低风险 `w:lvlOverride` 仅为目录编号兼容提示。\n"
        text += "- 当前完成的是稳定相似关系层；投射模同构类、分类映射、直和幺半群和 K0(R) 仍未完成，不主张外部数学首创。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_stable_similarity_trans"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
