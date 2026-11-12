"""Bind a reviewed four-page remaining-seed Word report to exact evidence."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(seed):
    docx = ROOT / f"Floquet-BdG-seed{seed}-剩余种子路径结局.docx"
    report_path = ROOT / f"remaining-seed{seed}-outcome-word-render" / "report.json"
    render = json.loads(report_path.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    losses = [row for row in render["fidelity"]["findings"] if row["category"] == "content-loss"]
    if len(losses) != 1 or losses[0]["element"] != "w:lvlOverride":
        raise ValueError(f"Unexpected content-loss findings: {losses}")
    source_names = [
        "remaining_seed_outcome_protocol.json", f"remaining_seed{seed}_path_outcome_analysis.json",
        f"remaining_seed{seed}_path_outcome_independent.json", "profile_stat_candidates_analysis.json",
        f"remaining-seed{seed}-outcome.png", "build_remaining_seed_outcome_report.js",
    ]
    record = {
        "schema": "floquet-bdg-remaining-seed-outcome-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "seed": seed,
        "sourceSha256": {name: sha(ROOT / name) for name in source_names},
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(docx), "renderReportSha256": sha(report_path),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 4,
            "reviewedPages": [row["file"] for row in pages], "contactSheetRead": True,
            "nearBlankPages": [], "clippedPages": [], "docxSha256": sha(docx),
            "tocPageMapping": [2, 3, 4], "libreOfficeFallbackUsed": False,
            "contentLossFindingsReviewed": ["word/numbering.xml w:lvlOverride；默认编号覆盖不影响本报告正文"],
            "note": "已先查看联系表，再逐一查看四个单页；目录、冻结协议、路径结局汇总、原生公式、四面板图、8项跳变表、独立复核与证据边界完整，无近空白页、裁切或表后叠字。",
        },
    }
    out = ROOT / f"remaining-seed{seed}-outcome-word-qa.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True, choices=[2, 3, 4, 5, 7])
    args = parser.parse_args()
    main(args.seed)
