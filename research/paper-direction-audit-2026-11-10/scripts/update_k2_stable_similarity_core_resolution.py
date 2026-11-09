"""新增 K2 稳定相似基础核，保留传递性和 K0(R) 为未完成。"""
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
    result = json.loads((PANEL / "k2_stable_similarity_core_verification_20261110.json").read_text(encoding="utf-8"))
    assert result["status"] == "pass" and result["compile_exit_code"] == 0
    assert result["stable_similarity_core_completed"]
    assert not result["stable_similarity_equivalence_completed"]
    assert not result["stable_similarity_completed"] and not result["general_k0_completed"]
    assert len(result["theorems_audited"]) == 2
    qa = json.loads((PANEL / "k2-stable-similarity-core-word-qa/report.json").read_text(encoding="utf-8"))
    assert qa["pages"] == qa["rendered"] == 4 and qa["nearBlankPages"] == []
    assert not [page for page in qa["pageFiles"] if page["clipped"]]
    content_loss = [item for item in qa["fidelity"]["findings"] if item["category"] == "content-loss"]
    assert [(item["element"], item["severity"]) for item in content_loss] == [("w:lvlOverride", "low")]
    with zipfile.ZipFile(PANEL / "K2_STABLE_SIMILARITY_CORE.docx") as docx:
        document = docx.read("word/document.xml").decode("utf-8")
        assert "<m:oMath" in document and "<w:tbl>" in document and "TOC" in document

    path = AUDIT / "strength-review.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    record = next(record for record in review["records"] if record["id"] == ID)
    original = {key: record[key] for key in ("role", "novelty", "unfinished", "priority")}
    resolution = record["resolution_2026_11_10"]
    resolution["status"] = "K2_stable_similarity_core_verified_transitivity_open"
    resolution["k2_stable_similarity_core"] = {
        "theorems": result["theorems_audited"],
        "compile_exit_code": 0,
        "checks": "11/11",
        "axioms": result["axioms"],
        "proof": str((PANEL / "k2_stable_similarity_core_probe_20261110.lean").relative_to(WORKSPACE)),
        "log": str((PANEL / "k2_stable_similarity_core_compile_log_20261110.txt").relative_to(WORKSPACE)),
        "report": str((PANEL / "K2_STABLE_SIMILARITY_CORE.md").relative_to(WORKSPACE)),
        "native_word": str((PANEL / "K2_STABLE_SIMILARITY_CORE.docx").relative_to(WORKSPACE)),
        "word_qa": str((PANEL / "k2-stable-similarity-core-word-qa/report.json").relative_to(WORKSPACE)),
        "word_pages": 4,
        "scope": "稳定相似的标准定义、自反性与对称性；传递性、投射模同构类、K0(R)、K3、K4 未完成。",
    }
    for key, value in original.items():
        assert record[key] == value
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    summary_path = AUDIT / "strength-review-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["k2_stable_similarity_core"] = {
        "paper_id": ID,
        "status": "pass",
        "compile_exit_code": 0,
        "checks": "11/11",
        "theorems_audited": 2,
        "word_pages_rendered": 4,
        "stable_similarity_equivalence_completed": False,
        "stable_similarity_completed": False,
        "general_k0_completed": False,
        "original_role_novelty_unfinished_priority_preserved": True,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    heading = "## K2 稳定相似基础核复核补记（2026-11-10）"
    text = md_path.read_text(encoding="utf-8")
    if heading not in text:
        cite = f"kimi-cite://text?path={quote(str(PANEL / 'K2_STABLE_SIMILARITY_CORE.md'))}&text={quote('K2 稳定相似基础核：标准定义、自反性与对称性')}"
        text += "\n" + heading + "\n\n"
        text += f"- [稳定相似基础核报告]({cite} \"citation\")及[原生 Word]({PANEL / 'K2_STABLE_SIMILARITY_CORE.docx'})。\n"
        text += "- `python verify_k2_stable_similarity_core_20261110.py` 实际退出码 0，11/11 检查通过；自反性与对称性均只依赖 Lean 标准三公理。\n"
        text += "- 原生 Word 共 4 页并逐页检查，无空白页或裁切；低风险 `w:lvlOverride` 仅为目录编号兼容提示。\n"
        text += "- 当前只完成稳定相似定义、自反性和对称性；传递性、投射模同构类和 K0(R) 仍未完成。\n"
        md_path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary["k2_stable_similarity_core"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
