"""登记 K2 稳定相似像模等价链证据，保留商层分类和 K0(R) 为未完成。"""
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
    result = json.loads((PANEL / "k2_stable_similarity_range_equiv_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["stable_similarity_range_equiv_completed"]
    assert not result["stable_similarity_classification_completed"] and not result["general_k0_completed"]
    assert len(result["theorems_audited"]) == 5
    assert len(result["checks"]) == 13 and all(item["pass"] for item in result["checks"])
    qa = json.loads((PANEL / "k2-stable-similarity-range-equiv-word-qa/report.json").read_text(encoding="utf-8"))
    assert qa["pages"] == qa["rendered"] == 5 and qa["nearBlankPages"] == []
    assert not [page for page in qa["pageFiles"] if page["clipped"]]
    content_loss = [item for item in qa["fidelity"]["findings"] if item["category"] == "content-loss"]
    assert [(item["element"], item["severity"]) for item in content_loss] == [("w:lvlOverride", "low")]
    with zipfile.ZipFile(PANEL / "K2_STABLE_SIMILARITY_RANGE_EQUIV.docx") as docx:
        document = docx.read("word/document.xml").decode("utf-8")
        assert "<m:oMath" in document and "<w:tbl>" in document and "TOC" in document
    regression = (PANEL / "k2_full_regression_stable_similarity_range_equiv_delivery_20261110.txt").read_text(encoding="utf-8")
    assert "Ran 56 tests" in regression and regression.rstrip().endswith("OK")

    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K2_stable_similarity_range_equiv_verified_quotient_classification_open"
    resolution["k2_stable_similarity_range_equiv"] = {
        "constructions": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "13/13",
        "k2_regression": "56/56",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_stable_similarity_range_equiv_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_stable_similarity_range_equiv_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_STABLE_SIMILARITY_RANGE_EQUIV.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_STABLE_SIMILARITY_RANGE_EQUIV.docx").relative_to(WORKSPACE)),
        "word_qa": str((PANEL / "k2-stable-similarity-range-equiv-word-qa/report.json").relative_to(WORKSPACE)),
        "word_pages": 5,
        "stable_similarity_range_equiv_completed": True,
        "stable_similarity_classification_completed": False,
        "general_k0_completed": False,
        "scope": "稳定相似保持像模同构类型；商层分类、逆向构造、直和幺半群和 K0(R) 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_stable_similarity_range_equiv"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "13/13",
        "k2_regression": "56/56",
        "constructions_audited": 5,
        "word_pages_rendered": 5,
        "stable_similarity_range_equiv_completed": True,
        "stable_similarity_classification_completed": False,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 稳定相似像模等价链复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_STABLE_SIMILARITY_RANGE_EQUIV.md'))}&text={quote('K2 稳定相似像模等价链：四段构造与见证组合')}"
        text += "\n" + heading + "\n\n"
        text += f"- [稳定相似像模等价链报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_STABLE_SIMILARITY_RANGE_EQUIV.docx'})。\n"
        text += "- `python verify_k2_stable_similarity_range_equiv_20261110.py` 实际退出码 0，13/13 检查通过；五个相关构造均只依赖 Lean 标准三公理。\n"
        text += "- 含报告和 Word 验收的完整 K2 回归实际 56/56 通过，退出码 0。\n"
        text += "- 原生 Word 共 5 页并逐页检查，无空白页或裁切；低风险 `w:lvlOverride` 仅为目录编号兼容提示。\n"
        text += "- 稳定相似保持像模同构类型已经闭合；商层分类、逆向构造、直和幺半群和 K0(R) 仍未完成，矩阵实例使用交换环。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_stable_similarity_range_equiv"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
