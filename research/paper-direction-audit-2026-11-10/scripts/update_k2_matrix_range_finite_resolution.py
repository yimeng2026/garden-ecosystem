"""登记 K2 矩阵像模有限生成性证据，保留稳定相似分类和 K0(R) 为未完成。"""
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
    result = json.loads((PANEL / "k2_matrix_range_finite_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["matrix_range_finite_completed"]
    assert not result["stable_similarity_classification_completed"] and not result["general_k0_completed"]
    assert len(result["theorems_audited"]) == 1
    assert len(result["checks"]) == 9 and all(item["pass"] for item in result["checks"])
    qa = json.loads((PANEL / "k2-matrix-range-finite-word-qa/report.json").read_text(encoding="utf-8"))
    assert qa["pages"] == qa["rendered"] == 4 and qa["nearBlankPages"] == []
    assert not [page for page in qa["pageFiles"] if page["clipped"]]
    content_loss = [item for item in qa["fidelity"]["findings"] if item["category"] == "content-loss"]
    assert [(item["element"], item["severity"]) for item in content_loss] == [("w:lvlOverride", "low")]
    with zipfile.ZipFile(PANEL / "K2_MATRIX_RANGE_FINITE.docx") as docx:
        document = docx.read("word/document.xml").decode("utf-8")
        assert "<m:oMath" in document and "<w:tbl>" in document and "TOC" in document
    regression = (PANEL / "k2_full_regression_matrix_range_finite_delivery_20261110.txt").read_text(encoding="utf-8")
    assert "Ran 52 tests" in regression and regression.rstrip().endswith("OK")

    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K2_matrix_range_finite_verified_stable_classification_open"
    resolution["k2_matrix_range_finite"] = {
        "theorems": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "9/9",
        "k2_regression": "52/52",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_matrix_range_finite_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_matrix_range_finite_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_MATRIX_RANGE_FINITE.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_MATRIX_RANGE_FINITE.docx").relative_to(WORKSPACE)),
        "word_qa": str((PANEL / "k2-matrix-range-finite-word-qa/report.json").relative_to(WORKSPACE)),
        "word_pages": 4,
        "matrix_range_finite_completed": True,
        "stable_similarity_classification_completed": False,
        "general_k0_completed": False,
        "scope": "交换环上任意矩阵的列向量像模有限生成性；稳定相似见证组合、商层分类和 K0(R) 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_matrix_range_finite"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "9/9",
        "k2_regression": "52/52",
        "theorems_audited": 1,
        "word_pages_rendered": 4,
        "matrix_range_finite_completed": True,
        "stable_similarity_classification_completed": False,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 矩阵像模有限生成性复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_MATRIX_RANGE_FINITE.md'))}&text={quote('K2 矩阵像模有限生成性：有限基与线性映射的像')}"
        text += "\n" + heading + "\n\n"
        text += f"- [矩阵像模有限生成性报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_MATRIX_RANGE_FINITE.docx'})。\n"
        text += "- `python verify_k2_matrix_range_finite_20261110.py` 实际退出码 0，9/9 检查通过；`matrix_range_finite` 只依赖 Lean 标准三公理。\n"
        text += "- 含报告和 Word 验收的完整 K2 回归实际 52/52 通过，退出码 0。\n"
        text += "- 原生 Word 共 4 页并逐页检查，无空白页或裁切；低风险 `w:lvlOverride` 仅为目录编号兼容提示。\n"
        text += "- 有限生成性与三个局部像模等价均已具备；稳定相似见证组合、商层分类和 K0(R) 仍未完成，有限生成性不单独等同于投射性。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_matrix_range_finite"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
