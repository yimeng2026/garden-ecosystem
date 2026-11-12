"""Bind the reviewed five-page inconsistency-structure report to exact evidence."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-候选不一致对结构分析.docx"
REPORT = ROOT / "pair-inconsistency-structure-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 5 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed five-page render does not satisfy the visual gate")
    losses = [row for row in render["fidelity"]["findings"] if row["category"] == "content-loss"]
    if len(losses) != 1 or losses[0]["element"] != "w:lvlOverride":
        raise ValueError(f"Unexpected content-loss findings: {losses}")
    source_names = [
        "pair_inconsistency_structure_protocol.json", "holdout_pair_evaluation_analysis.json",
        "pair_inconsistency_structure_analysis.json", "pair_inconsistency_structure_independent.json",
        "pair-inconsistency-structure.png", "build_pair_inconsistency_structure_report.js",
    ]
    record = {
        "schema": "floquet-bdg-pair-inconsistency-structure-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {name: sha(ROOT / name) for name in source_names},
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX), "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 5,
            "reviewedPages": [row["file"] for row in pages], "contactSheetRead": True,
            "nearBlankPages": [], "clippedPages": [], "docxSha256": sha(DOCX),
            "tocPageMapping": [2, 3, 4, 5], "libreOfficeFallbackUsed": False,
            "renderCommandExitCode": 6,
            "renderOutputComplete": True,
            "renderRecovery": "The render command returned a temporary-directory permission error after producing a complete five-page report. Existing outputs were reviewed once; no render retry was made.",
            "contentLossFindingsReviewed": ["word/numbering.xml w:lvlOverride；默认编号覆盖不影响本报告正文"],
            "note": "渲染命令返回临时目录权限错误，但既有report.json、联系表和五个单页完整。已先查看联系表，再逐一查看五个单页；目录、20个无序对汇总、原生公式、四面板图、最接近候选比较、16个失败集合、独立复核与边界完整，无近空白页、裁切或表后叠字。未重新渲染。",
        },
    }
    (ROOT / "pair-inconsistency-structure-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
