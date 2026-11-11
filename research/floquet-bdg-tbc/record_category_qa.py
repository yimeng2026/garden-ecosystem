"""Bind the completed four-page visual review to the exact category report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-端部机制类别检验.docx"
REPORT = ROOT / "category-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-category-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "repeated_category_protocol.json": sha(ROOT / "repeated_category_protocol.json"),
            "category_new_cells.json": sha(ROOT / "category_new_cells.json"),
            "category_new_cells_independent.json": sha(ROOT / "category_new_cells_independent.json"),
            "repeated_category_analysis.json": sha(ROOT / "repeated_category_analysis.json"),
            "repeated-categories.png": sha(ROOT / "repeated-categories.png"),
            "build_category_report.js": sha(ROOT / "build_category_report.js"),
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
            "note": "全部单页已查看；目录、公式、类别图、分类表和复现边界清晰，无近空白页或裁切。",
        },
    }
    (ROOT / "category-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
