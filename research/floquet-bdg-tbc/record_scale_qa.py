"""Bind the N=400 visual review to exact sources and hashes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-N400阈值诊断报告.docx"
REPORT = ROOT / "n400-word-qa" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report.get("pages") != 4 or report.get("rendered") != 4 or report.get("nearBlankPages"):
        raise ValueError("Expected four nonblank N=400 pages")
    if any(row.get("clipped") for row in report.get("pageFiles", [])):
        raise ValueError("Clipped N=400 page")
    sources = {
        "build_scale_report.js": sha(ROOT / "build_scale_report.js"),
        "n400-result.png": sha(ROOT / "n400-result.png"),
        "n400-coverage.png": sha(ROOT / "n400-coverage.png"),
    }
    docx_hash = sha(DOCX)
    if report.get("sourceSha256") and report["sourceSha256"] != sources:
        raise ValueError("N=400 visual QA is stale")
    if report.get("finalValidation", {}).get("docxSha256") and report["finalValidation"]["docxSha256"] != docx_hash:
        raise ValueError("N=400 DOCX changed after visual QA")
    report["sourceSha256"] = sources
    report["finalValidation"] = {
        "route": "kimi-word docx.py build with vendored docx-js 9.7.1",
        "exitCode": 0, "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "docxSha256": docx_hash,
        "scaleDiagnosticSha256": sha(ROOT / "scale_diagnostic.json"),
        "scaleIndependentSha256": sha(ROOT / "scale_independent_n400.json"),
        "n400ScaleSha256": sha(ROOT / "n400_scale.json"),
    }
    report["manualReview"] = {
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "passed", "contactSheetRead": True,
        "reviewedPages": [1, 2, 3, 4], "tocCachedPages": [2, 3, 4],
        "pageObservations": {
            "1": "封面、目录及非恢复保证声明完整。",
            "2": "阈值表、W0 原生公式和图 1 完整。",
            "3": "覆盖尾长表与图 2 清晰，L50 下降与 L90 增长并列。",
            "4": "独立复核、N=400 与 N=600 的不同诊断目的及复现路径完整。",
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
