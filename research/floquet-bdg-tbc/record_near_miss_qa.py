"""Bind the completed four-page visual review to the exact near-miss report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-近miss空间分布与次近对.docx"
REPORT = ROOT / "near-miss-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-near-miss-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "near_miss_spatial_protocol.json": sha(ROOT / "near_miss_spatial_protocol.json"),
            "near_miss_spatial_analysis.json": sha(ROOT / "near_miss_spatial_analysis.json"),
            "repeated_category_analysis.json": sha(ROOT / "repeated_category_analysis.json"),
            "unclassified_signature_analysis.json": sha(ROOT / "unclassified_signature_analysis.json"),
            "near-miss-spatial.png": sha(ROOT / "near-miss-spatial.png"),
            "build_near_miss_report.js": sha(ROOT / "build_near_miss_report.js"),
        },
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX), "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 4,
            "reviewedPages": [row["file"] for row in pages], "contactSheetRead": False,
            "nearBlankPages": [], "clippedPages": [], "docxSha256": sha(DOCX),
            "tocPageMapping": [2, 3, 4], "libreOfficeFallbackUsed": False,
            "note": "全部四个单页已逐一查看；目录、OMML公式、两张表、空间图和边界说明清晰，无近空白页或裁切；表格宽度回归通过。",
        },
    }
    (ROOT / "near-miss-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
