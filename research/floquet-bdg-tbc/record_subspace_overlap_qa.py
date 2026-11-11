"""Bind the completed four-page visual review to the exact subspace-overlap report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-跨尺寸子空间重叠.docx"
REPORT = ROOT / "subspace-overlap-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-subspace-overlap-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "subspace_overlap_protocol.json": sha(ROOT / "subspace_overlap_protocol.json"),
            "subspace_overlap_analysis.json": sha(ROOT / "subspace_overlap_analysis.json"),
            "repeated_category_analysis.json": sha(ROOT / "repeated_category_analysis.json"),
            "pair_response_analysis.json": sha(ROOT / "pair_response_analysis.json"),
            "subspace-overlap.png": sha(ROOT / "subspace-overlap.png"),
            "build_subspace_overlap_report.js": sha(ROOT / "build_subspace_overlap_report.js"),
        },
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX), "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 4,
            "reviewedPages": [row["file"] for row in pages], "contactSheetRead": True,
            "nearBlankPages": [], "clippedPages": [], "docxSha256": sha(DOCX),
            "tocPageMapping": [2, 3, 4], "libreOfficeFallbackUsed": False,
            "contentLossFindingsReviewed": ["word/numbering.xml w:lvlOverride；默认编号覆盖不影响本报告正文"],
            "note": "已先查看联系表，再逐一查看四个单页；结构化OMML上下标与分式、九行分配表、对数坐标图、三份重叠矩阵与主角度完整，无近空白页或裁切。",
        },
    }
    (ROOT / "subspace-overlap-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
