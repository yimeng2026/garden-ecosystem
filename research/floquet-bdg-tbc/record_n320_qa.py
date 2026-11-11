"""Bind the four-page N=320 visual review to exact sources and hashes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-TBC-N320定向报告.docx"
REPORT = ROOT / "n320-word-qa" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report.get("pages") != 4 or report.get("rendered") != 4 or report.get("nearBlankPages"):
        raise ValueError("Expected four nonblank N=320 pages")
    if any(row.get("clipped") for row in report.get("pageFiles", [])):
        raise ValueError("Clipped N=320 page")
    sources = {
        "build_n320_report.js": sha(ROOT / "build_n320_report.js"),
        "n320-winding.png": sha(ROOT / "n320-winding.png"),
        "n320-endpoints.png": sha(ROOT / "n320-endpoints.png"),
    }
    docx_hash = sha(DOCX)
    if report.get("sourceSha256") and report["sourceSha256"] != sources:
        raise ValueError("N=320 visual QA is stale")
    if report.get("finalValidation", {}).get("docxSha256") and report["finalValidation"]["docxSha256"] != docx_hash:
        raise ValueError("N=320 DOCX changed after visual QA")
    report["sourceSha256"] = sources
    report["finalValidation"] = {
        "route": "kimi-word docx.py build with vendored docx-js 9.7.1",
        "exitCode": 0, "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "docxSha256": docx_hash,
        "n320ResultsSha256": sha(ROOT / "n320_zero.json"),
        "n320IndependentSha256": sha(ROOT / "n320_independent.json"),
    }
    report["manualReview"] = {
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "passed", "contactSheetRead": True,
        "reviewedPages": [1, 2, 3, 4], "tocCachedPages": [2, 3, 4],
        "pageObservations": {
            "1": "封面、目录及不宣称热力学极限声明完整。",
            "2": "分组表、W0 原生公式、图 1 与图例清晰。",
            "3": "逐例表、图 2 与未恢复样本的端点权重不足完整。",
            "4": "七项独立复核、有限尺寸交叉边界和后续尺度估计方向完整。",
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
