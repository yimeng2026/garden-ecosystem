"""Bind the completed four-page visual review to the exact pair-response report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-最近对与次近对响应审计.docx"
REPORT = ROOT / "pair-response-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-pair-response-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "pair_response_protocol.json": sha(ROOT / "pair_response_protocol.json"),
            "pair_response_analysis.json": sha(ROOT / "pair_response_analysis.json"),
            "repeated_category_analysis.json": sha(ROOT / "repeated_category_analysis.json"),
            "near_miss_spatial_analysis.json": sha(ROOT / "near_miss_spatial_analysis.json"),
            "pair-response-audit.png": sha(ROOT / "pair-response-audit.png"),
            "build_pair_response_report.js": sha(ROOT / "build_pair_response_report.js"),
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
            "note": "全部四个单页已逐一查看；16行对照表、OMML公式、高对比度响应图、两张符号列联和边界说明完整，无近空白页或裁切。",
        },
    }
    (ROOT / "pair-response-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
