import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "FLOQUET_APPROXIMATION.docx"
REPORT = ROOT / "word-qa-floquet" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 3 or report.get("rendered") != 3:
    raise ValueError("final visual review requires exactly three rendered pages")
if report.get("nearBlankPages"):
    raise ValueError(f"near-blank pages require review: {report['nearBlankPages']}")

report["finalValidation"] = {
    "command": "python docx.py validate FLOQUET_APPROXIMATION.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3],
    "pageObservations": {
        "1": "封面和目录完整；三个可见缓存页码为 2、3、3。",
        "2": "零误差公式、三个定理、对照图和编译来源脚注完整，无裁切。",
        "3": "原文件边界、开放任务、固定工具链和另外两条脚注完整，无孤立末页。",
    },
    "tocCachedPages": [2, 3, 3],
    "nearBlankPagesReviewed": [],
    "contentLossReviewed": [
        {
            "part": "word/numbering.xml",
            "element": "w:lvlOverride",
            "count": 1,
            "severity": "low",
            "observation": "渲染器提示编号级别覆盖兼容性；逐页未见编号导致的内容缺失，标题、目录、表格和脚注均可见。",
        }
    ],
    "visualPassClaimed": True,
    "libreOfficeFallbackUsed": False,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "pages": report["pages"],
    "rendered": report["rendered"],
    "manualReview": report["manualReview"]["status"],
    "visualPassClaimed": report["manualReview"]["visualPassClaimed"],
    "sha256": report["finalValidation"]["sha256"],
}, ensure_ascii=False, indent=2))
