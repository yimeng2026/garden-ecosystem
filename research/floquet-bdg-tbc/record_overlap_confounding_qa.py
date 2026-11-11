"""Bind the reviewed four-page overlap-confounding report to its exact sources."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-重叠差异混杂审计.docx"
REPORT = ROOT / "overlap-confounding-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    losses = [row for row in render["fidelity"]["findings"] if row["category"] == "content-loss"]
    if len(losses) != 1 or losses[0]["element"] != "w:lvlOverride":
        raise ValueError(f"Unexpected content-loss findings require review: {losses}")
    record = {
        "schema": "floquet-bdg-overlap-confounding-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "overlap_confounding_protocol.json": sha(ROOT / "overlap_confounding_protocol.json"),
            "overlap_confounding_analysis.json": sha(ROOT / "overlap_confounding_analysis.json"),
            "embedding_census_analysis.json": sha(ROOT / "embedding_census_analysis.json"),
            "overlap-confounding-audit.png": sha(ROOT / "overlap-confounding-audit.png"),
            "build_overlap_confounding_report.js": sha(ROOT / "build_overlap_confounding_report.js"),
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
            "note": "已先查看联系表，再逐一查看四个单页；结构化OMML、全样本汇总、四面板图、十六案例表及线性嵌入门槛失败均完整，无近空白页或裁切。",
        },
    }
    (ROOT / "overlap-confounding-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
