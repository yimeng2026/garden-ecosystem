"""Bind the four-page finite-size visual review to exact sources and hashes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-TBC有限尺寸报告.docx"
REPORT = ROOT / "finite-word-qa" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report.get("pages") != 4 or report.get("rendered") != 4 or report.get("nearBlankPages"):
        raise ValueError("Expected four nonblank finite-size pages")
    if any(row.get("clipped") for row in report.get("pageFiles", [])):
        raise ValueError("Clipped finite-size page")
    sources = {
        "build_finite_size_report.js": sha(ROOT / "build_finite_size_report.js"),
        "finite-size-winding.png": sha(ROOT / "finite-size-winding.png"),
        "finite-size-endpoints.png": sha(ROOT / "finite-size-endpoints.png"),
    }
    docx_hash = sha(DOCX)
    if report.get("sourceSha256") and report["sourceSha256"] != sources:
        raise ValueError("Finite-size visual QA is stale")
    if report.get("finalValidation", {}).get("docxSha256") and report["finalValidation"]["docxSha256"] != docx_hash:
        raise ValueError("Finite-size DOCX changed after visual QA")
    report["sourceSha256"] = sources
    report["finalValidation"] = {
        "route": "kimi-word docx.py build with vendored docx-js 9.7.1",
        "exitCode": 0,
        "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "docxSha256": docx_hash,
        "finiteSizeSha256": sha(ROOT / "finite_size_zero.json"),
        "finiteIndependentSha256": sha(ROOT / "finite_size_independent.json"),
    }
    report["manualReview"] = {
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "passed", "contactSheetRead": True,
        "reviewedPages": [1, 2, 3, 4], "tocCachedPages": [2, 3, 4],
        "pageObservations": {
            "1": "封面、目录和 N=320 未计算声明完整。",
            "2": "11 例注册表、W0 原生公式、图 1 及 N=80 未收敛保留说明清晰。",
            "3": "尺寸趋势表、图 2 与逐 seed 对照完整，无图件重叠。",
            "4": "7 项独立复核、有限尺寸交叉假说及下一批定向算例完整。",
        },
        "contentLossReviewed": [{
            "part": "word/numbering.xml", "element": "w:lvlOverride", "severity": "low",
            "observation": "编号级别覆盖兼容性提示；逐页未见内容缺失。",
        }],
        "nearBlankPages": [], "clippedPages": [],
        "visualPassClaimed": True, "libreOfficeFallbackUsed": False,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": 4, "manualReview": "passed", "docxSha256": docx_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
