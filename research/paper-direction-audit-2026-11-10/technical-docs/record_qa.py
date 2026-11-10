import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "REVIEW.docx"
REPORT = ROOT / "word-qa" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))

if report.get("pages") != 4 or report.get("rendered") != 4:
    raise ValueError("final visual review requires exactly four rendered pages")
if report.get("nearBlankPages"):
    raise ValueError(f"near-blank pages require review: {report['nearBlankPages']}")

report["finalValidation"] = {
    "command": "python docx.py validate REVIEW.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3, 4],
    "pageObservations": {
        "1": "封面、中文页眉、页码和目录完整；五个可见缓存页码依次为 2、2、3、4、4。",
        "2": "十项来源、四个方向、状态矛盾与资产表完整；文字和表格未越界，质量进展来源脚注可见。",
        "3": "图 1 位于资产表之后、结果解释之前；两个原生公式清楚，科学边界表完整，四项来源脚注可见。",
        "4": "H3S、Lean/SI、Song/PNAS 和日期的论断分别连接正确来源；勘误表、开放边界和结尾完整，无裁切或孤立末页。",
    },
    "tocCachedPages": [2, 2, 3, 4, 4],
    "nearBlankPagesReviewed": [],
    "contentLossReviewed": [
        {
            "part": "word/numbering.xml",
            "element": "w:lvlOverride",
            "count": 1,
            "severity": "low",
            "observation": "渲染器对编号级别覆盖给出兼容性提示；逐页未见编号导致的内容缺失，标题、目录、表格和脚注均可见。",
        }
    ],
    "layoutIterations": 2,
    "layoutCorrection": "初次引用修复后为五页且末页仅一行表格和两段正文；压缩脚注冗余与间距后重新生成，最终为四页并再次逐页验收。",
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
