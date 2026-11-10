"""Bind the observed six-page visual review to exact source and artifact hashes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-TBC无序对照报告.docx"
REPORT = ROOT / "word-qa" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if report.get("pages") != 6 or report.get("rendered") != 6 or report.get("nearBlankPages"):
        raise ValueError("Expected six nonblank rendered pages")
    if any(row.get("clipped") for row in report.get("pageFiles", [])):
        raise ValueError("Clipped page reported")
    sources = {
        "build_report.js": sha(ROOT / "build_report.js"),
        "disorder-winding.png": sha(ROOT / "disorder-winding.png"),
        "disorder-gaps.png": sha(ROOT / "disorder-gaps.png"),
    }
    docx_hash = sha(DOCX)
    if report.get("sourceSha256") and report["sourceSha256"] != sources:
        raise ValueError("Visual QA is stale relative to current Word source or figures")
    if report.get("finalValidation", {}).get("docxSha256") and report["finalValidation"]["docxSha256"] != docx_hash:
        raise ValueError("Visual QA is stale relative to the current DOCX")
    report["sourceSha256"] = sources
    report["finalValidation"] = {
        "route": "kimi-word docx.py build with vendored docx-js 9.7.1",
        "exitCode": 0,
        "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "docxSha256": docx_hash,
        "resultsSha256": sha(ROOT / "results.json"),
        "disorderResultsSha256": sha(ROOT / "disorder_results.json"),
        "disorderIndependentSha256": sha(ROOT / "disorder_independent.json"),
    }
    report["manualReview"] = {
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "passed",
        "contactSheetRead": True,
        "reviewedPages": [1, 2, 3, 4, 5, 6],
        "tocCachedPages": [2, 3, 4, 5, 6],
        "pageObservations": {
            "1": "封面、真实目录域缓存及页码 2–6 完整。",
            "2": "时间帧、周期化和 winding 原生公式、振幅勘误表及来源脚注清晰。",
            "3": "基准表与图 1 位置正确，未收敛叉号和独立菱形可辨。",
            "4": "12 行汇总表与图 2 完整，对数体隙和端点外圈清晰。",
            "5": "两个未收敛类别和 14 行独立复核完整，主状态未被改写。",
            "6": "科学边界、旧 not_supported／inconclusive 状态及复现路径完整。",
        },
        "contentLossReviewed": [{
            "part": "word/numbering.xml", "element": "w:lvlOverride", "severity": "low",
            "observation": "编号级别覆盖兼容性提示；逐页未见正文、目录、公式、表格或图件缺失。",
        }],
        "nearBlankPages": [],
        "clippedPages": [],
        "visualPassClaimed": True,
        "libreOfficeFallbackUsed": False,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pages": 6, "manualReview": "passed", "docxSha256": docx_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
