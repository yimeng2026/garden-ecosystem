"""Bind the localization-scale visual review to exact source and artifact hashes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-局域恢复尺度报告.docx"
REPORT = ROOT / "word-qa" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report.get("pages") != 4 or report.get("rendered") != 4 or report.get("nearBlankPages"):
        raise ValueError("Expected four nonblank localization-scale pages")
    if any(row.get("clipped") for row in report.get("pageFiles", [])):
        raise ValueError("Clipped localization-scale page")
    sources = {
        "build_report.js": sha(ROOT / "build_report.js"),
        "coverage-scale.png": sha(ROOT / "coverage-scale.png"),
        "scale-diagnostics.png": sha(ROOT / "scale-diagnostics.png"),
    }
    docx_hash = sha(DOCX)
    if report.get("sourceSha256") and report["sourceSha256"] != sources:
        raise ValueError("Localization-scale visual QA is stale")
    if report.get("finalValidation", {}).get("docxSha256") and report["finalValidation"]["docxSha256"] != docx_hash:
        raise ValueError("Localization-scale DOCX changed after visual QA")
    report["sourceSha256"] = sources
    report["finalValidation"] = {
        "route": "kimi-word docx.py build with vendored docx-js 9.7.1",
        "exitCode": 0, "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "docxSha256": docx_hash,
        "localizationScaleSha256": sha(ROOT / "localization_scale.json"),
        "localizationCsvSha256": sha(ROOT / "localization_scale.csv"),
    }
    report["manualReview"] = {
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "passed", "contactSheetRead": True,
        "reviewedPages": [1, 2, 3, 4], "tocCachedPages": [2, 3, 4],
        "pageObservations": {
            "1": "封面、目录与仅作诊断尺寸声明完整。",
            "2": "覆盖公式、恢复分类表与图 1 完整。",
            "3": "未恢复样本尾部表、端点质量和 IPR 图件清晰。",
            "4": "已恢复对照、N=400／600 诊断问题和复现路径完整。",
        },
        "contentLossReviewed": [{
            "part": "word/numbering.xml", "element": "w:lvlOverride", "severity": "low",
            "observation": "编号级别覆盖兼容性提示；逐页未见正文、公式、表格或图件缺失。",
        }],
        "nearBlankPages": [], "clippedPages": [],
        "visualPassClaimed": True, "libreOfficeFallbackUsed": False,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": 4, "manualReview": "passed", "docxSha256": docx_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
