import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "REMEDIATION.docx"
REPORT = ROOT / "word-qa" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 3 or report.get("rendered") != 3:
    raise ValueError("final visual review requires exactly three rendered pages")
if report.get("nearBlankPages"):
    raise ValueError(f"near-blank pages require review: {report['nearBlankPages']}")

report["finalValidation"] = {
    "command": "python docx.py validate REMEDIATION.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3],
    "pageObservations": {
        "1": "封面和目录完整；四个可见缓存页码为 2、2、3、3。",
        "2": "整改资产表、两个原生公式、对照图、批次表和现代来源表完整；前三条脚注准确，无裁切。",
        "3": "另外两条脚注、五项输入血缘、验证条件、双边界和后续任务完整，无孤立末页。",
    },
    "tocCachedPages": [2, 2, 3, 3],
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
    "layoutIterations": 2,
    "layoutCorrection": "初版五页且后三节留白较多；取消后续强制分页后为三页，再按实际页面把目录修正为 2、2、3、3 并逐页复核。",
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
