"""新增 K2 零扩展相似与对齐证据，保留稳定相似传递性和 K0(R) 为未完成。"""
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
    result = json.loads((PANEL / "k2_zero_extension_similarity_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["zero_extension_alignment_completed"]
    assert not result["stable_similarity_completed"] and not result["general_k0_completed"]
    assert len(result["theorems_audited"]) == 3
    qa = json.loads((PANEL / "k2-zero-extension-similarity-word-qa/report.json").read_text(encoding="utf-8"))
    assert qa["pages"] == qa["rendered"] == 4 and qa["nearBlankPages"] == []
    assert not [page for page in qa["pageFiles"] if page["clipped"]]
    content_loss = [item for item in qa["fidelity"]["findings"] if item["category"] == "content-loss"]
    assert [(item["element"], item["severity"]) for item in content_loss] == [("w:lvlOverride", "low")]
    with zipfile.ZipFile(PANEL / "K2_ZERO_EXTENSION_SIMILARITY.docx") as docx:
        document = docx.read("word/document.xml").decode("utf-8")
        assert "<m:oMath" in document and "<w:tbl>" in document and "TOC" in document

    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K2_zero_extension_alignment_verified_transitivity_open"
    resolution["k2_zero_extension_similarity"] = {
        "theorems": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "12/12",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_zero_extension_similarity_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_zero_extension_similarity_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_ZERO_EXTENSION_SIMILARITY.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_ZERO_EXTENSION_SIMILARITY.docx").relative_to(WORKSPACE)),
        "word_qa": str((PANEL / "k2-zero-extension-similarity-word-qa/report.json").relative_to(WORKSPACE)),
        "word_pages": 4,
        "scope": "零扩展相似、结合律和重索引交换；稳定相似传递性、投射模同构类、K0(R)、K3、K4 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_zero_extension_similarity"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "12/12",
        "theorems_audited": 3,
        "word_pages_rendered": 4,
        "stable_similarity_completed": False,
        "stable_similarity_equivalence_completed": False,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 零扩展相似与对齐复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_ZERO_EXTENSION_SIMILARITY.md'))}&text={quote('K2 对齐接口：零扩展相似、结合律与重索引交换')}"
        text += "\n" + heading + "\n\n"
        text += f"- [零扩展相似与对齐报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_ZERO_EXTENSION_SIMILARITY.docx'})。\n"
        text += "- `python verify_k2_zero_extension_similarity_20261110.py` 实际退出码 0，12/12 检查通过；三条对齐定理均只依赖 Lean 标准三公理。\n"
        text += "- 原生 Word 共 4 页并逐页检查，无空白页或裁切；低风险 `w:lvlOverride` 仅为目录编号兼容提示。\n"
        text += "- 当前只完成零扩展相似与对齐工具；稳定相似传递性、投射模同构类和 K0(R) 仍未完成。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_zero_extension_similarity"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
