"""Bind the completed four-page visual review to the exact fixed-N path report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-固定尺寸参数路径.docx"
REPORT = ROOT / "fixed-n-path-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-fixed-n-path-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "fixed_n_path_protocol.json": sha(ROOT / "fixed_n_path_protocol.json"),
            "fixed_n_path_analysis.json": sha(ROOT / "fixed_n_path_analysis.json"),
            "swap_candidate_spectrum_analysis.json": sha(ROOT / "swap_candidate_spectrum_analysis.json"),
            "fixed-n-path.png": sha(ROOT / "fixed-n-path.png"),
            "build_fixed_n_path_report.js": sha(ROOT / "build_fixed_n_path_report.js"),
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
            "note": "已先查看联系表，再逐一查看四个单页；OMML公式、九点谱表、路径图、八条链接和边界说明完整，无近空白页或裁切。",
        },
    }
    (ROOT / "fixed-n-path-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
